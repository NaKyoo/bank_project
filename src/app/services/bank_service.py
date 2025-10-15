from typing import Optional
from fastapi import HTTPException             
from sqlmodel import Session, select          
from decimal import Decimal                   

from app.models.account import BankAccount, Transaction
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
        """
        Effectue un transfert d’argent entre deux comptes existants.
        """
        source = self.get_account(session, from_acc)           # Récupère le compte source
        destination = self.get_account(session, to_acc)        # Récupère le compte destinataire
        transaction = source.transfer_to(destination, amount)  # Effectue la logique du transfert
        session.add_all([source, destination, transaction])    # Ajoute les modifications à la session
        session.commit()                                       # Sauvegarde les changements
        session.refresh(transaction)                           # Actualise la transaction
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
                (Transaction.source_account_number == account_number) |  # Transactions sortantes
                (Transaction.destination_account_number == account_number)  # Transactions entrantes
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
        session.delete(account)
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
