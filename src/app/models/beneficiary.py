from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

class Beneficiary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_account_number: str = Field(foreign_key="bankaccount.account_number")
    beneficiary_account_number: str = Field(foreign_key="bankaccount.account_number")

    owner: Optional["BankAccount"] = Relationship( # type: ignore
        back_populates="beneficiaries",
        sa_relationship_kwargs={"foreign_keys": "[Beneficiary.owner_account_number]"}
    )