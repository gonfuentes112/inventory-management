import logging
from os import getenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.db.database import engine

from app.api.products import router as product_router
from app.api.category import router as category_router
from app.api.users import router as users_router
from app.api.orders import router as orders_router

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(product_router)
app.include_router(category_router)
app.include_router(users_router)
app.include_router(orders_router)


@app.get("/")
def root():
    return {"message": settings.app_name}


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check failed: database unavailable")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )

    return {"status": "ok"}
