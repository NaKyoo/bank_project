"""
Module principal de l'application Bank Project API.

Ce module configure et initialise l'application FastAPI avec :
- Configuration de la base de données SQLite
- Gestion du cycle de vie (lifespan) de l'application
- Middleware CORS pour les requêtes cross-origin
- Inclusion des routes définies dans les contrôleurs

Attributes:
    engine: Moteur SQLAlchemy pour la connexion à la base de données SQLite

Example:
    Pour lancer l'application :
        $ uvicorn app.main:app --reload

Author:
    Bank Project Team
    
Version:
    1.0.0
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import Session, select, SQLModel, create_engine
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware

# Imports des modules de l'application
from .controllers import bank_controller
from .models.account import BankAccount
from .models.user import User

# Configuration de la base de données
# Utilise SQLite pour le stockage persistant des données
engine = create_engine("sqlite:///bank.db")


# ==============================================================================
# CYCLE DE VIE DE L'APPLICATION
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestionnaire du cycle de vie de l'application FastAPI.
    
    Cette fonction asynchrone gère les événements de démarrage et d'arrêt
    de l'application. Elle est exécutée automatiquement par FastAPI.
    
    Fonctionnalités au démarrage (startup) :
        - Création automatique des tables de la base de données
        - Initialisation d'un utilisateur de démonstration
        - Création de comptes bancaires de test
    
    Fonctionnalités à l'arrêt (shutdown) :
        - Libération des ressources (si nécessaire)
        - Fermeture des connexions (si nécessaire)
    
    Args:
        app (FastAPI): Instance de l'application FastAPI
        
    Yields:
        None: Contrôle rendu à l'application pendant son exécution
        
    Example:
        Cette fonction est utilisée automatiquement par FastAPI :
        >>> app = FastAPI(lifespan=lifespan)
        
    Note:
        Les données de test sont créées uniquement si la base est vide.
        Cela évite les doublons lors des redémarrages.
    """


    # ---- Startup ----
    # Création automatique des tables définies dans les modèles SQLModel (si elles n’existent pas)
    SQLModel.metadata.create_all(engine)

    # Ouverture d’une session temporaire pour insérer des comptes de démonstration
    with Session(engine) as session:
        
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

        if not session.exec(select(User).where(User.email == "Eric123@gmail.com")).first(): 
            
            hashed_password = pwd_context.hash("Eric123!")

            user = User(
                    email="Eric123@gmail.com",
                    hashed_password=hashed_password,
                    is_active=True
                )
            session.add(user)
            session.commit()
            session.refresh(user)
            
        # Si aucun compte n'existe encore dans la base pour cet utilisateur
        existing_accounts = session.exec(
            select(BankAccount).where(BankAccount.owner_id == user.id)
        ).all()
        
        if not existing_accounts:
            # Création des comptes bancaires de base
            compte_courant = BankAccount(
                account_number="COMPTE_COURANT",
                balance=150,
                parent_account_number=None,  # Compte principal
                owner_id=user.id   
            )

            comptes_secondaires = [
                BankAccount(
                    account_number="COMPTE_EPARGNE",
                    balance=150,
                    parent_account_number="COMPTE_COURANT",  # Rattaché au compte courant
                    owner_id=user.id   
                ),
                BankAccount(
                    account_number="COMPTE_JOINT",
                    balance=150,
                    parent_account_number="COMPTE_COURANT",  # Rattaché au compte courant
                    owner_id=user.id
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


# ==============================================================================
# CONFIGURATION DE L'APPLICATION FASTAPI
# ==============================================================================

app = FastAPI(
    title="Bank Project API",
    description="API REST pour la gestion de comptes bancaires avec authentification JWT",
    version="1.0.0",
    lifespan=lifespan,  # Gestionnaire du cycle de vie défini ci-dessus
    docs_url="/docs",   # Documentation Swagger UI
    redoc_url="/redoc"  # Documentation ReDoc
)

# ==============================================================================
# CONFIGURATION DU MIDDLEWARE CORS
# ==============================================================================
# Le middleware CORS (Cross-Origin Resource Sharing) permet aux applications
# frontend (React, Vue, etc.) de communiquer avec l'API depuis un domaine différent.

app.add_middleware(
    CORSMiddleware,
    # Origines autorisées à faire des requêtes vers l'API
    # En production, remplacer par les domaines réels (ex: https://monapp.com)
    allow_origins=[
        "http://localhost:5173",  # Vite (React/Vue en développement)
        "http://localhost:3000",  # Create React App
    ],
    # Permet l'envoi de cookies et headers d'authentification
    allow_credentials=True,
    # Méthodes HTTP autorisées (GET, POST, PUT, DELETE, etc.)
    allow_methods=["*"],
    # Headers personnalisés autorisés (Authorization, Content-Type, etc.)
    allow_headers=["*"]
)

# ==============================================================================
# INCLUSION DES ROUTES
# ==============================================================================
# Toutes les routes de l'API sont définies dans le module bank_controller
# et sont automatiquement préfixées et documentées par FastAPI
app.include_router(bank_controller.router)