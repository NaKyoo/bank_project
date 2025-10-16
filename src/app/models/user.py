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
