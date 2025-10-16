from fastapi import APIRouter, HTTPException, Path, Depends        
from decimal import Decimal                         
from fastapi.params import Body                     
from sqlmodel import Session, select                        

from app.models.account import BankAccount, Transaction, TransactionStatus
from app.models.transfer import TransferRequest, Transfer  
from app.models.user import User, UserLoginRequest, UserLoginResponse, UserRegisterRequest, UserRegisterResponse, create_access_token, get_current_user
from app.services.bank_service import bank_service          
from app.db import get_session                              

from passlib.context import CryptContext



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


@router.post("/transfer/{transaction_id}/cancel")
def cancel_transaction(transaction_id: int, session: Session = Depends(get_session)):
    # Récupère la transaction depuis la base via son ID
    transaction = session.get(Transaction, transaction_id)
    if not transaction:
        raise HTTPException(404, "Transaction non trouvée")

    # Vérifie que la transaction est encore PENDING avant de l'annuler
    if transaction.status != TransactionStatus.PENDING:
        raise HTTPException(400, "Impossible d'annuler une transaction déjà complétée ou annulée")

    # Récupère le compte source pour appliquer la logique métier d'annulation
    source_account = session.get(BankAccount, transaction.source_account_number)
    source_account.cancel_transfer(transaction)  # change le statut


    session.add(transaction)
    session.commit()
    session.refresh(transaction)

    # Si on voulait supprimer la transaction de la base plutôt que de la marquer comme CANCELED
    # session.delete(transaction)
    # session.commit()

    return {
        "message": f"Transaction {transaction_id} annulée",
        "status": transaction.status
    }


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
    - Le parent doit être un compte principal actif
    - Solde initial >= 0
    - Nombre total de comptes maximum : 5"""
    
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


@router.get("/transactions/{user_account_number}/{transaction_id}")
def get_transaction_detail(
    user_account_number: str = Path(..., description="Numéro du compte de l'utilisateur impliqué"),
    transaction_id: int = Path(..., description="ID de la transaction à consulter"),
    session: Session = Depends(get_session)
):
    """
    Récupère les détails d'une transaction par son ID.
    Vérifie que la transaction existe et que l'utilisateur est impliqué.
    """

    transaction_details = bank_service.get_transaction_detail(
        session=session,
        transaction_id=transaction_id,
        user_account_number=user_account_number
    )

    return transaction_details

# ============================================================
# Récupérer les informations complètes d’un utilisateur
# ============================================================

@router.get("/users/{user_id}/full_info")
def get_user_info(user_id: int = Path(..., description="ID de l'utilisateur"),
                  session: Session = Depends(get_session)):
    return bank_service.get_user_full_info(session, user_id)

# ============================================================
# Enregistrer un nouvel utilisateur avec un compte bancaire principal
# ============================================================

@router.post("/users/register", response_model=UserRegisterResponse)
def register_user(payload: UserRegisterRequest,session: Session = Depends(get_session)):
    """
    Enregistre un nouvel utilisateur avec un compte bancaire principal.
    - Hashage sécurisé du mot de passe
    - Création automatique d'un compte bancaire principal
    - Validation des données d'entrée
    """
    
    # Vérifie si le nom d'utilisateur est déjà pris
    existing_user = session.exec(select(User).where(User.email == payload.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà pris")

    # Crée l'utilisateur et son compte bancaire principal
    new_user = User.register(email=payload.email, password=payload.password)  # type: ignore

    # Ajoute l'utilisateur et son compte à la session et commit en base
    session.add(new_user)
    session.commit()
    session.refresh(new_user)


    return UserRegisterResponse(
        id=new_user.id,
        email=new_user.email,
        primary_account_number = new_user.bank_accounts[0].account_number

    )

# ============================================================
# Authentifier un utilisateur
# ============================================================
@router.post("/users/login", response_model=UserLoginResponse)
def login_user(payload: UserLoginRequest, session: Session = Depends(get_session)):
    """
    Authentifie un utilisateur avec son email et mot de passe.
    - Vérifie les informations d'identification
    - Retourne les informations de l'utilisateur et son compte principal
    """
    
    # Recherchez l'utilisateur par email
    db_user = session.exec(select(User).where(User.email == payload.email)).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    # Vérifiez le mot de passe
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    if not pwd_context.verify(payload.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    # Créez un token JWT
    access_token = create_access_token(db_user) # type: ignore

    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=db_user.id,
        email=db_user.email,
    )
    
# ============================================================
# Récupérer les informations de l'utilisateur courant via le token JWT
# ============================================================
@router.get("/users/me")
def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user