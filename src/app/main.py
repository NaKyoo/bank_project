from fastapi import FastAPI
import uvicorn


app = FastAPI(title="Bank Project API")


@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)