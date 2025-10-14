from fastapi import FastAPI
import uvicorn
from app.controllers import bank_controller

app = FastAPI(title="Bank Project API")
app.include_router(bank_controller.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)