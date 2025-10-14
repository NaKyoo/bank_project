from decimal import Decimal
from typing import Dict
from fastapi import HTTPException
from datetime import datetime

from app.models.beneficiary import Beneficiary


class BankAccount:
    def __init__(self, account_number: str, balance: Decimal = Decimal('0')):
        self.account_number = account_number
        self.balance = balance


class BankService:
    def __init__(self):
        # Simulation d'une base de comptes
        self.accounts = {
            "COMPTE_EPARGNE": BankAccount("COMPTE_EPARGNE", Decimal('150')),
            "COMPTE_COURANT": BankAccount("COMPTE_COURANT", Decimal('150')),
            "COMPTE_JOINT": BankAccount("COMPTE_JOINT", Decimal('150'))
        }
        # Mapping des comptes vers leurs bénéficiaires
        self.beneficiaries: Dict[str, Dict[str, Beneficiary]] = {
            account: {} for account in self.accounts
        }


    ######################################
    ############# COMPTES ################
    ######################################
    def get_account(self, account_number: str) -> BankAccount:
        account = self.accounts.get(account_number)
        if not account:
            raise HTTPException(status_code=404, detail=f"Compte '{account_number}' non trouvé.")
        return account


    def get_account_info(self, account_number: str) -> Dict:
        """Retourne les informations d’un compte (solde, bénéficiaires, etc.)"""
        account = self.get_account(account_number)  # lève 404 si non trouvé

        beneficiary_list = []
        if account_number in self.beneficiaries:
            beneficiary_list = [
                {"name": b.name, "account_number": b.account_number}
                for b in self.beneficiaries[account_number].values()
            ]

        return {
            "account_number": account.account_number,
            "balance": account.balance,
            "beneficiaries": beneficiary_list,
        }


    ######################################
    ############# TRANSFERTS ################
    ######################################
    def transfer_money(self, from_account: str, to_account: str, amount: Decimal):
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Le montant du transfert doit être positif.")

        source = self.get_account(from_account)
        destination = self.get_account(to_account)

        if from_account == to_account:
            raise HTTPException(status_code=400, detail="Le compte source et le compte destinataire doivent être différents.")

        if source.balance < amount:
            raise HTTPException(status_code=400, detail=f"Solde insuffisant sur le compte {from_account}.")

        source.balance -= amount
        destination.balance += amount

        return {
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
            "source_balance": source.balance,
            "destination_balance": destination.balance,
            "date": datetime.now()
        }


    ######################################
    ############# DEPOT ################
    ######################################
    def deposit_money(self, account_number: str, amount: Decimal):
        """Ajoute de l’argent sur un compte (dépôt)."""
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Le montant du dépôt doit être positif.")

        account = self.get_account(account_number)
        account.balance += amount

        return {
            "account_number": account.account_number,
            "amount_deposited": amount,
            "new_balance": account.balance,
            "date": datetime.now()
        }
        
        
        
    ######################################
    ############# BENEFICIAIRES ################
    ######################################
    def add_beneficiary(self, owner_account: str, name: str, account_number: str):
        """Ajoute un bénéficiaire avec validations métier strictes"""

        owner = self.get_account(owner_account)

        # Le nom du bénéficiaire doit être renseigné
        if not name.strip():
            raise HTTPException(status_code=400, detail="Le nom du bénéficiaire doit être renseigné.")

        # Le bénéficiaire ne peut pas être un des comptes de l’utilisateur
        if account_number == owner_account:
            raise HTTPException(status_code=400, detail="Impossible d'ajouter soi-même comme bénéficiaire.")

        # Le bénéficiaire doit exister
        if account_number not in self.accounts:
            raise HTTPException(status_code=404, detail=f"Le compte bénéficiaire {account_number} n'existe pas.")

        # Le bénéficiaire ne peut pas être ajouté plusieurs fois (même nom)
        if name in self.beneficiaries[owner_account]:
            raise HTTPException(status_code=400, detail=f"Un bénéficiaire avec le nom '{name}' existe déjà.")

        # Ajout du bénéficiaire
        self.beneficiaries[owner_account][name] = Beneficiary(name, account_number)
        return {
            "owner_account": owner_account,
            "beneficiary_name": name,
            "beneficiary_account": account_number
        }
        
        
    def get_beneficiaries(self, owner_account: str):
        """Retourne la liste des bénéficiaires pour un compte"""
        owner = self.get_account(owner_account)
        return [
            {"name": b.name, "account_number": b.account_number}
            for b in self.beneficiaries[owner_account].values()
        ]


# Instance unique du service
bank_service = BankService()
