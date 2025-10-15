from fastapi import APIRouter, Path, Depends        
from decimal import Decimal                         
from fastapi.params import Body                     
from sqlmodel import Session                        

from app.models.transfer import TransferRequest, Transfer  
from app.services.bank_service import bank_service          
from app.db import get_session          

from fastapi import HTTPException 
from app.models.account import Transaction   
                
# ------------------------------
# Création du routeur principal de l’application
# ------------------------------
router = APIRouter()
# Ce routeur regroupe les routes liées à la gestion des comptes et transferts bancaires.


@router.get("/")
async def read_root():
    """Route de test pour vérifier que l’API fonctionne."""
    return {"message": "Hello, FastAPI!"}


# ------------------------------
# Effectuer un transfert entre deux comptes
# ------------------------------
@router.post("/transfer", response_model=Transfer)
def make_transfer(request: TransferRequest, session: Session = Depends(get_session)):
    """
    Endpoint pour exécuter un transfert entre deux comptes :
    - Vérifie les comptes source et destination
    - Crée une transaction de type 'transfer'
    - Renvoie les informations du transfert effectué
    """
    # Appel du service pour exécuter le transfert
    result = bank_service.transfer(
        session,
        from_acc=request.from_account,
        to_acc=request.to_account,
        amount=request.amount
    )

    # Retourne une instance du modèle Transfer (réponse API)
    return Transfer(
        date=result.date,
        from_account=request.from_account,
        to_account=request.to_account,
        amount=request.amount,
        status="completed"
    )


# ------------------------------
# Effectuer un dépôt sur un compte
# ------------------------------
@router.post("/deposit")
def deposit(account_number: str, deposit_amount: Decimal, session: Session = Depends(get_session)):
    """
    Endpoint pour effectuer un dépôt :
    - Vérifie le compte
    - Ajoute le montant au solde
    - Crée une transaction 'deposit'
    """
    return bank_service.deposit(session, account_number, deposit_amount)


# ------------------------------
# Obtenir les informations d’un compte
# ------------------------------
@router.get("/accounts/{account_number}")
def get_account_info(account_number: str = Path(..., description="Numéro du compte"), 
                     session: Session = Depends(get_session)):
    """
    Endpoint pour récupérer toutes les informations d’un compte :
    - Solde actuel
    - Liste des bénéficiaires
    - Historique des transactions
    """
    return bank_service.get_account_info(session, account_number)


# ------------------------------
# Ajouter un bénéficiaire à un compte
# ------------------------------
@router.post("/accounts/{owner_account_number}/beneficiaries")
def add_beneficiary(owner_account_number: str, 
                    beneficiary_account_number: str = Body(..., embed=True), 
                    session: Session = Depends(get_session)):
    """
    Endpoint pour ajouter un bénéficiaire :
    - Le propriétaire (owner) ajoute un autre compte comme bénéficiaire
    - Vérifie que ce n’est pas le même compte
    - Crée un lien Beneficiary en base
    """
    return bank_service.add_beneficiary(session, owner_account_number, beneficiary_account_number)


# ------------------------------
# Lister les bénéficiaires d’un compte
# ------------------------------
@router.get("/accounts/{owner_account_number}/beneficiaries")
def list_beneficiaries(owner_account_number: str, session: Session = Depends(get_session)):
    """
    Endpoint pour obtenir la liste des bénéficiaires liés à un compte.
    - Retourne la liste des numéros de comptes bénéficiaires
    """
    beneficiaries = bank_service.get_beneficiaries(session, owner_account_number)
    return [{"beneficiary_account_number": b} for b in beneficiaries]


@router.get("/transaction/{transaction_id}" , response_model=Transaction)
# session va permettre de lire  et trasaction_id est récupérer depuis l'url
def detail_transaction( transaction_id: int , session: Session = Depends(get_session)): 
    # transaction est un objet Transaction, résultat de DB (objet ou None)
    # retourn l'instance transaction dont le PK vaut transaction_id
    #transaction = session.get(Transaction , transaction_id) # interroge la DB pourt savoir si il y a une transaction  
    transaction = session.exec(text("""
                                    SELECT  t.transaction_id, 
                                            t.transaction_type, 
                                            t.amount, 
                                            t.source_account_number, 
                                            t.destination_account_number,
                                            t.date
                                            u.name 
                                    FROM transaction AS t
                                    INNER JOIN bankaccount AS b ON b.source_account_number = transaction.source_account_number
                                    INNER JOIN user AS u ON u.user_id = b.user_id
                                    WHERE transaction_id = {trasaction_id}
                                    """
                                    ))
    if not transaction :
        raise HTTPException(status_code=404, detail="Id transaction not found")
    return transaction

