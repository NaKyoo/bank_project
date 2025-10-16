from threading import Thread
from time import sleep
from fastapi import HTTPException             
from sqlmodel import Session, select          
from decimal import Decimal                   

from app.db import engine
from app.models.account import BankAccount, Transaction, TransactionStatus
from app.models.beneficiary import Beneficiary


# ------------------------------
# Service bancaire principal
# ------------------------------
class BankService:
    """
    Cette classe regroupe les opérations principales du système bancaire :
    - gestion des comptes (dépôt, transfert)
    - gestion des bénéficiaires
    - consultation d’informations de compte

    Elle agit comme une couche métier entre la base de données (SQLModel)
    et les routes FastAPI.
    """

    def __init__(self):
        """
        Initialise le service et s’assure que la base de données et les tables
        sont bien créées au démarrage.
        """
        from app.db import create_db_and_tables  # Import local pour éviter une boucle d’importation
        create_db_and_tables()                   # Création automatique des tables si elles n’existent pas


    # ------------------------------
    # Récupération d’un compte
    # ------------------------------
    def get_account(self, session: Session, account_number: str) -> BankAccount:
        """
        Récupère un compte à partir de son numéro dans la base de données.

        Args:
            session (Session): session SQLModel active
            account_number (str): numéro du compte à chercher

        Returns:
            BankAccount: l’objet du compte trouvé

        Raises:
            HTTPException: si le compte n’existe pas
        """
        account = session.get(BankAccount, account_number)  # Recherche dans la base
        if not account:
            raise HTTPException(404, f"Compte '{account_number}' non trouvé")  # Si absent, renvoie une erreur HTTP 404
        return account


    # ------------------------------
    # Dépôt d’argent sur un compte
    # ------------------------------
    def deposit(self, session: Session, account_number: str, amount: Decimal) -> Transaction:
        """
        Effectue un dépôt sur un compte et enregistre la transaction correspondante.
        """
        account = self.get_account(session, account_number)   # Vérifie que le compte existe
        transaction = account.deposit(amount)                 # Appelle la méthode deposit() du modèle
        session.add_all([account, transaction])               # Prépare les objets à insérer ou mettre à jour
        session.commit()                                      # Valide les changements dans la base
        session.refresh(transaction)                          # Rafraîchit la transaction pour avoir l'ID et la date
        return transaction


    # ------------------------------
    # Transfert entre deux comptes
    # ------------------------------
    def transfer(self, session: Session, from_acc: str, to_acc: str, amount: Decimal) -> Transaction:
        # Récupère les objets BankAccount correspondant aux numéros de compte
        source = self.get_account(session, from_acc)
        destination = self.get_account(session, to_acc)
        
        # Crée la transaction PENDING via la logique métier de BankAccount
        transaction = source.transfer_to(destination, amount)
        
        # Ajoute la transaction à la session et commit pour la sauvegarder en base
        session.add_all([transaction])
        session.commit()
        session.refresh(transaction) # Recharge la transaction avec l'ID généré

        # Fonction interne pour finaliser la transaction après un délai
        def delayed_complete(transaction_id: int):
            sleep(5)  # Délai simulant le traitement asynchrone
            with Session(engine) as new_session:
                # Récupère la transaction depuis la base
                transaction_from_db = new_session.get(Transaction, transaction_id)
                if not transaction_from_db:
                    return  # Si la transaction a été supprimée ou n'existe pas, abandon

                # Vérifie que la transaction est encore PENDING
                if transaction_from_db.status != TransactionStatus.PENDING:
                    print(f"Transaction {transaction_from_db.id} annulée avant exécution.")
                    return

                # Récupère les comptes source et destination depuis la base
                source_account_db = new_session.get(BankAccount, transaction_from_db.source_account_number)
                destination_account_db = new_session.get(BankAccount, transaction_from_db.destination_account_number)

                # Applique la logique de completion du transfert
                source_account_db.complete_transfer(destination_account_db, transaction_from_db)

                # Ajoute les comptes et la transaction modifiée à la session et commit
                new_session.add_all([source_account_db, destination_account_db, transaction_from_db])
                new_session.commit()
                new_session.refresh(transaction_from_db)
                print(f"Transaction {transaction_from_db.id} complétée !")

        # Lance le traitement différé dans un thread séparé
        Thread(target=delayed_complete, args=(transaction.id,), daemon=True).start()

        # Retourne l'objet transaction créé immédiatement (statut PENDING)
        return transaction


    # ------------------------------
    # Ajout d’un bénéficiaire
    # ------------------------------
    def add_beneficiary(self, session: Session, owner_account_number: str, target_account_number: str) -> Beneficiary:
        """
        Ajoute un bénéficiaire (autre compte) pour un compte donné.
        """
        owner = self.get_account(session, owner_account_number)     # Récupère le compte propriétaire
        target = self.get_account(session, target_account_number)   # Récupère le compte à ajouter comme bénéficiaire
        new_beneficiary = owner.add_beneficiary(target)             # Appelle la logique du modèle
        session.add(new_beneficiary)                                # Ajoute le bénéficiaire dans la session
        session.commit()                                            # Enregistre la modification
        session.refresh(new_beneficiary)                            # Rafraîchit les données depuis la base
        return new_beneficiary


    # ------------------------------
    # Consultation d’un compte complet
    # ------------------------------
    def get_account_info(self, session: Session, account_number: str):
        """
        Récupère toutes les informations d’un compte :
        - solde actuel
        - liste des bénéficiaires
        - historique des transactions
        """
        account = self.get_account(session, account_number)  # Vérifie que le compte existe

        # Vérification si le compte est clôturé
        if not account.is_active:
            raise HTTPException(403, "Ce compte est clôturé et ne peut plus être consulté")
        
        # Liste des bénéficiaires associés à ce compte
        beneficiaries = session.exec(
            select(Beneficiary.beneficiary_account_number)
            .where(Beneficiary.owner_account_number == account_number)
        ).all()

        # Transactions liées au compte (sortantes ou entrantes)
        transactions = session.exec(
            select(Transaction)
            .where(
                ((Transaction.source_account_number == account_number) |  # Transactions sortantes
                (Transaction.destination_account_number == account_number)) &  # Transactions entrantes
                (Transaction.status == TransactionStatus.COMPLETED) # Filtre par statut
            )
        ).all()

        # Structure de réponse complète
        return {
            "account_number": account.account_number,
            "current_balance": account.balance,
            "beneficiaries": [{"beneficiary_account_number": b} for b in beneficiaries],
            "transactions": [
                {
                    "transaction_type": t.transaction_type,
                    "transaction_amount": t.amount,
                    "source_account_number": t.source_account_number,
                    "destination_account_number": t.destination_account_number,
                    "transaction_date": t.date
                }
                for t in transactions
            ]
        }


    # ------------------------------
    # Récupération de la liste des bénéficiaires d’un compte
    # ------------------------------
    def get_beneficiaries(self, session: Session, account_number: str):
        """
        Récupère uniquement les numéros de comptes bénéficiaires d’un compte donné.
        """
        return session.exec(
            select(Beneficiary.beneficiary_account_number)
            .where(Beneficiary.owner_account_number == account_number)
        ).all()
        
    # ============================================================
    # Ouverture d’un compte
    # ============================================================
    def open_account(self, session: Session, account_number: str, parent_account_number: str, initial_balance: Decimal = 0) -> BankAccount:
        """Ouvre un nouveau compte secondaire :
        - Vérifie que le compte n’existe pas déjà actif
        - Vérifie que le parent existe et est actif
        - Initialise le solde et associe le parent"""
        
        # Vérifie que le compte n'existe pas déjà
        existing_account = session.get(BankAccount, account_number)
        if existing_account and existing_account.is_active:
            raise HTTPException(400, f"Le compte {account_number} existe déjà et est actif.")

        # Récupère le compte parent
        parent_account = self.get_account(session, parent_account_number)
        if not parent_account.is_active:
            raise HTTPException(400, f"Le compte parent {parent_account_number} est fermé.")

        # Création d’un nouveau compte
        account = BankAccount(
            account_number=account_number,
            balance=initial_balance,
            is_active=True,
            parent_account_number=parent_account.account_number
        )

        session.add(account)
        session.commit()
        session.refresh(account)
        return account
    
    # ============================================================
    # Clôture d’un compte
    # ============================================================
    def close_account(self, session: Session, account_number: str) -> BankAccount:
        """
        Clôture un compte secondaire :
        - Vérifie son existence
        - Vérifie que ce n’est pas un compte parent avec enfants actifs
        - Transfère le solde vers le compte parent si nécessaire
        - Désactive le compte via BankAccount.close_account()
        """
        account = self.get_account(session, account_number)

        # Interdit la clôture d'un parent s'il a des enfants actifs
        if account.child_accounts:
            active_children = [c for c in account.child_accounts if c.is_active]
            if active_children:
                raise HTTPException(400, "Impossible de clôturer un compte parent tant que des comptes secondaires sont actifs.")

        if not account.is_active:
            raise HTTPException(400, "Le compte est déjà clôturé.")

        # Transfert du solde vers le parent si c'est un compte secondaire
        if account.balance > 0 and account.parent_account_number:
            parent_account = self.get_account(session, account.parent_account_number)
            account.transfer_to(parent_account, account.balance)

        account.close_account()
        session.add(account)
        session.commit()
        session.refresh(account)
        return account


    # ============================================================
    # Archivage d’un compte clôturé
    # ============================================================
    def archive_account(self, session: Session, account_number: str, reason: str = "Clôture du compte"):
        """
        Archive un compte clôturé :
        - Crée un ArchivedBankAccount à partir de BankAccount.archive()
        - Supprime le compte original de la table principale
        - Conserve la référence parent-enfant
        """
        account = self.get_account(session, account_number)

        if account.is_active:
            raise HTTPException(400, "Impossible d’archiver un compte encore actif.")
        if not account.closed_at:
            raise HTTPException(400, "Le compte doit être clôturé avant archivage.")

        archived = account.archive()

        session.add(archived)
        session.commit()

        return {
            "message": f"Le compte {account_number} a été archivé avec succès.",
            "archived_at": archived.archived_at,
            "parent_account_number": archived.parent_account_number
        }




# ------------------------------
# Instance unique (singleton) du service
# ------------------------------
# Cette instance peut être importée et utilisée directement dans les routes FastAPI
bank_service = BankService()