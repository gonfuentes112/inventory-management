from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.db.database import engine

from app.api.products import router as product_router
from app.api.category import router as category_router

from app import models

app = FastAPI(title=settings.app_name)

app.include_router(product_router)
app.include_router(category_router)


@app.get("/")
def root():
    return {"message": settings.app_name}


@app.get("/health")
def health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"status": "ok"}
