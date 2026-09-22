"""Orchestrateur principal du Moteur de Simulation & Prescription."""
from datetime import datetime, timezone
from app.schemas.simulation import (
    SimulationInputSchema,
    SimulationResponseSchema,
)
from app.services.campaign.knowledge.enrichment_service import CampaignAIEnricher
from app.services.campaign.simulation.budget_allocator import BudgetAllocator
from app.services.campaign.simulation.constants import CITY_BENCHMARKS
from app.services.campaign.simulation.form_parser import SimulationFormParser
from app.services.campaign.simulation.metrics_estimator import MetricsEstimator


class SimulationEngine:
    """Point d'entrée de service stateless exécutant le pipeline complet de prescription & projection."""

    @classmethod
    def run(
        cls,
        payload: SimulationInputSchema,
        include_ai_enrichment: bool = True,
    ) -> SimulationResponseSchema:
        # 1. Normalisation et validation
        validated_form, city_key = SimulationFormParser.parse_and_validate(payload)
        benchmark = CITY_BENCHMARKS[city_key]

        # 2. Algorithme Prescriptif (Allocation budgétaire + Formats + Créneaux)
        allocator = BudgetAllocator(city_benchmark=benchmark)
        prescription = allocator.allocate(form=validated_form)

        # 3. Algorithme Prédictif (Projections chiffrées & Score de confiance pour chaque option)
        estimator = MetricsEstimator(city_benchmark=benchmark)
        for option in prescription.allocation_options:
            option.projections = estimator.estimate_for_allocations(
                form=validated_form,
                meta_budget=option.meta_ads_allocation.budget_fcfa,
                wa_budget=option.whatsapp_ads_allocation.budget_fcfa,
                max_supported_leads=prescription.max_supported_leads,
                bottleneck=prescription.operational_bottleneck_detected,
            )

        projections = estimator.estimate(form=validated_form, prescription=prescription)

        # 4. Enrichissement prescriptif par la Base de Connaissances / IA LLM
        ai_enrichment = None
        if include_ai_enrichment:
            ai_enrichment = CampaignAIEnricher.enrich(
                form=validated_form,
                prescription=prescription,
                projections=projections,
            )

        # 5. Fusion dans le schéma de réponse consolidé
        return SimulationResponseSchema(
            input_summary=validated_form,
            prescription=prescription,
            projections=projections,
            ai_enrichment=ai_enrichment,
            created_at=datetime.now(timezone.utc),
        )
