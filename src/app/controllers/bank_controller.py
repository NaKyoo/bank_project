from fastapi import APIRouter,  Path, Depends
from decimal import Decimal
from fastapi.params import Body
from sqlmodel import Session
from app.models.transfer import TransferRequest, Transfer
from app.services.bank_service import bank_service
from app.db import get_session

router = APIRouter()

@router.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}


@router.post("/transfer", response_model=Transfer)
def make_transfer(request: TransferRequest, session: Session = Depends(get_session)):
    result = bank_service.transfer(
        session,
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
def deposit(account_number: str, deposit_amount: Decimal, session: Session = Depends(get_session)):
    return bank_service.deposit(session, account_number, deposit_amount)


@router.get("/accounts/{account_number}")
def get_account_info(account_number: str = Path(..., description="Numéro du compte"), 
                     session: Session = Depends(get_session)):
    return bank_service.get_account_info(session, account_number)


@router.post("/accounts/{owner_account_number}/beneficiaries")
def add_beneficiary(owner_account_number: str, 
                    beneficiary_account_number: str = Body(..., embed=True), 
                    session: Session = Depends(get_session)):
    return bank_service.add_beneficiary(session, owner_account_number, beneficiary_account_number)


@router.get("/accounts/{owner_account_number}/beneficiaries")
def list_beneficiaries(owner_account_number: str, session: Session = Depends(get_session)):
    beneficiaries = bank_service.get_beneficiaries(session, owner_account_number)
    return [{"beneficiary_account_number": b} for b in beneficiaries]
