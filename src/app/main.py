from fastapi import FastAPI
import uvicorn
from app.models.transfer import TransferRequest, Transfer
from app.services.bank_service import bank_service



app = FastAPI(title="Bank Project API")


@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
    
    
    
@app.post("/transfer", response_model=Transfer)
def make_transfer(request: TransferRequest):
    result = bank_service.transfer_money(
        from_account=request.from_account,
        to_account=request.to_account,
        amount=request.amount
    )

    return Transfer(
        date=result["date"],
        from_account=result["from_account"],
        to_account=result["to_account"],
        amount=result["amount"],
        status="completed"
    )
    
@app.get("/accounts/{account_number}")
def get_account(account_number: str):
    """Permet de vérifier le solde d’un compte"""
    account = bank_service.get_account(account_number)
    return {
        "account_number": account.account_number,
        "balance": account.balance
    }