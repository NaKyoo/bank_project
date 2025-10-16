from typing import List, Optional
from sqlmodel import Relationship, SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    is_active: bool = True
    
    
    bank_accounts: List["BankAccount"] = Relationship( # type: ignore
    back_populates="owner",
    sa_relationship_kwargs={"foreign_keys": "[BankAccount.owner_id]"}
)
    
def get_account_info(self, account_number: str):
        """
        Retourne les informations d'un compte associé à cet utilisateur.
        """
        for account in self.bank_accounts:
            if account.account_number == account_number:
                return {
                    "account_number": account.account_number,
                    "balance": account.balance,
                    "is_active": account.is_active,
                    "parent_account_number": account.parent_account_number,
                }
        return None