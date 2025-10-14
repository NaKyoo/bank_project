from typing import Dict

from pydantic import BaseModel

class Beneficiary:
    def __init__(self, account_number: str):
        self.account_number = account_number

class BeneficiaryRequest(BaseModel):
    account_number: str