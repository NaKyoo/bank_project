from fastapi import HTTPException
from sqlmodel import Session, select
from app.models.account import BankAccount, Transaction
from app.models.beneficiary import Beneficiary
from app.db import get_session, engine
from decimal import Decimal

class BankService:
    def __init__(self):
        from app.db import create_db_and_tables
        create_db_and_tables()

    def get_account(self, session: Session, account_number: str) -> BankAccount:
        account = session.get(BankAccount, account_number)
        if not account:
            raise HTTPException(404, f"Compte '{account_number}' non trouvé")
        return account

    def deposit(self, session: Session, account_number: str, amount: Decimal):
        account = self.get_account(session, account_number)
        if amount <= 0:
            raise HTTPException(400, "Le montant du dépôt doit être positif")
        account.balance += amount
        transaction = Transaction(transaction_type="deposit", amount=amount, destination_account_number=account.account_number)
        session.add(transaction)
        session.add(account)
        session.commit()
        session.refresh(account)
        return transaction

    def transfer(self, session: Session, from_acc: str, to_acc: str, amount: Decimal):
        source = self.get_account(session, from_acc)
        destination = self.get_account(session, to_acc)
        if amount <= 0:
            raise HTTPException(400, "Le montant du transfert doit être positif")
        if source.balance < amount:
            raise HTTPException(400, "Solde insuffisant")
        source.balance -= amount
        destination.balance += amount

        transaction = Transaction(
            transaction_type="transfer",
            amount=amount,
            source_account_number=source.account_number,
            destination_account_number=destination.account_number
        )
        session.add_all([source, destination, transaction])
        session.commit()
        session.refresh(transaction)
        return transaction

    def add_beneficiary(self, session: Session, owner_account_number: str, target_account_number: str):
        owner_account = session.get(BankAccount, owner_account_number)
        target_account = session.get(BankAccount, target_account_number)

        if not owner_account or not target_account:
            raise HTTPException(404, "Compte non trouvé")
        if owner_account_number == target_account_number:
            raise HTTPException(400, "Impossible d'ajouter soi-même comme bénéficiaire")
        
        # Vérifie si le bénéficiaire existe déjà
        existing = session.exec(
            select(Beneficiary).where(
                Beneficiary.owner_account_number == owner_account_number,
                Beneficiary.beneficiary_account_number == target_account_number
            )
        ).first()
        if existing:
            raise HTTPException(400, "Ce compte est déjà un bénéficiaire")
        
        new_beneficiary = Beneficiary(
            owner_account_number=owner_account_number,
            beneficiary_account_number=target_account_number
        )
        session.add(new_beneficiary)
        session.commit()
        session.refresh(new_beneficiary)
        return new_beneficiary

    def get_account_info(self, session: Session, account_number: str):
        account = session.get(BankAccount, account_number)
        if not account:
            raise HTTPException(404, "Compte non trouvé")
        
        # Bénéficiaires
        beneficiaries = session.exec(
            select(Beneficiary.beneficiary_account_number)
            .where(Beneficiary.owner_account_number == account_number)
        ).all()
        
        # Transactions
        transactions = session.exec(
            select(Transaction)
            .where(
                (Transaction.source_account_number == account_number) |
                (Transaction.destination_account_number == account_number)
            )
        ).all()
        
        transaction_list = [
            {
                "transaction_type": t.transaction_type,
                "transaction_amount": t.amount,
                "source_account_number": t.source_account_number,
                "destination_account_number": t.destination_account_number,
                "transaction_date": t.date
            }
            for t in transactions
        ]
        
        return {
            "account_number": account.account_number,
            "current_balance": account.balance,
            "beneficiaries": [{"beneficiary_account_number": b} for b in beneficiaries],
            "transactions": transaction_list
    }

        
    def get_beneficiaries(self, session: Session, account_number: str):
        return session.exec(
            select(Beneficiary.beneficiary_account_number)
            .where(Beneficiary.owner_account_number == account_number)
        ).all()



# instance unique du service
bank_service = BankService()
