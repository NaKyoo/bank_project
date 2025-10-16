from pydantic import Field
from datetime import datetime
from sqlmodel import Field, SQLModel
from typing import Optional 


class User(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    last_name: str
    creation_date: datetime