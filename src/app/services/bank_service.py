from fastapi import HTTPException
from sqlmodel import Session, select
from decimal import Decimal
from app.models.account import BankAccount, Transaction
from app.models.beneficiary import Beneficiary


class BankService:
    def __init__(self):
        from app.db import create_db_and_tables
        create_db_and_tables()

    def get_account(self, session: Session, account_number: str) -> BankAccount:
        account = session.get(BankAccount, account_number)
        if not account:
            raise HTTPException(404, f"Compte '{account_number}' non trouvé")
        return account

    def deposit(self, session: Session, account_number: str, amount: Decimal) -> Transaction:
        account = self.get_account(session, account_number)
        transaction = account.deposit(amount)
        session.add_all([account, transaction])
        session.commit()
        session.refresh(transaction)
        return transaction

    def transfer(self, session: Session, from_acc: str, to_acc: str, amount: Decimal) -> Transaction:
        source = self.get_account(session, from_acc)
        destination = self.get_account(session, to_acc)
        transaction = source.transfer_to(destination, amount)
        session.add_all([source, destination, transaction])
        session.commit()
        session.refresh(transaction)
        return transaction

    def add_beneficiary(self, session: Session, owner_account_number: str, target_account_number: str) -> Beneficiary:
        owner = self.get_account(session, owner_account_number)
        target = self.get_account(session, target_account_number)
        new_beneficiary = owner.add_beneficiary(target)
        session.add(new_beneficiary)
        session.commit()
        session.refresh(new_beneficiary)
        return new_beneficiary

    def get_account_info(self, session: Session, account_number: str):
        account = self.get_account(session, account_number)

        beneficiaries = session.exec(
            select(Beneficiary.beneficiary_account_number)
            .where(Beneficiary.owner_account_number == account_number)
        ).all()

        transactions = session.exec(
            select(Transaction)
            .where(
                (Transaction.source_account_number == account_number) |
                (Transaction.destination_account_number == account_number)
            )
        ).all()

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

    def get_beneficiaries(self, session: Session, account_number: str):
        return session.exec(
            select(Beneficiary.beneficiary_account_number)
            .where(Beneficiary.owner_account_number == account_number)
        ).all()


# instance unique
bank_service = BankService()
