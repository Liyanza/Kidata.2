"""Endpoint stateless pour la simulation et prescription publicitaire."""
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.simulation import (
    SimulationInputSchema,
    SimulationResponseSchema,
    AIEnrichmentSchema,
)
from app.services.campaign.knowledge.enrichment_service import CampaignAIEnricher
from app.services.campaign.simulation.engine import SimulationEngine

router = APIRouter()


@router.post(
    "/simulate",
    response_model=SimulationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Simuler et prescrire une campagne publicitaire Retail en FCFA",
    description="Moteur prescriptif et prédictif calculant l'allocation optimale du budget, les métriques et les recommandations IA.",
)
def simulate_campaign(
    payload: SimulationInputSchema,
    include_ai: bool = Query(default=True, description="Activer l'enrichissement stratégique et la génération de copies par l'IA"),
) -> SimulationResponseSchema:
    """Exécute la simulation de campagne de manière totalement stateless."""
    try:
        response = SimulationEngine.run(payload, include_ai_enrichment=include_ai)
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


@router.post(
    "/enrich",
    response_model=AIEnrichmentSchema,
    status_code=status.HTTP_200_OK,
    summary="Enrichir une simulation existante avec des recommandations IA et des copies",
    description="Génère des scripts WhatsApp et accroches publicitaires basés sur les données de simulation fournies.",
)
def enrich_simulation(
    payload: SimulationResponseSchema,
) -> AIEnrichmentSchema:
    """Génère l'enrichissement IA à la demande pour une simulation existante."""
    try:
        enrichment = CampaignAIEnricher.enrich(
            form=payload.input_summary,
            prescription=payload.prescription,
            projections=payload.projections,
        )
        return enrichment
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'enrichissement IA : {str(exc)}",
        )
