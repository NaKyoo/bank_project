from fastapi import APIRouter, Path, Depends        
from decimal import Decimal                         
from fastapi.params import Body                     
from sqlmodel import Session                        

from app.models.transfer import TransferRequest, Transfer  
from app.services.bank_service import bank_service          
from app.db import get_session                              


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


# ============================================================
# Clôturer un compte
# ============================================================
@router.post("/accounts/{account_number}/close")
def close_account(
    account_number: str = Path(..., description="Numéro du compte à clôturer"),
    session: Session = Depends(get_session)
):
    """
    Clôture un compte bancaire :
    - Le rend inactif (`is_active=False`)
    - Transfère automatiquement le solde vers le compte parent si c'est un compte secondaire
    - Vérifie qu'un compte parent avec enfants actifs ne peut pas être clôturé
    - Enregistre la date de clôture (`closed_at`)
    """
    account = bank_service.close_account(session, account_number)
    return {
        "message": f"Le compte {account.account_number} a été clôturé avec succès.",
        "closed_at": account.closed_at,
        "parent_account_number": account.parent_account_number
    }


# ============================================================
# Archiver un compte clôturé
# ============================================================
@router.post("/accounts/{account_number}/archive")
def archive_account(
    account_number: str = Path(..., description="Numéro du compte à archiver"),
    reason: str = Body(default="Clôture du compte", embed=True),
    session: Session = Depends(get_session)
):
    """
    Archive un compte clôturé :
    - Crée une entrée dans la table 'archived_bank_accounts'
    - Conserve le lien parent-enfant
    - Supprime le compte original
    """
    result = bank_service.archive_account(session, account_number, reason)
    return result
