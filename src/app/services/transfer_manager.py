#################################################
# PERMET DE SUPPRIMER LES BOUCLES D'IMPORTATION #
#################################################

# app/services/transfer_manager.py
from typing import Dict
from app.models.transfer import Transfer

transfers_in_progress: Dict[int, Transfer] = {}

transfer_counter = 0
