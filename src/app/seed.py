from sqlmodel import Session, select, create_engine , SQLModel 
from models.account import BankAccount 
from models.account import Transaction    
from models.beneficiary import Beneficiary

engine = create_engine("sqlite:///bank.db")
SQLModel.metadata.create_all(engine)

def seed ():
    with Session(engine) as session:
            # Si aucun compte n’existe encore dans la base...
            if not session.exec(select(BankAccount)).first():
                # ... alors on crée quelques comptes bancaires de base
                comptes = [
                    BankAccount(account_number="COMPTE_EPARGNE", balance=150),
                    BankAccount(account_number="COMPTE_COURANT", balance=150),
                    BankAccount(account_number="COMPTE_JOINT", balance=150),
                ]
                #...ici on créé des transactions en dur 
                transaction = [
                    Transaction(transaction_id=1 , transaction_type="transfert" , amount=19 , source_account_number="COMPTE_EPARGNE" , destination_account_number="COMPTE_COURANT")
                ]
                
                # On ajoute les comptes dans la session et on enregistre en base
                session.add_all(comptes)
                session.add_all(transaction)
                session.commit()
                
seed()
