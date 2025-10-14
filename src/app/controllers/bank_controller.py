from fastapi import APIRouter, HTTPException, Path
from decimal import Decimal
from app.schemas.transfer import TransferRequest, Transfer
from app.schemas.beneficiary import BeneficiaryRequest
from app.services.bank_service import bank_service

router = APIRouter()

@router.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}

@router.post("/transfer", response_model=Transfer)
def make_transfer(request: TransferRequest):
    result = bank_service.transfer(
        from_acc=request.from_account,
        to_acc=request.to_account,
        amount=request.amount
    )
    return Transfer(
        date=result.date,
        from_account=request.from_account,
        to_account=request.to_account,
        amount=request.amount,
        status="completed"
    )

@router.post("/deposit")
def deposit(account_number: str, amount: Decimal):
    return bank_service.deposit(account_number, amount)

@router.get("/accounts/{account_number}")
def get_account_info(account_number: str = Path(..., description="Numéro du compte")):
    return bank_service.get_account_info(account_number)

@router.post("/accounts/{owner_account_number}/beneficiaries")
def add_beneficiary(owner_account_number: str, request: BeneficiaryRequest):
    try:
        beneficiary_account_number = request.account_number
        return bank_service.add_beneficiary(owner_account_number, beneficiary_account_number)
    except HTTPException as e:
        raise e

@router.get("/accounts/{owner_account_number}/beneficiaries")
def list_beneficiaries(owner_account_number: str):
    account = bank_service.get_account(owner_account_number)
    return [
        {"beneficiary_account_number": beneficiary.beneficiary_account_number}
        for beneficiary in account.beneficiaries.values()
    ]
