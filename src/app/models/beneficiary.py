from typing import Dict

from pydantic import BaseModel

class Beneficiary:
    def __init__(self, name: str, account_number: str):
        self.name = name
        self.account_number = account_number

class BeneficiaryRequest(BaseModel):
    name: str
    account_number: str