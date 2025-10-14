from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime

class TransferRequest(BaseModel):
    from_account: str = Field(..., description="Numéro du compte source")
    to_account: str = Field(..., description="Numéro du compte destinataire")
    amount: Decimal = Field(..., gt=0, description="Montant à transférer (doit être positif)")
    
class Transfer(BaseModel):
    date: datetime = Field(default_factory=datetime.now, description="Date et heure du transfert")
    from_account: str
    to_account: str
    amount: Decimal
    status: str = "completed"
