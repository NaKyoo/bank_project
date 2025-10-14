from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional

class Beneficiary:
    def __init__(self, beneficiary_account_number: str):
        self.beneficiary_account_number = beneficiary_account_number

class Transaction:
    def __init__(
        self,
        transaction_type: str,
        amount: Decimal,
        source_account_number: Optional[str] = None,
        destination_account_number: Optional[str] = None
    ):
        self.transaction_type = transaction_type  # "deposit" ou "transfer"
        self.amount = amount
        self.source_account_number = source_account_number
        self.destination_account_number = destination_account_number
        self.date = datetime.now()

class BankAccount:
    def __init__(self, account_number: str, initial_balance: Decimal = Decimal("0")):
        self.account_number = account_number
        self.balance = initial_balance
        self.beneficiaries: Dict[str, Beneficiary] = {}
        self.transactions: List[Transaction] = []

    def deposit(self, deposit_amount: Decimal) -> Transaction:
        if deposit_amount <= 0:
            raise ValueError("Le montant du dépôt doit être positif")
        self.balance += deposit_amount
        transaction = Transaction(
            transaction_type="deposit",
            amount=deposit_amount,
            source_account_number=None,
            destination_account_number=self.account_number
        )
        self.transactions.append(transaction)
        return transaction

    def transfer_to(self, destination_account: "BankAccount", transfer_amount: Decimal) -> Transaction:
        if transfer_amount <= 0:
            raise ValueError("Le montant du transfert doit être positif")
        if self.account_number == destination_account.account_number:
            raise ValueError("Le compte source et le compte destinataire doivent être différents")
        if self.balance < transfer_amount:
            raise ValueError("Solde insuffisant pour le transfert")
        self.balance -= transfer_amount
        destination_account.balance += transfer_amount
        transaction = Transaction(
            transaction_type="transfer",
            amount=transfer_amount,
            source_account_number=self.account_number,
            destination_account_number=destination_account.account_number
        )
        self.transactions.append(transaction)
        destination_account.transactions.append(transaction)
        return transaction

    def add_beneficiary(self, beneficiary_account: "BankAccount"):
        if beneficiary_account.account_number == self.account_number:
            raise ValueError("Impossible d'ajouter soi-même comme bénéficiaire")
        if beneficiary_account.account_number in self.beneficiaries:
            raise ValueError("Ce compte est déjà un bénéficiaire")

        self.beneficiaries[beneficiary_account.account_number] = Beneficiary(
            beneficiary_account.account_number
        )
        return {
            "owner_account": self.account_number,
            "beneficiary_account_number": beneficiary_account.account_number
        }