from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from sqlmodel import Session, select, SQLModel, create_engine
from app.controllers import bank_controller
from app.models.account import BankAccount

engine = create_engine("sqlite:///bank.db")

# Définition du lifespan pour startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- Startup ----
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        if not session.exec(select(BankAccount)).first():
            comptes = [
                BankAccount(account_number="COMPTE_EPARGNE", balance=150),
                BankAccount(account_number="COMPTE_COURANT", balance=150),
                BankAccount(account_number="COMPTE_JOINT", balance=150),
            ]
            session.add_all(comptes)
            session.commit()
    yield
    # ---- Shutdown ----
    

app = FastAPI(title="Bank Project API", lifespan=lifespan)
app.include_router(bank_controller.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
