"""Routeur principal de l'API v1."""
from fastapi import APIRouter
from app.api.v1.endpoints import simulation

api_router = APIRouter()
api_router.include_router(
    simulation.router,
    prefix="/campaigns",
    tags=["Simulation & Prescription"],
)
