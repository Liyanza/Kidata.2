"""Validation, normalisation et sanitisation des données d'entrée de simulation."""
import re
from typing import Tuple
from app.schemas.simulation import SimulationInputSchema
from app.services.campaign.simulation.constants import (
    CITY_BENCHMARKS,
    DEFAULT_CITY,
    MIN_DAILY_BUDGET_META_FCFA,
)


class SimulationFormParser:
    """Valide et enrichit les données utilisateur avant traitement par les algorithmes."""

    @staticmethod
    def parse_and_validate(input_data: SimulationInputSchema) -> Tuple[SimulationInputSchema, str]:
        """Normalise la zone géographique et s'assure de la cohérence économique minimale."""
        sanitized_city = input_data.target_zone.strip().upper()
        # Supprime les accents et caractères spéciaux simples
        sanitized_city = re.sub(r"[ÉÈÊË]", "E", sanitized_city)
        sanitized_city = re.sub(r"[ÀÂÄ]", "A", sanitized_city)

        resolved_city_key = sanitized_city if sanitized_city in CITY_BENCHMARKS else DEFAULT_CITY

        # Vérification d'un budget journalier minimal global
        min_total_required = MIN_DAILY_BUDGET_META_FCFA * input_data.duration_days
        if input_data.total_budget_fcfa < min_total_required:
            raise ValueError(
                f"Le budget total ({input_data.total_budget_fcfa:,.0f} FCFA) est inférieur au seuil technique minimal "
                f"de {min_total_required:,.0f} FCFA pour une durée de {input_data.duration_days} jours."
            )

        return input_data, resolved_city_key
