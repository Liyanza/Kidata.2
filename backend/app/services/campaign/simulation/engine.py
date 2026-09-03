"""Orchestrateur principal du Moteur de Simulation & Prescription."""
from datetime import datetime, timezone
from app.schemas.simulation import (
    SimulationInputSchema,
    SimulationResponseSchema,
)
from app.services.campaign.simulation.budget_allocator import BudgetAllocator
from app.services.campaign.simulation.constants import CITY_BENCHMARKS
from app.services.campaign.simulation.form_parser import SimulationFormParser
from app.services.campaign.simulation.metrics_estimator import MetricsEstimator


class SimulationEngine:
    """Point d'entrée de service stateless exécutant le pipeline complet de prescription & projection."""

    @classmethod
    def run(cls, payload: SimulationInputSchema) -> SimulationResponseSchema:
        # 1. Normalisation et validation
        validated_form, city_key = SimulationFormParser.parse_and_validate(payload)
        benchmark = CITY_BENCHMARKS[city_key]

        # 2. Algorithme Prescriptif (Allocation budgétaire + Formats + Créneaux)
        allocator = BudgetAllocator(city_benchmark=benchmark)
        prescription = allocator.allocate(form=validated_form)

        # 3. Algorithme Prédictif (Projections chiffrées & Score de confiance)
        estimator = MetricsEstimator(city_benchmark=benchmark)
        projections = estimator.estimate(form=validated_form, prescription=prescription)

        # 4. Fusion dans le schéma de réponse consolidé
        return SimulationResponseSchema(
            input_summary=validated_form,
            prescription=prescription,
            projections=projections,
            created_at=datetime.now(timezone.utc),
        )
