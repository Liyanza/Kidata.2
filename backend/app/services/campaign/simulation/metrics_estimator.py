"""Modèle d'estimation prédictive et statistique des performances."""
from typing import Any, Dict
from app.schemas.simulation import (
    PrescriptionOutputSchema,
    ProjectionOutputSchema,
    SimulationInputSchema,
)
from app.services.campaign.simulation.constants import (
    BASE_CONFIDENCE_SCORE,
    CLOSING_RATE_BENCHMARKS,
    DIRECT_WEB_CONVERSION_RATE,
)


class MetricsEstimator:
    """Calcule les projections de reach, clics, leads, ventes, chiffre d'affaires, CAC et ROAS."""

    def __init__(self, city_benchmark: Dict[str, Any]):
        self.benchmark = city_benchmark

    def estimate(
        self,
        form: SimulationInputSchema,
        prescription: PrescriptionOutputSchema,
    ) -> ProjectionOutputSchema:
        return self.estimate_for_allocations(
            form=form,
            meta_budget=prescription.meta_ads_allocation.budget_fcfa,
            wa_budget=prescription.whatsapp_ads_allocation.budget_fcfa,
            max_supported_leads=prescription.max_supported_leads,
            bottleneck=prescription.operational_bottleneck_detected,
        )

    def estimate_for_allocations(
        self,
        form: SimulationInputSchema,
        meta_budget: float,
        wa_budget: float,
        max_supported_leads: int,
        bottleneck: bool = False,
    ) -> ProjectionOutputSchema:
        total_budget = form.total_budget_fcfa
        basket = form.average_basket_fcfa

        # 1. Facteur d'amplification organique basé sur les actifs existants
        followers_boost = min(0.15, (form.facebook_followers or 0) / 100_000.0)
        contacts_boost = min(0.08, (form.whatsapp_contacts or 0) / 10_000.0)

        # 2. Portée et Impressions publicitaires
        cpm_min = self.benchmark["cpm_min_fcfa"]
        cpm_mean = self.benchmark["cpm_mean_fcfa"]
        cpm_max = self.benchmark["cpm_max_fcfa"]
        frequency = self.benchmark["ad_frequency_factor"]

        impressions_min = (total_budget / cpm_max) * 1000.0
        impressions_mean = (total_budget / cpm_mean) * 1000.0
        impressions_max = (total_budget / cpm_min) * 1000.0

        reach_min = int((impressions_min / frequency) * (1.0 + followers_boost))
        reach_max = int((impressions_max / frequency) * (1.0 + followers_boost))
        expected_impressions = int(impressions_mean * (1.0 + followers_boost))

        # 3. Clics générés
        ctr = self.benchmark["ctr_mean"]
        expected_clicks = int(expected_impressions * ctr)

        # 4. Leads WhatsApp attendus
        cost_per_wa_lead = self.benchmark["cost_per_whatsapp_lead_fcfa"]
        if wa_budget > 0:
            raw_leads = wa_budget / cost_per_wa_lead
            expected_leads = int(min(raw_leads, max_supported_leads))
        else:
            expected_leads = 0

        # 5. Ventes attendues
        closing_min = CLOSING_RATE_BENCHMARKS["min"] + contacts_boost
        closing_mean = CLOSING_RATE_BENCHMARKS["mean"] + contacts_boost
        closing_max = CLOSING_RATE_BENCHMARKS["max"] + contacts_boost

        wa_sales_min = expected_leads * closing_min
        wa_sales_mean = expected_leads * closing_mean
        wa_sales_max = expected_leads * closing_max

        direct_clicks = int((meta_budget / (cpm_mean / 1000.0)) * ctr) if meta_budget > 0 else 0
        direct_sales_min = direct_clicks * DIRECT_WEB_CONVERSION_RATE["min"]
        direct_sales_mean = direct_clicks * DIRECT_WEB_CONVERSION_RATE["mean"]
        direct_sales_max = direct_clicks * DIRECT_WEB_CONVERSION_RATE["max"]

        total_sales_min = int(round(wa_sales_min + direct_sales_min))
        total_sales_mean = int(round(wa_sales_mean + direct_sales_mean))
        total_sales_max = int(round(wa_sales_max + direct_sales_max))

        total_sales_mean = max(1 if total_budget >= 15000 else 0, total_sales_mean)
        total_sales_max = max(total_sales_mean, total_sales_max)
        total_sales_min = min(total_sales_mean, total_sales_min)

        # 6. Chiffre d'Affaires prévisionnel en FCFA
        revenue_min = round(total_sales_min * basket, 2)
        revenue_mean = round(total_sales_mean * basket, 2)
        revenue_max = round(total_sales_max * basket, 2)

        # 7. Coût d'Acquisition Client (CAC) et ROAS
        cac = round(total_budget / total_sales_mean, 2) if total_sales_mean > 0 else 0.0
        roas_min = round(revenue_min / total_budget, 2) if total_budget > 0 else 0.0
        roas_mean = round(revenue_mean / total_budget, 2) if total_budget > 0 else 0.0
        roas_max = round(revenue_max / total_budget, 2) if total_budget > 0 else 0.0

        # 8. Score de confiance statistique calibré
        confidence_score = self._compute_confidence_score(
            duration_days=form.duration_days,
            total_budget=total_budget,
            has_followers=(form.facebook_followers or 0) > 500,
            has_contacts=(form.whatsapp_contacts or 0) > 100,
            bottleneck=bottleneck,
        )

        return ProjectionOutputSchema(
            reach_min=reach_min,
            reach_max=reach_max,
            expected_impressions=expected_impressions,
            expected_clicks=expected_clicks,
            expected_leads=expected_leads,
            expected_sales_min=total_sales_min,
            expected_sales_max=total_sales_max,
            expected_sales_mean=total_sales_mean,
            expected_revenue_fcfa_min=revenue_min,
            expected_revenue_fcfa_max=revenue_max,
            expected_revenue_fcfa_mean=revenue_mean,
            cost_per_acquisition_fcfa=cac,
            roas_min=roas_min,
            roas_max=roas_max,
            roas_mean=roas_mean,
            confidence_score=confidence_score,
        )

    def _compute_confidence_score(
        self,
        duration_days: int,
        total_budget: float,
        has_followers: bool,
        has_contacts: bool,
        bottleneck: bool,
    ) -> float:
        """Calcule un indice de fiabilité entre 0.0 et 1.0 (base froide à 0.65)."""
        score = BASE_CONFIDENCE_SCORE

        if duration_days >= 7:
            score += 0.08
        if duration_days >= 14:
            score += 0.04

        if (total_budget / duration_days) >= 5000:
            score += 0.05

        if has_followers:
            score += 0.04
        if has_contacts:
            score += 0.04

        if bottleneck:
            score -= 0.03

        return round(min(0.95, max(0.50, score)), 2)
