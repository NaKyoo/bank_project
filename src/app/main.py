from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import Session, select, SQLModel, create_engine


from app.controllers import bank_controller
from app.models.account import BankAccount
from app.models.user import User

engine = create_engine("sqlite:///bank.db")

# ------------------------------
# Définition du cycle de vie (lifespan) de l’application
# ------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Fonction exécutée automatiquement au démarrage (startup)
    et à l’arrêt (shutdown) de l’application FastAPI.
    Elle permet d’initialiser la base de données et d’ajouter des données de test.
    """

    # ---- Startup ----
    # Création automatique des tables définies dans les modèles SQLModel (si elles n’existent pas)
    SQLModel.metadata.create_all(engine)

    # Ouverture d’une session temporaire pour insérer des comptes de démonstration
    with Session(engine) as session:
        # create a demo user if it does not exist; use model helper to hash password
        if not session.exec(select(User).where(User.email == "Eric123@gmail.com")).first():
            user = User(email="Eric123@gmail.com", is_active=True)
            user.set_password("Eric123!")
            session.add(user)
            session.commit()
            session.refresh(user)
        # Si aucun compte n’existe encore dans la base...
        if not session.exec(select(BankAccount)).first():
            # Création des comptes bancaires de base
            compte_courant = BankAccount(
                account_number="COMPTE_COURANT",
                balance=150,
                parent_account_number=None,  # Compte principal
                user_id=user.user_id
            )

            comptes_secondaires = [
                BankAccount(
                    account_number="COMPTE_EPARGNE",
                    balance=150,
                    parent_account_number="COMPTE_COURANT",  # Rattaché au compte courant
                    user_id=user.user_id
                ),
                BankAccount(
                    account_number="COMPTE_JOINT",
                    balance=150,
                    parent_account_number="COMPTE_COURANT",  # Rattaché au compte courant
                    user_id=user.user_id
                ),
            ]

            # On ajoute tous les comptes dans la session
            session.add(compte_courant)
            session.add_all(comptes_secondaires)
            session.commit()
            
            session.refresh(user)
            

    # Le code suivant (après yield) s’exécutera à la fermeture de l’application.
    yield

    # ---- Shutdown ----
    # Ici, on pourrait libérer des ressources (fermer connexions, logs, etc.)
    # Aucun nettoyage spécifique n’est nécessaire dans ce cas.


# ------------------------------
# Création de l’application FastAPI
# ------------------------------
app = FastAPI(
    title="Bank Project API",
    lifespan=lifespan             # Cycle de vie défini plus haut
)

# Inclusion du routeur principal (défini dans bank_controller)
app.include_router(bank_controller.router)