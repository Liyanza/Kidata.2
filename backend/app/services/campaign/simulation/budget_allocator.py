"""Algorithme prescriptif d'allocation budgétaire sous contrainte opérationnelle."""
from typing import Any, Dict, Tuple
from app.schemas.simulation import (
    AllocationStrategyTypeEnum,
    BudgetAllocationOptionSchema,
    ChannelAllocationSchema,
    FormatRecommendationSchema,
    PrescriptionOutputSchema,
    SimulationInputSchema,
    TimeSlotSchema,
)
from app.services.campaign.simulation.constants import (
    MIN_DAILY_BUDGET_META_FCFA,
    MIN_DAILY_BUDGET_WHATSAPP_FCFA,
    OBJECTIVE_DEFAULT_SPLIT,
    RECOMMENDED_FORMATS,
    RECOMMENDED_TIME_SLOTS,
)


class BudgetAllocator:
    """Alloue intelligemment le budget entre Meta Ads et Click-to-WhatsApp Ads selon 3 stratégies distinctes."""

    def __init__(self, city_benchmark: Dict[str, Any]):
        self.benchmark = city_benchmark

    def allocate(self, form: SimulationInputSchema) -> PrescriptionOutputSchema:
        total_budget = form.total_budget_fcfa
        duration = form.duration_days
        daily_capacity = form.daily_lead_capacity
        objective = form.objective.value

        # 1. Capacité maximale théorique de traitement sur la période
        max_supported_leads = daily_capacity * duration

        # 2. Coût unitaire d'acquisition d'une conversation WhatsApp
        cost_per_wa_lead = self.benchmark["cost_per_whatsapp_lead_fcfa"]

        # 3. Budget maximal absorbable par l'équipe sur WhatsApp
        max_spendable_wa_budget = float(max_supported_leads * cost_per_wa_lead)

        # --- Stratégie 1 : Recommandée / Équilibrée ---
        split_ratios = OBJECTIVE_DEFAULT_SPLIT.get(
            objective,
            OBJECTIVE_DEFAULT_SPLIT["sales"],
        )
        rec_meta_alloc, rec_wa_alloc, rec_bottleneck = self._compute_channel_split(
            total_budget=total_budget,
            duration=duration,
            target_wa_ratio=split_ratios["whatsapp_ratio"],
            max_spendable_wa_budget=max_spendable_wa_budget,
        )

        option_recommended = BudgetAllocationOptionSchema(
            strategy_type=AllocationStrategyTypeEnum.RECOMMENDED,
            name="Stratégie 1 : Équilibrée (Recommandée Liyanza)",
            tagline="Équilibre optimal entre ventes directes et notoriété de marque.",
            meta_ads_allocation=rec_meta_alloc,
            whatsapp_ads_allocation=rec_wa_alloc,
            description=(
                "Recommandée pour la majorité des campagnes. Elle adapte la répartition budgétaire "
                "à votre objectif principal tout en évitant d'engorger votre équipe commerciale."
            ),
        )

        # --- Stratégie 2 : Max Conversion Directe (WhatsApp) ---
        conv_meta_alloc, conv_wa_alloc, _ = self._compute_channel_split(
            total_budget=total_budget,
            duration=duration,
            target_wa_ratio=0.85,
            max_spendable_wa_budget=max_spendable_wa_budget,
        )

        option_max_conversion = BudgetAllocationOptionSchema(
            strategy_type=AllocationStrategyTypeEnum.MAX_CONVERSION,
            name="Stratégie 2 : Max Conversion (Ventes Directes WhatsApp)",
            tagline="Focus maximal sur les leads WhatsApp pour un chiffre d'affaires immédiat.",
            meta_ads_allocation=conv_meta_alloc,
            whatsapp_ads_allocation=conv_wa_alloc,
            description=(
                "Recommandée si votre priorité absolue est la génération rapide de trésorerie. "
                "La majorité du budget absorbable est focalisée sur les conversations WhatsApp."
            ),
        )

        # --- Stratégie 3 : Max Visibilité & Portée (Meta Ads) ---
        reach_meta_alloc, reach_wa_alloc, _ = self._compute_channel_split(
            total_budget=total_budget,
            duration=duration,
            target_wa_ratio=0.20,
            max_spendable_wa_budget=max_spendable_wa_budget,
        )

        option_max_reach = BudgetAllocationOptionSchema(
            strategy_type=AllocationStrategyTypeEnum.MAX_REACH,
            name="Stratégie 3 : Max Visibilité (Notoriété & Portée Meta)",
            tagline="Maximise la couverture géographique, la notoriété et le retargeting.",
            meta_ads_allocation=reach_meta_alloc,
            whatsapp_ads_allocation=reach_wa_alloc,
            description=(
                "Recommandée pour le lancement d'un produit, l'ouverture d'une boutique ou la notoriété. "
                "Le budget est massivement orienté vers Meta Ads pour toucher un large public."
            ),
        )

        allocation_options = [
            option_recommended,
            option_max_conversion,
            option_max_reach,
        ]

        # Rédaction de la justification stratégique principale
        rationale_text = self._build_rationale(
            form=form,
            meta_alloc=rec_meta_alloc,
            wa_alloc=rec_wa_alloc,
            bottleneck=rec_bottleneck,
            max_leads=max_supported_leads,
        )

        time_slots = [TimeSlotSchema(**slot) for slot in RECOMMENDED_TIME_SLOTS]
        formats = [FormatRecommendationSchema(**fmt) for fmt in RECOMMENDED_FORMATS]

        return PrescriptionOutputSchema(
            meta_ads_allocation=rec_meta_alloc,
            whatsapp_ads_allocation=rec_wa_alloc,
            allocation_options=allocation_options,
            recommended_time_slots=time_slots,
            recommended_formats=formats,
            rationale=rationale_text,
            operational_bottleneck_detected=rec_bottleneck,
            max_supported_leads=max_supported_leads,
        )

    def _compute_channel_split(
        self,
        total_budget: float,
        duration: int,
        target_wa_ratio: float,
        max_spendable_wa_budget: float,
    ) -> Tuple[ChannelAllocationSchema, ChannelAllocationSchema, bool]:
        """Calcule la ventilation budgétaire entre Meta Ads et WhatsApp sous contraintes."""
        target_wa_budget = total_budget * target_wa_ratio

        bottleneck_detected = False
        if target_wa_budget > max_spendable_wa_budget:
            allocated_wa_budget = max_spendable_wa_budget
            bottleneck_detected = True
        else:
            allocated_wa_budget = target_wa_budget

        allocated_meta_budget = total_budget - allocated_wa_budget

        min_wa_budget = MIN_DAILY_BUDGET_WHATSAPP_FCFA * duration
        min_meta_budget = MIN_DAILY_BUDGET_META_FCFA * duration

        if allocated_wa_budget > 0 and allocated_wa_budget < min_wa_budget:
            allocated_wa_budget = min_wa_budget
            allocated_meta_budget = max(0.0, total_budget - allocated_wa_budget)

        if allocated_meta_budget > 0 and allocated_meta_budget < min_meta_budget:
            allocated_meta_budget = min_meta_budget
            allocated_wa_budget = max(0.0, total_budget - allocated_meta_budget)

        wa_percentage = round((allocated_wa_budget / total_budget) * 100.0, 2)
        meta_percentage = round((allocated_meta_budget / total_budget) * 100.0, 2)

        meta_alloc = ChannelAllocationSchema(
            budget_fcfa=round(allocated_meta_budget, 2),
            budget_percentage=meta_percentage,
            daily_budget_fcfa=round(allocated_meta_budget / duration, 2),
        )

        wa_alloc = ChannelAllocationSchema(
            budget_fcfa=round(allocated_wa_budget, 2),
            budget_percentage=wa_percentage,
            daily_budget_fcfa=round(allocated_wa_budget / duration, 2),
        )

        return meta_alloc, wa_alloc, bottleneck_detected

    def _build_rationale(
        self,
        form: SimulationInputSchema,
        meta_alloc: ChannelAllocationSchema,
        wa_alloc: ChannelAllocationSchema,
        bottleneck: bool,
        max_leads: int,
    ) -> str:
        base = (
            f"Stratégie orientée '{form.objective.value.upper()}' pour la zone de {form.target_zone} sur {form.duration_days} jours. "
            f"Allocation recommandée : {wa_alloc.budget_percentage}% sur Click-to-WhatsApp Ads ({wa_alloc.budget_fcfa:,.0f} FCFA) "
            f"et {meta_alloc.budget_percentage}% sur Meta Ads ({meta_alloc.budget_fcfa:,.0f} FCFA). "
        )
        if bottleneck:
            base += (
                f"[Alerte Capacité Commerciale] Votre équipe peut traiter au maximum {form.daily_lead_capacity} conversations/jour "
                f"(soit un plafond de {max_leads} prospects sur {form.duration_days} jours). "
                f"Afin de ne pas gaspiller votre budget en conversations non traitées, le surplus budgétaire "
                f"a été réinjecté automatiquement sur Meta Ads pour maximiser la visibilité de votre catalogue et le retargeting."
            )
        else:
            base += (
                f"Votre capacité commerciale ({form.daily_lead_capacity} leads/jour) est parfaitement calibrée "
                f"pour absorber le flux direct généré sans perte de conversion."
            )
        return base

