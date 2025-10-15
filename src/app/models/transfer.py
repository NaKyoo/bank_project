from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime

# ------------------------------
# Classe représentant une requête de transfert (entrée utilisateur)
# ------------------------------
class TransferRequest(BaseModel):
    """
    Ce modèle définit la structure des données attendues lorsqu’un utilisateur
    demande un transfert d’argent entre deux comptes.
    """

    # Numéro du compte source (obligatoire)
    from_account: str = Field(
        ...,  # Les trois points (...) signifient que le champ est requis
        description="Numéro du compte source"
    )

    # Numéro du compte destinataire (obligatoire)
    to_account: str = Field(
        ...,
        description="Numéro du compte destinataire"
    )

    # Montant à transférer (obligatoire et doit être supérieur à 0)
    amount: Decimal = Field(
        ...,                  # Champ requis
        gt=0,                 # Validation : le montant doit être strictement supérieur à 0
        description="Montant à transférer (doit être positif)"
    )


# ------------------------------
# Classe représentant un transfert effectué (réponse ou enregistrement)
# ------------------------------
class Transfer(BaseModel):
    """
    Ce modèle représente une opération de transfert enregistrée
    après validation ou exécution. Il peut être retourné comme réponse API
    ou enregistré dans un historique.
    """

    # Date et heure du transfert (valeur par défaut : maintenant)
    date: datetime = Field(
        default_factory=datetime.now,
        description="Date et heure du transfert"
    )

    # Numéro du compte source
    from_account: str

    # Numéro du compte destinataire
    to_account: str

    # Montant transféré
    amount: Decimal

    # Statut du transfert (par défaut : "completed")
    status: str = "completed"