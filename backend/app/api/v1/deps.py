"""Dépendances injectables pour les routes FastAPI."""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db


async def get_database_session(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AsyncSession, None]:
    """Fournit une session de base de données asynchrone."""
    yield session
