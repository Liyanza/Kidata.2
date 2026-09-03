"""Configuration centrale de l'application avec Pydantic v2."""
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "LIYANZA - Moteur de Simulation & Prescription Digitale"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # Base de données PostgreSQL (SQLAlchemy 2.0 Async)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/liyanza_db"

    # CORS
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://app.liyanza.com",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
