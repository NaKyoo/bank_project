from contextlib import asynccontextmanager         
from fastapi import FastAPI                        
import uvicorn                                     
from sqlmodel import Session, select, SQLModel, create_engine  
from app.controllers import bank_controller        
from app.models.account import BankAccount         

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
        # Si aucun compte n’existe encore dans la base...
        if not session.exec(select(BankAccount)).first():
            # ... alors on crée quelques comptes bancaires de base
            comptes = [
                BankAccount(account_number="COMPTE_EPARGNE", balance=150),
                BankAccount(account_number="COMPTE_COURANT", balance=150),
                BankAccount(account_number="COMPTE_JOINT", balance=150),
            ]
            # On ajoute les comptes dans la session et on enregistre en base
            session.add_all(comptes)
            session.commit()

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

