import time
from datetime import datetime, timezone
import threading
from fastapi import APIRouter, HTTPException, Path, Depends       
from decimal import Decimal                         
from fastapi.params import Body                     
from sqlmodel import Session  
                 

from app.models.transfer import TransferRequest, Transfer  
from app.services.bank_service import bank_service          
from app.db import get_session, engine   
from app.services.transfer_manager import transfers_in_progress, transfer_counter                           


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
# Modifie auto pour finaliser les transferts après un délai
# ------------------------------
def transfer_delay(transfer_id: int):
    """Fonction qui attend 5 secondes puis finalise le transfert s’il n’=a pas été annulé."""
    time.sleep(5)

    transfer = transfers_in_progress.get(transfer_id)
    if not transfer:
        return  

    with Session(engine) as session:
        source = bank_service.get_account(session, transfer.from_account)
        dest = bank_service.get_account(session, transfer.to_account)

        if not source or not dest:
            transfer.status = "failed"
            del transfers_in_progress[transfer_id]
            return

        source.balance -= transfer.amount
        dest.balance += transfer.amount

        session.add(source)
        session.add(dest)
        
        session.commit()

    transfer.status = "completed"
    print(f"Transfert #{transfer_id} finalisé automatiquement.")
    

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
    global transfer_counter
    
    # Appel du service pour exécuter le transfert
    result = bank_service.transfer(
        session,
        from_acc=request.from_account,
        to_acc=request.to_account,
        amount=request.amount
    )

    # Retourne une instance du modèle Transfer (réponse API)
    transfer_counter += 1
    transfer = Transfer(
        id=transfer_counter,
        date=result.date,
        from_account=request.from_account,
        to_account=request.to_account,
        amount=request.amount,
        status="pending"
    )

    transfers_in_progress[transfer.id] = transfer

    # Thread pour finaliser le transfert
    threading.Thread(target=transfer_delay, args=(transfer.id,)).start()

    return transfer

# ------------------------------
# Annuler un transfert en cours
# ------------------------------
@router.post("/transfer/{transfer_id}/cancel")
def cancel_transfer(transfer_id: int):
    """Annule un transfert dans les 5 secondes suivant sa création."""
    transfer = transfers_in_progress.get(transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfert introuvable ou déjà finalisé.")
    
    if transfer.status != "pending":
        raise HTTPException(status_code=400, detail="Transfert déjà finalisé ou annulé.")
    
    if not transfer.can_be_cancelled():
        raise HTTPException(status_code=400, detail="Le délai de 5 secondes est expiré.")
    
    # Remboursement du compte source, si tu veux faire la logique inverse ici
    transfer.status = "cancelled"
    del transfers_in_progress[transfer_id]

    return {"message": f"Transfert #{transfer_id} annulé avec succès."}

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
# Ouvrir un compte
# ============================================================
@router.post("/accounts/open")
def open_account(
    account_number: str = Body(..., embed=True, description="Numéro du nouveau compte secondaire"),
    parent_account_number: str = Body(..., embed=True, description="Numéro du compte parent"),
    initial_balance: Decimal = Body(0, embed=True, description="Solde initial du compte"),
    session: Session = Depends(get_session)
):
    """Crée un nouveau compte secondaire rattaché à un compte parent existant.
    - Vérifie que le compte parent est actif
    - Initialise le solde
    - Retourne les informations du nouveau compte"""
    account = bank_service.open_account(session, account_number, parent_account_number, initial_balance)
    return {
        "message": f"Le compte {account.account_number} a été créé avec succès.",
        "account_number": account.account_number,
        "parent_account_number": account.parent_account_number,
        "current_balance": account.balance,
        "is_active": account.is_active
    }

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
