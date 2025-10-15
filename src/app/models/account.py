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

    # Relations
    transactions: List[Transaction] = Relationship(
        back_populates="source_account",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.source_account_number]"}
    )
    incoming_transactions: List[Transaction] = Relationship(
        back_populates="destination_account",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.destination_account_number]"}
    )
    beneficiaries: List["Beneficiary"] = Relationship( # type: ignore
        back_populates="owner",
        sa_relationship_kwargs={"foreign_keys": "[Beneficiary.owner_account_number]"}
    )

    # Méthodes métier (encapsulation via méthode)
    def deposit(self, amount: Decimal) -> Transaction:
        if amount <= 0:
            raise ValueError("Le montant du dépôt doit être positif")
        self.balance += amount
        return Transaction(
            transaction_type="deposit",
            amount=amount,
            destination_account_number=self.account_number
        )

    def transfer_to(self, target: "BankAccount", amount: Decimal) -> Transaction:
        if amount <= 0:
            raise ValueError("Le montant du transfert doit être positif")
        if self.balance < amount:
            raise ValueError("Solde insuffisant")
        if self.account_number == target.account_number:
            raise ValueError("Impossible de transférer vers soi-même")

        self.balance -= amount
        target.balance += amount
        return Transaction(
            transaction_type="transfer",
            amount=amount,
            source_account_number=self.account_number,
            destination_account_number=target.account_number
        )

    def add_beneficiary(self, beneficiary_account: "BankAccount") -> "Beneficiary": # type: ignore
        from app.models.beneficiary import Beneficiary

        if beneficiary_account.account_number == self.account_number:
            raise ValueError("Impossible d'ajouter soi-même comme bénéficiaire")

        existing = [b.beneficiary_account_number for b in self.beneficiaries]
        if beneficiary_account.account_number in existing:
            raise ValueError("Ce compte est déjà un bénéficiaire")

        new_beneficiary = Beneficiary(
            owner_account_number=self.account_number,
            beneficiary_account_number=beneficiary_account.account_number
        )
        self.beneficiaries.append(new_beneficiary)
        return new_beneficiary
