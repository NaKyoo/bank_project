
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from app.main import app
from app import main

# Setup in-memory database for testing
test_engine = create_engine(
    "sqlite:///:memory:", 
    connect_args={"check_same_thread": False}
)

# Patch the engine in the application
main.engine = test_engine

# Create tables in the test database
SQLModel.metadata.create_all(test_engine)

client = TestClient(app)

def test_read_root():
    """
    Test simple pour vérifier que l'API démarre et répond sur la racine.
    """
    response = client.get("/")
    assert response.status_code == 200
    # Test corrigé pour vérifier le bon fonctionnement du CI/CD
    assert response.json() == {"message": "Hello, FastAPI!"}

