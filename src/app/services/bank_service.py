from decimal import Decimal
from typing import Dict
from fastapi import HTTPException
from app.models.account import BankAccount

class BankService:
    def __init__(self):
        self.accounts: Dict[str, BankAccount] = {
            "COMPTE_EPARGNE": BankAccount("COMPTE_EPARGNE", Decimal("150")),
            "COMPTE_COURANT": BankAccount("COMPTE_COURANT", Decimal("150")),
            "COMPTE_JOINT": BankAccount("COMPTE_JOINT", Decimal("150")),
        }

    def get_account(self, account_number: str) -> BankAccount:
        account = self.accounts.get(account_number)
        if not account:
            raise HTTPException(404, f"Compte '{account_number}' non trouvé")
        return account

    def deposit(self, account_number: str, amount: Decimal):
        account = self.get_account(account_number)
        try:
            return account.deposit(amount)
        except ValueError as e:
            raise HTTPException(400, str(e))

    def transfer(self, from_acc: str, to_acc: str, amount: Decimal):
        source = self.get_account(from_acc)
        destination = self.get_account(to_acc)
        try:
            return source.transfer_to(destination, amount)
        except ValueError as e:
            raise HTTPException(400, str(e))

    def add_beneficiary(self, owner_account_number: str, target_account_number: str):
        owner_account = self.get_account(owner_account_number)
        target_account = self.get_account(target_account_number)

        try:
            return owner_account.add_beneficiary(target_account)
        except ValueError as e:
            raise HTTPException(400, str(e))

    def get_account_info(self, account_number: str):
        bank_account = self.get_account(account_number)
        
        beneficiary_list = [
            {
                "beneficiary_name": beneficiary.name,
                "beneficiary_account_number": beneficiary.beneficiary_account_number
            }
            for beneficiary in bank_account.beneficiaries.values()
        ]
        
        transaction_list = [
            {
                "transaction_type": transaction.transaction_type,
                "transaction_amount": transaction.amount,
                "source_account_number": transaction.source_account_number,
                "destination_account_number": transaction.destination_account_number,
                "transaction_date": transaction.date
            }
            for transaction in bank_account.transactions
        ]
        
        return {
            "account_number": bank_account.account_number,
            "current_balance": bank_account.balance,
            "beneficiaries": beneficiary_list,
            "transactions": transaction_list
        }
        
    def get_beneficiaries(self, account_number: str):
        bank_account = self.get_account(account_number)
        return list(bank_account.beneficiaries)


# instance unique du service
bank_service = BankService()
