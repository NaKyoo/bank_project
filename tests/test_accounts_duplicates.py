"""
Test pour vérifier qu'il n'y a pas de comptes en double dans la base de données.

Ce test vérifie :
1. Que la base de données ne contient que 3 comptes uniques
2. Que l'API /users/me/accounts retourne 3 comptes uniques
3. Qu'il n'y a pas de doublons de COMPTE_JOINT ou COMPTE_EPARGNE
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session, select
from app.main import app
from app import main
from app.models.account import BankAccount
from app.models.user import User

# Configuration d'une base de données en mémoire pour les tests
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False}
)

# Remplace le moteur de base de données de l'application par celui de test
main.engine = test_engine

# Crée toutes les tables nécessaires dans la base de données de test
SQLModel.metadata.create_all(test_engine)

client = TestClient(app)


def test_no_duplicate_accounts_in_database():
    """
    Test 1: Vérifie qu'il n'y a pas de comptes en double dans la base de données.
    """
    with Session(test_engine) as session:
        # Récupère tous les comptes
        accounts = session.exec(select(BankAccount)).all()
        
        # Vérifie le nombre total de comptes
        assert len(accounts) == 3, f"Attendu 3 comptes, trouvé {len(accounts)}"
        
        # Vérifie qu'il n'y a pas de doublons
        account_numbers = [acc.account_number for acc in accounts]
        unique_account_numbers = set(account_numbers)
        
        assert len(account_numbers) == len(unique_account_numbers), \
            f"Doublons détectés ! Comptes: {account_numbers}"
        
        # Vérifie que les 3 comptes attendus sont présents
        expected_accounts = {"COMPTE_COURANT", "COMPTE_EPARGNE", "COMPTE_JOINT"}
        assert unique_account_numbers == expected_accounts, \
            f"Comptes attendus: {expected_accounts}, trouvés: {unique_account_numbers}"


def test_api_returns_unique_accounts():
    """
    Test 2: Vérifie que l'API /users/me/accounts retourne des comptes uniques.
    """
    # Connexion avec l'utilisateur de test
    login_response = client.post(
        "/users/login",
        json={"email": "Eric123@gmail.com", "password": "Eric123!"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Récupère les comptes via l'API
    response = client.get(
        "/users/me/accounts",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    accounts = response.json()
    
    # Vérifie le nombre de comptes retournés
    assert len(accounts) == 3, f"L'API devrait retourner 3 comptes, mais retourne {len(accounts)}"
    
    # Vérifie qu'il n'y a pas de doublons
    account_numbers = [acc["account_number"] for acc in accounts]
    unique_account_numbers = set(account_numbers)
    
    assert len(account_numbers) == len(unique_account_numbers), \
        f"L'API retourne des doublons ! Comptes: {account_numbers}"
    
    # Affiche les comptes pour debug
    print(f"\n✅ Comptes retournés par l'API: {account_numbers}")


def test_each_account_appears_once():
    """
    Test 3: Vérifie que chaque compte (COURANT, EPARGNE, JOINT) n'apparaît qu'une seule fois.
    """
    with Session(test_engine) as session:
        # Compte le nombre d'occurrences de chaque type de compte
        compte_courant_count = session.exec(
            select(BankAccount).where(BankAccount.account_number == "COMPTE_COURANT")
        ).all()
        
        compte_epargne_count = session.exec(
            select(BankAccount).where(BankAccount.account_number == "COMPTE_EPARGNE")
        ).all()
        
        compte_joint_count = session.exec(
            select(BankAccount).where(BankAccount.account_number == "COMPTE_JOINT")
        ).all()
        
        # Vérifie qu'il n'y a qu'une seule occurrence de chaque
        assert len(compte_courant_count) == 1, \
            f"COMPTE_COURANT devrait apparaître 1 fois, trouvé {len(compte_courant_count)} fois"
        
        assert len(compte_epargne_count) == 1, \
            f"COMPTE_EPARGNE devrait apparaître 1 fois, trouvé {len(compte_epargne_count)} fois"
        
        assert len(compte_joint_count) == 1, \
            f"COMPTE_JOINT devrait apparaître 1 fois, trouvé {len(compte_joint_count)} fois"
        
        print(f"\n✅ Tous les comptes sont uniques:")
        print(f"   - COMPTE_COURANT: {len(compte_courant_count)} occurrence")
        print(f"   - COMPTE_EPARGNE: {len(compte_epargne_count)} occurrence")
        print(f"   - COMPTE_JOINT: {len(compte_joint_count)} occurrence")
