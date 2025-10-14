import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

from ..models.transfer import TransferRequest, Transfer


def test_valid_transfer_request():
    """Test de création d'une requête de transfert valide"""
    data = {
        "from_account": "FR123456789",
        "to_account": "FR987654321",
        "amount": Decimal("150.75")
    }
    req = TransferRequest(**data)
    assert req.from_account == "FR123456789"
    assert req.to_account == "FR987654321"
    assert req.amount == Decimal("150.75")


def test_transfer_request_negative_amount():
    """Test que le montant négatif déclenche une erreur"""
    with pytest.raises(ValidationError):
        TransferRequest(
            from_account="FR111111111",
            to_account="FR222222222",
            amount=Decimal("-10.00")
        )


def test_transfer_request_missing_field():
    """Test qu'un champ manquant déclenche une erreur"""
    with pytest.raises(ValidationError):
        TransferRequest(
            from_account="FR111111111",
            amount=Decimal("50.00")
        )


def test_transfer_creation_defaults():
    """Test la création d'un transfert avec valeurs par défaut"""
    transfer = Transfer(
        from_account="FR123",
        to_account="FR456",
        amount=Decimal("200.00")
    )
    assert transfer.from_account == "FR123"
    assert transfer.to_account == "FR456"
    assert transfer.amount == Decimal("200.00")
    assert transfer.status == "completed"
    assert isinstance(transfer.date, datetime)
    # Vérifie que la date est proche de maintenant (moins de 2 secondes d'écart)
    assert abs((datetime.now() - transfer.date).total_seconds()) < 2


def test_transfer_custom_date_and_status():
    """Test qu'on peut surcharger la date et le statut"""
    custom_date = datetime(2024, 1, 1, 12, 0, 0)
    transfer = Transfer(
        date=custom_date,
        from_account="FR111",
        to_account="FR222",
        amount=Decimal("500.00"),
        status="pending"
    )
    assert transfer.date == custom_date
    assert transfer.status == "pending"
