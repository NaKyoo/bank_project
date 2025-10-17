from fastapi import APIRouter, HTTPException, Path, Depends        
from decimal import Decimal                         
from fastapi.params import Body                     
from sqlmodel import Session, select

from app.models.account import BankAccount, Transaction, TransactionStatus
from app.models.transfer import TransferRequest, Transfer
from app.models.user import (
    User,
    UserLoginRequest,
    UserLoginResponse,
    UserRegisterRequest,
    UserRegisterResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.services.bank_service import bank_service
from app.db import get_session
from app.security import create_access_token, get_current_user


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
def make_transfer(request: TransferRequest, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # transfer between accounts
    # Appel du service pour exécuter le transfert
    # Ensure the source account belongs to the authenticated user
    source_account = bank_service.get_account(session, request.from_account)
    if source_account.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")

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
def cancel_transaction(transaction_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # cancel a pending transfer
    transaction = session.get(Transaction, transaction_id)
    if not transaction:
        raise HTTPException(404, "Transaction non trouvée")

    # Vérifie que la transaction est encore PENDING avant de l'annuler
    if transaction.status != TransactionStatus.PENDING:
        raise HTTPException(400, "Impossible d'annuler une transaction déjà complétée ou annulée")

    # Récupère le compte source pour appliquer la logique métier d'annulation
    source_account = session.get(BankAccount, transaction.source_account_number)
    # Only owner of source (or admin) can cancel
    if source_account.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
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
def deposit(account_number: str, deposit_amount: Decimal, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # deposit into account (only owner or admin)
    account = bank_service.get_account(session, account_number)
    if account.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    return bank_service.deposit(session, account_number, deposit_amount)


# ------------------------------
# Obtenir les informations d’un compte
# ------------------------------
@router.get("/accounts/{account_number}")
def get_account_info(account_number: str = Path(..., description="Numéro du compte"), 
                     session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # get account info
    account = bank_service.get_account(session, account_number)
    if account.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    return bank_service.get_account_info(session, account_number)


# ------------------------------
# Ajouter un bénéficiaire à un compte
# ------------------------------
@router.post("/accounts/{owner_account_number}/beneficiaries")
def add_beneficiary(owner_account_number: str, 
                    beneficiary_account_number: str = Body(..., embed=True), 
                    session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # add beneficiary
    account = bank_service.get_account(session, owner_account_number)
    if account.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    return bank_service.add_beneficiary(session, owner_account_number, beneficiary_account_number)


# ------------------------------
# Lister les bénéficiaires d’un compte
# ------------------------------
@router.get("/accounts/{owner_account_number}/beneficiaries")
def list_beneficiaries(owner_account_number: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # list beneficiaries
    account = bank_service.get_account(session, owner_account_number)
    if account.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    beneficiaries = bank_service.get_beneficiaries(session, owner_account_number)
    return [{"beneficiary_account_number": b} for b in beneficiaries]


@router.get("/accounts/{account_number}/transactions")
def get_account_transactions(account_number: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # get transactions for account (only completed) and ensure ownership
    account = bank_service.get_account(session, account_number)
    if account.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    return bank_service.get_transaction_history(session, account_number, current_user)





# user endpoints
@router.post("/users", response_model=UserRead, status_code=201)
def create_user(user_in: UserCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # only admin can create users via this route
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    user = bank_service.create_user(session, email=user_in.email, password=user_in.password, name=user_in.name, last_name=user_in.last_name, phone=user_in.phone, role=user_in.role)
    return user


@router.get("/users")
def list_users(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # list users (debug)
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    from app.models.user import User as UserModel
    users = session.exec(select(UserModel)).all()
    return [
        {
            "user_id": u.user_id,
            "email": u.email,
            "name": u.name,
            "last_name": u.last_name,
            "phone": u.phone,
            "is_active": u.is_active,
            "role": u.role,
            "creation_date": u.creation_date,
            "last_login": u.last_login
        }
        for u in users
    ]


@router.get("/users/{user_id}", response_model=UserRead)
def read_user(user_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    if current_user.user_id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    return bank_service.get_user(session, user_id)


@router.patch("/users/{user_id}", response_model=UserRead)
def patch_user(user_id: int, user_in: UserUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # partial update user
    if current_user.user_id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    updated = bank_service.update_user(session, user_id, **user_in.dict(exclude_unset=True))
    return updated


@router.post("/users/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(user_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # deactivate user
    if current_user.user_id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    return bank_service.deactivate_user(session, user_id)


@router.post("/users/{user_id}/last_login", response_model=UserRead)
def set_last_login(user_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # update last_login to now
    if current_user.user_id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    return bank_service.set_last_login(session, user_id)
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
    # create secondary account
    
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
    # close account
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
    # archive closed account
    result = bank_service.archive_account(session, account_number, reason)
    return result


@router.get("/transactions/{user_account_number}/{transaction_id}")
def get_transaction_detail(
    user_account_number: str = Path(..., description="Numéro du compte de l'utilisateur impliqué"),
    transaction_id: int = Path(..., description="ID de la transaction à consulter"),
    session: Session = Depends(get_session)
):
    # get transaction details if user involved

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
    # full user info
    return bank_service.get_user_full_info(session, user_id)

# ============================================================
# Enregistrer un nouvel utilisateur avec un compte bancaire principal
# ============================================================

@router.post("/users/register", response_model=UserRegisterResponse)
def register_user(payload: UserRegisterRequest,session: Session = Depends(get_session)):
    # register new user with primary account
    
    # Use the service to create user + primary account
    result = bank_service.register_user(session, payload.email, payload.password)
    created_user = result["user"]
    primary_account_number = result["primary_account_number"]

    return UserRegisterResponse(
        id=created_user.user_id,
        email=created_user.email,
        primary_account_number=primary_account_number,
    )

# ============================================================
# Authentifier un utilisateur
# ============================================================
@router.post("/users/login", response_model=UserLoginResponse)
def login_user(payload: UserLoginRequest, session: Session = Depends(get_session)):
    # authenticate user and return token
    
    # Recherchez l'utilisateur par email
    db_user = session.exec(select(User).where(User.email == payload.email)).first()
    if not db_user or not db_user.verify_password(payload.password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    # Créez un token JWT
    access_token = create_access_token(db_user)  # type: ignore

    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=db_user.user_id,
        email=db_user.email,
    )
    
# ============================================================
# Récupérer les informations de l'utilisateur courant via le token JWT
# ============================================================
@router.get("/users/me")
def read_current_user(current_user: dict = Depends(get_current_user)):
    # return current user info from token
    return current_user


@router.get("/users/me/accounts")
def read_my_accounts(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # return list of current user's accounts (number + balance) sorted by creation date desc
    accounts = bank_service.get_user_accounts(session, current_user.user_id)
    return accounts


# parameterized route must come AFTER the static /users/me routes to avoid collision
@router.get("/users/{user_id}/accounts")
def get_user_accounts(user_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # list accounts for a user; only the user or admin
    if current_user.user_id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    return bank_service.get_user_accounts(session, user_id)

