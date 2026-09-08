from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.db.database import engine


app = FastAPI(title=settings.app_name)


@app.get("/")
def root():
    return {"message": settings.app_name}


@app.get("/health")
def health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"status": "ok"}