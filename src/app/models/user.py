from decimal import Decimal
from typing import Annotated, List, Optional
import uuid
from pydantic import BaseModel, EmailStr
from pydantic.types import StringConstraints
from sqlmodel import Relationship, SQLModel, Field
from passlib.context import CryptContext
from app.models.account import BankAccount

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    is_active: bool = True
    
    
    bank_accounts: List["BankAccount"] = Relationship( # type: ignore
    back_populates="owner",
    sa_relationship_kwargs={"foreign_keys": "[BankAccount.owner_id]"}
)
    
    @classmethod
    def register (cls, email: str, password: str) -> "User":
        
        # Hashage du mot de passe
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        hashed_password = pwd_context.hash(password)
        
        # Création de l'utilisateur avec son compte bancaire principal lors de l'ouverture
        new_user = cls(email=email, hashed_password=hashed_password)
        
        primary_bank_account = BankAccount( # type: ignore
            account_number=f"ACC{uuid.uuid4().hex[:12].upper()}",
            balance= Decimal("0.00"),
            is_active=True,
            owner=new_user
        )
    
        # Lien entre l'utilisateur et son compte bancaire principal
        new_user.bank_accounts.append(primary_bank_account) # type: ignore
        
        deposit_transaction = primary_bank_account.deposit(amount=Decimal("100.00"))
        
        primary_bank_account.transactions.append(deposit_transaction)

        return new_user
    
    
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=8, pattern=r"^[A-Za-z\d@$!%*?&]+$")]
    

class UserRegisterResponse(BaseModel):
    id : int
    email : str
    primary_account_number : str
    
    
class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    
class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
