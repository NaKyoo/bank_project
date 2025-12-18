"""
Module de configuration de la base de données.

Ce module fournit une fonction de dépendance FastAPI pour obtenir
une session de base de données SQLModel. Il est utilisé dans les routes
via l'injection de dépendances de FastAPI.

Functions:
    get_session: Générateur de session de base de données

Example:
    Utilisation dans une route FastAPI :
        >>> @router.get("/users")
        >>> def get_users(session: Session = Depends(get_session)):
        >>>     users = session.exec(select(User)).all()
        >>>     return users

Author:
    Bank Project Team
    
Version:
    1.0.0
"""

from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./bank.db"

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# ==============================================================================
# DÉPENDANCE FASTAPI - SESSION DE BASE DE DONNÉES
# ==============================================================================

def get_session():
    """
    Générateur de session de base de données pour FastAPI.
    
    Cette fonction est utilisée comme dépendance dans les routes FastAPI
    pour obtenir une session de base de données. La session est automatiquement
    fermée après l'exécution de la route grâce au mot-clé 'yield'.
    
    Yields:
        Session: Session SQLModel connectée à la base de données
        
    Example:
        Utilisation dans une route :
        >>> @router.post("/users")
        >>> def create_user(user: User, session: Session = Depends(get_session)):
        >>>     session.add(user)
        >>>     session.commit()
        >>>     return user
        
    Note:
        La session est automatiquement fermée après l'exécution de la route,
        même en cas d'exception. Cela garantit qu'aucune connexion ne reste ouverte.
    """
    # Création d'une nouvelle session de base de données
    with Session(engine) as session:
        # Rend la session disponible à la route FastAPI
        yield session
        # La session est automatiquement fermée après le 'yield'
        # grâce au context manager 'with'
