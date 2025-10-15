from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import Optional, List


class User(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    last_name: str
    creation_date: datetime