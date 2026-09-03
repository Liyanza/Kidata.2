"""Algorithme prescriptif d'allocation budgétaire sous contrainte opérationnelle."""
from typing import Any, Dict
from app.schemas.simulation import (
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
    """Alloue intelligemment le budget entre Meta Ads et Click-to-WhatsApp Ads."""

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

        # 4. Allocation théorique souhaitée selon l'objectif
        split_ratios = OBJECTIVE_DEFAULT_SPLIT.get(
            objective,
            OBJECTIVE_DEFAULT_SPLIT["sales"],
        )
        target_wa_budget = total_budget * split_ratios["whatsapp_ratio"]

        # 5. Application de la contrainte d'engorgement opérationnel
        bottleneck_detected = False
        if target_wa_budget > max_spendable_wa_budget:
            allocated_wa_budget = max_spendable_wa_budget
            bottleneck_detected = True
        else:
            allocated_wa_budget = target_wa_budget

        # 6. Le reliquat est réinjecté sur Meta Ads (notoriété, catalogue, retargeting)
        allocated_meta_budget = total_budget - allocated_wa_budget

        # 7. Contrôle des seuils minimaux
        min_wa_budget = MIN_DAILY_BUDGET_WHATSAPP_FCFA * duration
        min_meta_budget = MIN_DAILY_BUDGET_META_FCFA * duration

        if allocated_wa_budget > 0 and allocated_wa_budget < min_wa_budget:
            allocated_wa_budget = min_wa_budget
            allocated_meta_budget = max(0.0, total_budget - allocated_wa_budget)

        if allocated_meta_budget > 0 and allocated_meta_budget < min_meta_budget:
            allocated_meta_budget = min_meta_budget
            allocated_wa_budget = max(0.0, total_budget - allocated_meta_budget)

        # Calcul des ratios effectifs
        wa_percentage = round((allocated_wa_budget / total_budget) * 100.0, 2)
        meta_percentage = round((allocated_meta_budget / total_budget) * 100.0, 2)

        meta_allocation = ChannelAllocationSchema(
            budget_fcfa=round(allocated_meta_budget, 2),
            budget_percentage=meta_percentage,
            daily_budget_fcfa=round(allocated_meta_budget / duration, 2),
        )

        wa_allocation = ChannelAllocationSchema(
            budget_fcfa=round(allocated_wa_budget, 2),
            budget_percentage=wa_percentage,
            daily_budget_fcfa=round(allocated_wa_budget / duration, 2),
        )

        # Rédaction de la justification stratégique
        rationale_text = self._build_rationale(
            form=form,
            meta_alloc=meta_allocation,
            wa_alloc=wa_allocation,
            bottleneck=bottleneck_detected,
            max_leads=max_supported_leads,
        )

        time_slots = [TimeSlotSchema(**slot) for slot in RECOMMENDED_TIME_SLOTS]
        formats = [FormatRecommendationSchema(**fmt) for fmt in RECOMMENDED_FORMATS]

        return PrescriptionOutputSchema(
            meta_ads_allocation=meta_allocation,
            whatsapp_ads_allocation=wa_allocation,
            recommended_time_slots=time_slots,
            recommended_formats=formats,
            rationale=rationale_text,
            operational_bottleneck_detected=bottleneck_detected,
            max_supported_leads=max_supported_leads,
        )

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
