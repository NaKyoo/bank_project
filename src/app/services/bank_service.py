from threading import Thread
from time import sleep
from fastapi import HTTPException             
from sqlmodel import Session, select          
from decimal import Decimal                   

from app.db import engine
from app.models.account import BankAccount, Transaction, TransactionStatus
from app.models.beneficiary import Beneficiary
from app.models.user import User
import uuid
from datetime import datetime, timezone


# ------------------------------
# Service bancaire principal
# ------------------------------
class BankService:
   


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
        # return account info, beneficiaries and completed transactions
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
    

    # Historique des transactions d'un compte
    def get_transaction_history(self, session: Session, account_number: str, current_user: User):
        """Return completed transactions for an account (ordered desc).

        This method requires an authenticated `current_user` (provided by the
        FastAPI dependency `get_current_user`). It enforces that only the owner
        of the account or an admin can access the history.
        """
        # S'assurer que le compte existe
        account = self.get_account(session, account_number)

        # Exiger une authentification explicite
        if not current_user:
            raise HTTPException(401, "Authentification requise")

        # Vérifier que le compte appartient à l'utilisateur courant (ou admin)
        user_accounts = [a["account_number"] for a in self.get_user_accounts(session, current_user.user_id)]
        if account_number not in user_accounts and current_user.role != "admin":
            raise HTTPException(403, "Accès refusé")

        transactions = session.exec(
            select(Transaction)
            .where(
                ((Transaction.source_account_number == account_number) |
                 (Transaction.destination_account_number == account_number)) &
                (Transaction.status == TransactionStatus.COMPLETED)
            )
            .order_by(Transaction.date.desc())
        ).all()

        return [
            {
                "amount": t.amount,
                "date": t.date,
                "source": t.source_account_number,
                "destination": t.destination_account_number
            }
            for t in transactions
        ]


    # renvoit les comptes d'un utilisateur
    def get_user_accounts(self, session: Session, user_id: int):
        from app.models.account import BankAccount
        accounts = session.exec(
            select(BankAccount)
            .where(BankAccount.user_id == user_id)
            .order_by(BankAccount.creation_date.desc())
        ).all()
        return [
            {
                "account_number": acc.account_number,
                "balance": acc.balance
            }
            for acc in accounts
        ]

    def register_user(self, session: Session, email: str, password: str):
        """Crée un utilisateur et un compte principal, retourne {'user': user, 'primary_account_number': str}"""
        existing = self.get_user_by_email(session, email)
        if existing:
            raise HTTPException(400, "Un utilisateur avec cet email existe déjà")

        # Create user
        user = User(email=email)
        user.set_password(password)

        # Create primary bank account
        from app.models.account import BankAccount
        primary = BankAccount(account_number=f"ACC{uuid.uuid4().hex[:12].upper()}", balance=0)
        user.accounts.append(primary)

        session.add_all([user, primary])
        session.commit()
        session.refresh(user)

        return {"user": user, "primary_account_number": primary.account_number}


    # User management
    def get_user(self, session: Session, user_id: int) -> User:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(404, f"User with id {user_id} not found")
        return user
    

    def get_user_by_email(self, session: Session, email: str) -> User | None:
        return session.exec(select(User).where(User.email == email)).first()
    

    def create_user(self, session: Session, email: str, password: str, name: str | None = None, last_name: str | None = None, phone: str | None = None, role: str = "customer") -> User:
        existing = self.get_user_by_email(session, email)
        if existing:
            raise HTTPException(400, "Un utilisateur avec cet email existe déjà")

        user = User(email=email, name=name, last_name=last_name, phone=phone, role=role)
        user.set_password(password)

        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    

    def update_user(self, session: Session, user_id: int, **fields) -> User:
        user = self.get_user(session, user_id)
        if "password" in fields and fields["password"]:
            user.set_password(fields.pop("password"))

        allowed = {"name", "last_name", "phone", "role", "is_active"}
        for k, v in list(fields.items()):
            if k in allowed:
                setattr(user, k, v)

        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    

    def deactivate_user(self, session: Session, user_id: int) -> User:
        user = self.get_user(session, user_id)
        user.is_active = False
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


    def set_last_login(self, session: Session, user_id: int) -> User:
        user = self.get_user(session, user_id)
        user.last_login = datetime.now(timezone.utc)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
        
    # ============================================================
    # Ouverture d’un compte
    # ============================================================
    def open_account(self, session: Session, account_number: str, parent_account_number: str, initial_balance: Decimal = 0) -> BankAccount:
        """Ouvre un nouveau compte secondaire :
        - Vérifie que le compte n’existe pas déjà actif
        - Vérifie que le parent existe et est un compte principal actif
        - Vérifie que le solde initial est >= 0
        - Vérifie que le nombre total de comptes ne dépasse pas 5"""
        
        ##Vérifie que le numéro de compte est fourni
        if not account_number or account_number.strip() == "":
            raise HTTPException(400, "Le numéro du compte est obligatoire.")
        
        # Vérifie si le solde de base est négatif
        if initial_balance < 0:
            raise HTTPException(400, "Le solde initial ne peut pas être négatif.")
        
        # Vérifie le nombre total de comptes
        total_accounts = session.exec(select(BankAccount)).all()
        if len(total_accounts) >= 5:
            raise HTTPException(400, "Impossible de créer plus de 5 comptes au total.")
        
        # Vérifie que le compte n'existe pas déjà
        existing_account = session.get(BankAccount, account_number)
        if existing_account and existing_account.is_active:
            raise HTTPException(400, f"Le compte {account_number} existe déjà et est actif.")

        # Récupère le compte parent
        parent_account = self.get_account(session, parent_account_number)
        
        # Vérifie que le parent est actif et bien un compte principal
        if not parent_account.is_active:
            raise HTTPException(400, f"Le compte parent {parent_account_number} est fermé.")
        if parent_account.parent_account_number is not None:
            raise HTTPException(400, "Le compte parent doit être un compte principal.")

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
    # Récupération des infos d'une transaction
    # ------------------------------
    def get_transaction_detail(self, session: Session, transaction_id: int, user_account_number: str):
        # return transaction details if user_account_number is source or destination
        transaction = session.get(Transaction, transaction_id)
        if not transaction:
            raise HTTPException(404, f"Transaction {transaction_id} introuvable")

        if user_account_number not in [transaction.source_account_number, transaction.destination_account_number]:
            raise HTTPException(403, "Vous n'êtes pas autorisé à consulter cette transaction")

        return {
            "transaction_id": transaction.id,
            "transaction_type": transaction.transaction_type,
            "amount": transaction.amount,
            "date": transaction.date,
            "source_account_number": transaction.source_account_number,
            "destination_account_number": transaction.destination_account_number,
            "status": transaction.status
        }


    def get_user_full_info(self, session: Session, user_id: int):
            # return user info and associated accounts
            user_record = session.get(User, user_id)
            if not user_record:
                raise HTTPException(404, f"Utilisateur avec l'ID {user_id} introuvable")

            # Vérifie si l'utilisateur est actif
            if not user_record.is_active:
                raise HTTPException(403, f"L'utilisateur {user_record.email} est inactif")

            # Liste des comptes de l'utilisateur
            comptes_info = [
                {
                    "account_number": compte.account_number,
                    "current_balance": compte.balance,
                    "is_active": compte.is_active,
                    "parent_account_number": compte.parent_account_number
                }
                for compte in user_record.bank_accounts
            ]

            return {
                "user_id": user_record.user_id,
                "email": user_record.email,
                "is_active": user_record.is_active,
                "accounts": comptes_info,
            }


# ------------------------------
# Instance unique (singleton) du service
# ------------------------------
# Cette instance peut être importée et utilisée directement dans les routes FastAPI
bank_service = BankService()