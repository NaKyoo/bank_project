from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

# ------------------------------
# Classe représentant un Bénéficiaire
# ------------------------------
class Beneficiary(SQLModel, table=True):
    """
    Cette classe représente un lien entre un compte propriétaire (owner)
    et un compte bénéficiaire (beneficiary), c’est-à-dire un compte vers lequel
    le propriétaire est autorisé à effectuer des transferts.
    """

    # Identifiant unique du bénéficiaire (clé primaire)
    id: Optional[int] = Field(default=None, primary_key=True)

    # Numéro du compte du propriétaire (clé étrangère vers BankAccount.account_number)
    owner_account_number: str = Field(foreign_key="bankaccount.account_number")

    # Numéro du compte du bénéficiaire (clé étrangère vers BankAccount.account_number)
    beneficiary_account_number: str = Field(foreign_key="bankaccount.account_number")

    # Relation vers le compte propriétaire
    owner: Optional["BankAccount"] = Relationship(   # type: ignore pour éviter une erreur d’import circulaire
        back_populates="beneficiaries",              # Lien vers l’attribut 'beneficiaries' dans la classe BankAccount
        sa_relationship_kwargs={                     # Paramètre SQLAlchemy : précise quelle clé étrangère utiliser
            "foreign_keys": "[Beneficiary.owner_account_number]"
        }
    )