"""
Tests unitaires pour la route racine de l'API FastAPI.
Ce fichier teste que la route "/" retourne bien le message attendu.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from app.main import app
from app import main

# Configuration d'une base de données en mémoire pour les tests
# Cela permet d'isoler les tests et d'éviter d'affecter la base de données de production
test_engine = create_engine(
    "sqlite:///:memory:", 
    connect_args={"check_same_thread": False}
)

# Remplace le moteur de base de données de l'application par celui de test
main.engine = test_engine

# Crée toutes les tables nécessaires dans la base de données de test
SQLModel.metadata.create_all(test_engine)

# Initialise le client de test FastAPI
client = TestClient(app)


def test_read_root():
    """
    Test de la route racine (/).
    
    Vérifie que :
    - Le code de statut HTTP est 200 (OK)
    - La réponse JSON contient le message attendu : {"message": "Hello, FastAPI!"}
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, FastAPI!"}
