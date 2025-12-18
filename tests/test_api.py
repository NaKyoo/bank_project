"""
Module de tests unitaires pour l'API Bank Project.

Ce module contient les tests automatisés pour vérifier le bon fonctionnement
de l'API FastAPI. Il utilise pytest et TestClient pour simuler des requêtes HTTP.

Configuration:
    - Base de données en mémoire SQLite pour l'isolation des tests
    - TestClient FastAPI pour simuler les requêtes HTTP
    - Fixtures pytest pour la configuration de l'environnement de test

Example:
    Pour exécuter les tests :
        $ pytest tests/test_api.py -v
        $ pytest  # Pour tous les tests

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
# TESTS UNITAIRES
# ==============================================================================

def test_read_root():
    """
    Test de la route racine de l'API (/).
    
    Vérifie que :
        - Le code de statut HTTP est 200 (OK)
        - La réponse JSON contient le message attendu
    
    Returns:
        None: Le test passe si les assertions sont vérifiées
        
    Raises:
        AssertionError: Si la réponse ne correspond pas aux attentes
        
    Example:
        >>> response = client.get("/")
        >>> assert response.status_code == 200
        >>> assert response.json() == {"message": "Hello, FastAPI!"}
    """
    # Envoi d'une requête GET vers la route racine
    response = client.get("/")
    
    # Vérification du code de statut HTTP
    assert response.status_code == 200, "La route racine doit retourner un code 200"
    
    # Vérification du contenu de la réponse JSON
    assert response.json() == {"message": "Hello, FastAPI!"}, \
        "Le message de bienvenue doit être 'Hello, FastAPI!'"

