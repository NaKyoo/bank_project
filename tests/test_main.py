"""
Module de tests unitaires pour la route racine de l'API.

Ce module contient les tests spécifiques pour vérifier le bon fonctionnement
de la route racine ("/") de l'API FastAPI.

Tests inclus:
    - test_read_root: Vérifie que la route racine retourne le message attendu

Configuration:
    - Base de données en mémoire SQLite pour l'isolation
    - TestClient FastAPI pour les requêtes HTTP simulées

Example:
    Pour exécuter ce test spécifique :
        $ pytest tests/test_main.py -v
        $ pytest tests/test_main.py::test_read_root

Author:
    Bank Project Team
    
Version:
    1.0.0
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from app.main import app
from app import main

# ==============================================================================
# CONFIGURATION DE L'ENVIRONNEMENT DE TEST
# ==============================================================================

# Configuration d'une base de données en mémoire pour les tests
# Cela permet d'isoler les tests et d'éviter d'affecter la base de données de production
test_engine = create_engine(
    "sqlite:///:memory:",  # Base de données SQLite en mémoire (volatile)
    connect_args={"check_same_thread": False}  # Nécessaire pour SQLite avec FastAPI
)

# Remplacement du moteur de base de données de l'application par celui de test
# Cela garantit que tous les tests utilisent la base de données en mémoire
main.engine = test_engine

# Création de toutes les tables définies dans les modèles SQLModel
# Les tables sont créées dans la base de données en mémoire avant chaque test
SQLModel.metadata.create_all(test_engine)

# Initialisation du client de test FastAPI
# Ce client permet de simuler des requêtes HTTP vers l'API
client = TestClient(app)


# ==============================================================================
# TESTS UNITAIRES - ROUTE RACINE
# ==============================================================================

def test_read_root():
    """
    Test de la route racine de l'API (/).
    
    Ce test vérifie que la route racine de l'API répond correctement
    avec le message de bienvenue attendu.
    
    Vérifie que :
        - Le code de statut HTTP est 200 (OK)
        - La réponse JSON contient {"message": "Hello, FastAPI!"}
    
    Returns:
        None: Le test passe si toutes les assertions sont vérifiées
        
    Raises:
        AssertionError: Si la réponse ne correspond pas aux attentes
        
    Example:
        >>> response = client.get("/")
        >>> assert response.status_code == 200
        >>> assert response.json() == {"message": "Hello, FastAPI!"}
        
    Note:
        Ce test est utilisé par le workflow CI/CD pour vérifier
        le bon fonctionnement de l'API après chaque push.
    """
    # Envoi d'une requête GET vers la route racine
    response = client.get("/")
    
    # Vérification du code de statut HTTP
    assert response.status_code == 200, \
        "La route racine doit retourner un code HTTP 200 (OK)"
    
    # Vérification du contenu de la réponse JSON
    assert response.json() == {"message": "Hello, FastAPI!"}, \
        "Le message de bienvenue doit être exactement 'Hello, FastAPI!'"

