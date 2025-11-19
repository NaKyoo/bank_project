from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional  

from enum import Enum
from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel



class TransactionStatus(str, Enum):
    """
    Enumération représentant les différents états possibles d'une transaction.
    
    Attributes:
        PENDING (str): La transaction a été créée mais n'a pas encore été exécutée.
        COMPLETED (str): La transaction a été exécutée avec succès.
        CANCELED (str): La transaction a été annulée et n'a pas été effectuée.
    """
    
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELED = "canceled"

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

    # Statut actuel de la transaction
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)


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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    owner: Optional["User"] = Relationship( # type: ignore
        back_populates="bank_accounts",
        sa_relationship_kwargs={"foreign_keys": "[BankAccount.owner_id]"}
    )

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
        sa_relationship_kwargs={"foreign_keys": "[Transaction.source_account_number]", "cascade": "all, delete-orphan"}
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
        """Ouvre un nouveau compte secondaire :
        - Initialise le solde (>=0)
        - Associe le compte principal comme parent obligatoire
        - Vérifie que le compte n'est pas déjà actif"""
           
        if self.is_active:
            raise ValueError("Le compte est déjà actif.")
        
        if initial_balance < 0:
            raise ValueError("Le solde initial ne peut pas être négatif.")
        
        if parent_account is None or parent_account.parent_account_number is not None:
            # Si le parent est absent ou n'est pas un compte principal
            raise ValueError("Le compte parent doit être un compte principal existant.")

        self.is_active = True
        self.closed_at = None
        self.balance = initial_balance
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
            
        # Vérifie s'il existe des transactions PENDING dans les transactions liées à ce compte
        pending_transactions = [
            t for t in self.transactions + self.incoming_transactions
            if t.status == TransactionStatus.PENDING
        ]
        if pending_transactions:
            raise ValueError("Impossible de clôturer le compte : des transactions sont encore en cours.")

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
            destination_account_number=self.account_number,
            status=TransactionStatus.COMPLETED 
        )

    # ------------------------------
    # Effectuer un transfert vers un autre compte
    # ------------------------------
    def transfer_to(self, target: "BankAccount", amount: Decimal) -> Transaction:
        """
        Crée une transaction de type 'transfer' PENDING vers un autre compte.
        
        Args:
            target (BankAccount): Le compte destinataire.
            amount (Decimal): Le montant du transfert.
        
        Returns:
            Transaction: La transaction créée avec status PENDING.
        
        Raises:
            ValueError: Si le montant est négatif, si le compte cible est le même,
                        ou si le solde est insuffisant.
        """
        
        if amount <= 0:
            raise ValueError("Le montant du transfert doit être positif")
        if self.account_number == target.account_number:
            raise ValueError("Impossible de transférer vers soi-même")
        if self.balance < amount:
            raise ValueError("Solde insuffisant")

        # Crée la transaction PENDING
        transaction = Transaction(
            transaction_type="transfer",
            amount=amount,
            source_account_number=self.account_number,
            destination_account_number=target.account_number,
            status=TransactionStatus.PENDING
        )
        return transaction
      
    # ------------------------------
    # Répartir un transfert sur plusieurs comptes sans limitation pour le compte principal
    # ------------------------------
    def complete_transfer(self, targets: list["BankAccount"], transaction: Transaction):
        """
        Répartit le montant d'une transaction PENDING sur plusieurs comptes.
        Les comptes secondaires ont un plafond de 50 000€.
        Le compte principal (parent_account_number=None) est illimité.
        """
        SECONDARY_ACCOUNT_MAX = Decimal("50000")

        if transaction.status != TransactionStatus.PENDING:
            raise ValueError("Transaction déjà complétée ou annulée")
        
        
        remaining_amount = transaction.amount
        self.balance -= transaction.amount

        # Répartition sur les comptes secondaires
        for target in targets:
            if remaining_amount <= 0:
                break

            if target.parent_account_number is not None:  # compte secondaire
                available_space = SECONDARY_ACCOUNT_MAX - target.balance
                if available_space <= 0:
                    continue
                to_transfer = min(remaining_amount, available_space)
            else:  # compte principal illimité
                to_transfer = remaining_amount

            target.balance += to_transfer
            remaining_amount -= to_transfer

        transaction.status = TransactionStatus.COMPLETED
        
    # ------------------------------
    # Annuler un transfert
    # ------------------------------
    def cancel_transfer(self, transaction: Transaction):
        """
        Annule une transaction PENDING. Logique métier pure (ne touche pas à la base de données).

        Args:
            transaction (Transaction): La transaction à annuler.

        Returns:
            Transaction: La transaction avec status mis à CANCELED.

        Raises:
            ValueError: Si la transaction n'est pas PENDING.
        """
        
        if transaction.status != TransactionStatus.PENDING:
            raise ValueError("Transaction déjà complétée ou annulée")
        transaction.status = TransactionStatus.CANCELED
        return transaction

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