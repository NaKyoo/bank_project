from fastapi import FastAPI
from pydantic import BaseModel # bibliotèque permettant la validation de données

# app = FastAPI() # application ASGI --> pertme l'envoie de requette au serveur web suur python

class Item(BaseModel) :
    name : str
    description : str
    price : float 
    tax : float

"""
Instlation et dépendances utile à la story 1

python -m pip install --upgrade pip
python -m pip install "sqlmodel>=0.0.22" "sqlalchemy>=2.0"
python -m pip install fastapi pydantic uvicorn
python -m pip install "passlib[bcrypt]==1.7.4" "bcrypt==4.0.1"
python -m pip install pyjwt

"""