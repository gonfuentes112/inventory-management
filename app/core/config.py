from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_JWT_SECRET_LENGTH = 32
PLACEHOLDER_SECRET_MARKERS = ("change-me", "changeme")


class Settings(BaseSettings):
    app_name: str = "Inventory Management API"
    database_url: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REDIS_URL: str

    CORS_ORIGINS: str = "http://localhost:3000"

    LOGIN_RATE_LIMIT_ATTEMPTS: int = 10
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 300

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def jwt_secret_must_be_strong(cls, value: str) -> str:
        if len(value) < MIN_JWT_SECRET_LENGTH:
            raise ValueError(
                f"JWT_SECRET_KEY must be at least {MIN_JWT_SECRET_LENGTH} characters. "
                "Generate one with: "
                'python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )

        lowered = value.lower()
        if any(marker in lowered for marker in PLACEHOLDER_SECRET_MARKERS):
            raise ValueError(
                "JWT_SECRET_KEY looks like a placeholder value; set a real secret"
            )

        return value

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]


settings = Settings()
