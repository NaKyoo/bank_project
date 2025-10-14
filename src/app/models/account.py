from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_type: str
    amount: Decimal
    source_account_number: Optional[str] = Field(default=None, foreign_key="bankaccount.account_number")
    destination_account_number: Optional[str] = Field(default=None, foreign_key="bankaccount.account_number")
    date: datetime = Field(default_factory=datetime.now)

    
    # Relations
    source_account: Optional["BankAccount"] = Relationship(
        back_populates="transactions",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.source_account_number]"}
    )
    destination_account: Optional["BankAccount"] = Relationship(
        back_populates="incoming_transactions",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.destination_account_number]"}
    )
    
class BankAccount(SQLModel, table=True):
    account_number: str = Field(primary_key=True)
    balance: Decimal = Field(default=Decimal("0"))

    # transactions envoyées
    transactions: List["Transaction"] = Relationship(
        back_populates="source_account",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.source_account_number]"}
    )

    # transactions reçues
    incoming_transactions: List["Transaction"] = Relationship(
        back_populates="destination_account",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.destination_account_number]"}
    )

    # bénéficiaires
    beneficiaries: List["Beneficiary"] = Relationship( # type: ignore
        back_populates="owner",
        sa_relationship_kwargs={"foreign_keys": "[Beneficiary.owner_account_number]"}
    )

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
        from app.models.beneficiary import Beneficiary  # Import here to avoid circular import

        if beneficiary_account.account_number == self.account_number:
            raise ValueError("Impossible d'ajouter soi-même comme bénéficiaire")
        beneficiary_numbers = [b.beneficiary_account_number for b in self.beneficiaries]
        if beneficiary_account.account_number in beneficiary_numbers:
            raise ValueError("Ce compte est déjà un bénéficiaire")

        beneficiary = Beneficiary(
            owner_account_number=self.account_number,
            beneficiary_account_number=beneficiary_account.account_number
        )
        self.beneficiaries.append(beneficiary)
        return {
            "owner_account": self.account_number,
            "beneficiary_account_number": beneficiary_account.account_number
        }
