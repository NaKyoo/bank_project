from decimal import Decimal
from fastapi import HTTPException
from datetime import datetime


class BankAccount:
    def __init__(self, account_number: str, balance: Decimal = Decimal('0')):
        self.account_number = account_number
        self.balance = balance


class BankService:
    def __init__(self):
        # Simulation de base de données avec quelques comptes
        self.accounts = {
            "COMPTE_EPARGNE": BankAccount("COMPTE_EPARGNE", Decimal('150')),
            "COMPTE_COURANT": BankAccount("COMPTE_COURANT", Decimal('150')),
            "COMPTE_JOINT": BankAccount("COMPTE_JOINT", Decimal('150'))
        }

    def get_account(self, account_number: str) -> BankAccount:
        """Retourne un compte existant ou lève une exception si non trouvé."""
        account = self.accounts.get(account_number)
        if not account:
            raise HTTPException(
                status_code=404,
                detail=f"Compte '{account_number}' non trouvé."
            )
        return account

    def transfer_money(self, from_account: str, to_account: str, amount: Decimal):
        """Effectue un transfert d’argent avec validations métiers."""

        # Montant doit être positif
        if amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="Le montant du transfert doit être positif."
            )

        # Les deux comptes doivent exister
        source = self.get_account(from_account)
        destination = self.get_account(to_account)

        # Le compte destinataire doit être différent du compte source
        if from_account == to_account:
            raise HTTPException(
                status_code=400,
                detail="Le compte source et le compte destinataire doivent être différents."
            )

        # Le compte source doit avoir assez d’argent
        if source.balance < amount:
            raise HTTPException(
                status_code=400,
                detail=f"Solde insuffisant sur le compte {from_account}."
            )

        # Mise à jour des soldes
        source.balance -= amount
        destination.balance += amount

        # Retourne un résumé de la transaction
        return {
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
            "source_balance": source.balance,
            "destination_balance": destination.balance,
            "date": datetime.now()
        }


# Instance unique du service
bank_service = BankService()
