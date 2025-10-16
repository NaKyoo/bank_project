from datetime import datetime, timezone
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
    
    
    is_active: bool = Field(default=True)
    closed_at: Optional[datetime] = Field(default=None)
    

    # ==============================
    # Lien parent-enfant
    # ==============================
    
    parent_account_number: Optional[str] = Field(default=None, foreign_key="bankaccount.account_number")
    
    # Le parent (compte principal)
    parent_account: Optional["BankAccount"] = Relationship(
        back_populates="child_accounts",
        sa_relationship_kwargs={"remote_side": "[BankAccount.account_number]"}
    )

    # Les enfants (comptes secondaires)
    child_accounts: List["BankAccount"] = Relationship(
        back_populates="parent_account"
    )
    
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
    
    def open_account(self, parent_account: Optional["BankAccount"] = None, initial_balance: Decimal = 0):
        """Réactive ou crée un compte secondaire :
        - Le rend actif
        - Initialise le solde
        - Associe un parent si fourni"""
        if self.is_active:
            raise ValueError("Le compte est déjà actif.")

        self.is_active = True
        self.closed_at = None
        self.balance = initial_balance

        if parent_account:
            self.parent_account_number = parent_account.account_number
    
    
    def close_account(self):
        """Clôture le compte et transfère le solde au parent si nécessaire"""
        if not self.is_active:
            raise ValueError("Le compte est déjà clôturé.")
        
        # Interdire la clôture d'un parent s'il a des enfants actifs
        if self.child_accounts:
            active_children = [c for c in self.child_accounts if c.is_active]
            if active_children:
                raise ValueError("Impossible de clôturer un compte parent tant que des comptes secondaires sont actifs.")
        
        # Transfert du solde vers le parent si compte secondaire
        if self.balance > 0 and self.parent_account:
            self.transfer_to(self.parent_account, self.balance)

        self.is_active = False
        self.closed_at = datetime.now(timezone.utc)


    def archive(self) -> "ArchivedBankAccount":
        """
        Crée une archive complète du compte clôturé,
        incluant la référence au compte parent (si secondaire).
        """
        if self.is_active:
            raise ValueError("Impossible d’archiver un compte encore actif.")
        if not self.closed_at:
            raise ValueError("Le compte doit être clôturé avant archivage.")

        return ArchivedBankAccount(
            original_account_number=self.account_number,
            balance=self.balance,
            closed_at=self.closed_at,
            parent_account_number=self.parent_account_number,
            archived_at=datetime.now(timezone.utc)
        )


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
    
    
# ===============================
# Table d’archive des comptes
# ===============================
class ArchivedBankAccount(SQLModel, table=True):
    """Table séparée pour les comptes archivés."""
    id: Optional[int] = Field(default=None, primary_key=True)
    original_account_number: str = Field(index=True)
    balance: Decimal
    closed_at: datetime
    parent_account_number: Optional[str] = Field(default=None) 
    archived_at: datetime = Field(default_factory=datetime.now(timezone.utc)
)
