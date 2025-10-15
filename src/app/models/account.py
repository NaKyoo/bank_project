from datetime import datetime           
from decimal import Decimal
from typing import List, Optional  

from sqlmodel import Field, Relationship, SQLModel


# ------------------------------
# Classe représentant une Transaction
# ------------------------------
class Transaction(SQLModel, table=True):
    # Identifiant unique de la transaction (clé primaire)
    id: Optional[int] = Field(default=None, primary_key=True)

    # Type de transaction (exemples : "deposit", "transfer", etc.)
    transaction_type: str

    # Montant de la transaction (en Decimal pour éviter les erreurs d’arrondi)
    amount: Decimal

    # Numéro du compte source (clé étrangère vers la table BankAccount)
    source_account_number: Optional[str] = Field(default=None, foreign_key="bankaccount.account_number")

    # Numéro du compte destinataire (clé étrangère vers la table BankAccount)
    destination_account_number: Optional[str] = Field(default=None, foreign_key="bankaccount.account_number")

    # Date et heure de la transaction (valeur par défaut : maintenant)
    date: datetime = Field(default_factory=datetime.now)

    # Relation vers le compte source (le compte qui envoie l'argent)
    source_account: Optional["BankAccount"] = Relationship(
        back_populates="transactions",  # Nom du champ correspondant dans BankAccount
        sa_relationship_kwargs={"foreign_keys": "[Transaction.source_account_number]"}  # Spécifie la clé étrangère
    )

    # Relation vers le compte destinataire (le compte qui reçoit l'argent)
    destination_account: Optional["BankAccount"] = Relationship(
        back_populates="incoming_transactions",  # Nom du champ correspondant dans BankAccount
        sa_relationship_kwargs={"foreign_keys": "[Transaction.destination_account_number]"}
    )


# ------------------------------
# Classe représentant un Compte Bancaire
# ------------------------------
class BankAccount(SQLModel, table=True):
    # Numéro de compte unique (clé primaire)
    account_number: str = Field(primary_key=True)

    # Solde du compte (par défaut à 0)
    balance: Decimal = Field(default=Decimal("0"))

    # ------------------------------
    # Relations avec d'autres tables
    # ------------------------------

    # Liste des transactions où ce compte est la source (sortantes)
    transactions: List[Transaction] = Relationship(
        back_populates="source_account",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.source_account_number]"}
    )

    # Liste des transactions où ce compte est la destination (entrantes)
    incoming_transactions: List[Transaction] = Relationship(
        back_populates="destination_account",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.destination_account_number]"}
    )

    # Liste des bénéficiaires associés à ce compte
    beneficiaries: List["Beneficiary"] = Relationship(  # type: ignore pour éviter une erreur d'import circulaire
        back_populates="owner",
        sa_relationship_kwargs={"foreign_keys": "[Beneficiary.owner_account_number]"}
    )

    # ------------------------------
    # Méthodes métier (logique applicative)
    # ------------------------------

    # Effectuer un dépôt sur le compte
    def deposit(self, amount: Decimal) -> Transaction:
        # Vérifie que le montant est positif
        if amount <= 0:
            raise ValueError("Le montant du dépôt doit être positif")
        
        # Vérifie que le montant ne dépasse pas 2000 €
        if amount > Decimal('2000'):
            raise ValueError("Le dépôt ne peut pas dépasser 2000 € par opération")

        # Ajoute le montant au solde actuel
        self.balance += amount

        # Crée et retourne un objet Transaction représentant le dépôt
        return Transaction(
            transaction_type="deposit",
            amount=amount,
            destination_account_number=self.account_number
        )

    # Effectuer un transfert vers un autre compte
    def transfer_to(self, target: "BankAccount", amount: Decimal) -> Transaction:
        # Vérifie que le montant est valide
        if amount <= 0:
            raise ValueError("Le montant du transfert doit être positif")

        # Vérifie que le solde est suffisant
        if self.balance < amount:
            raise ValueError("Solde insuffisant")

        # Empêche de transférer vers soi-même
        if self.account_number == target.account_number:
            raise ValueError("Impossible de transférer vers soi-même")

        # Déduit le montant du solde du compte source
        self.balance -= amount

        # Ajoute le montant au solde du compte destinataire
        target.balance += amount

        # Crée et retourne un objet Transaction représentant le transfert
        return Transaction(
            transaction_type="transfer",
            amount=amount,
            source_account_number=self.account_number,
            destination_account_number=target.account_number
        )

    # Ajouter un compte bénéficiaire (autre compte autorisé à recevoir des transferts)
    def add_beneficiary(self, beneficiary_account: "BankAccount") -> "Beneficiary":  # type: ignore
        from app.models.beneficiary import Beneficiary  # Import retardé pour éviter une boucle d'importation

        # Vérifie que le bénéficiaire n'est pas le compte lui-même
        if beneficiary_account.account_number == self.account_number:
            raise ValueError("Impossible d'ajouter soi-même comme bénéficiaire")

        # Vérifie si le bénéficiaire existe déjà
        existing = [b.beneficiary_account_number for b in self.beneficiaries]
        if beneficiary_account.account_number in existing:
            raise ValueError("Ce compte est déjà un bénéficiaire")

        # Crée un nouvel objet Beneficiary liant les deux comptes
        new_beneficiary = Beneficiary(
            owner_account_number=self.account_number,
            beneficiary_account_number=beneficiary_account.account_number
        )

        # Ajoute ce bénéficiaire à la liste des bénéficiaires du compte
        self.beneficiaries.append(new_beneficiary)

        # Retourne le nouvel objet créé
        return new_beneficiary
