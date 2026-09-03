"""Endpoint stateless pour la simulation et prescription publicitaire."""
from fastapi import APIRouter, HTTPException, status
from app.schemas.simulation import (
    SimulationInputSchema,
    SimulationResponseSchema,
)
from app.services.campaign.simulation.engine import SimulationEngine

router = APIRouter()


@router.post(
    "/simulate",
    response_model=SimulationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Simuler et prescrire une campagne publicitaire Retail en FCFA",
    description="Moteur prescriptif et prédictif calculant l'allocation optimale du budget et les métriques attendues.",
)
async def simulate_campaign(
    payload: SimulationInputSchema,
) -> SimulationResponseSchema:
    """Exécute la simulation de campagne de manière totalement stateless."""
    try:
        response = SimulationEngine.run(payload)
        return response
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne lors de la simulation : {str(exc)}",
        )
