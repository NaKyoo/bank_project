from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from passlib.context import CryptContext
from sqlmodel import SQLModel, Field, Relationship


if TYPE_CHECKING:
    # Import pour les annotations de type uniquement (évite import circulaire à l'exécution)
    from app.models.account import BankAccount


# Password hashing context (bcrypt) — used by User helpers
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)  # index pour accélérer les recherches par email
    password_hash: str
    name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = Field(default=True)
    role: str = Field(default="customer")
    creation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

    # Relation inverse vers les comptes (import retardé via string pour éviter import circulaire)
    accounts: List["BankAccount"] = Relationship(back_populates="user")

    def set_password(self, plain_password: str) -> None:
        self.password_hash = pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        try:
            return pwd_context.verify(plain_password, self.password_hash)
        except Exception:
            return False

    @property
    def full_name(self) -> str:
        parts = [p for p in (self.name, self.last_name) if p]
        return " ".join(parts)


class UserCreate(SQLModel):
    email: str
    password: str
    name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: str = "customer"


class UserRead(SQLModel):
    user_id: Optional[int]
    email: str
    name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    role: str = "customer"
    creation_date: datetime
    last_login: Optional[datetime] = None

    class Config:
        orm_mode = True


class UserUpdate(SQLModel):
    name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None