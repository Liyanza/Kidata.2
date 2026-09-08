"""Tests unitaires pour le moteur complet de simulation."""
import pytest
from app.schemas.simulation import (
    GenderEnum,
    ObjectiveEnum,
    SimulationInputSchema,
    TargetAudienceSchema,
)
from app.services.campaign.simulation.engine import SimulationEngine


def test_simulation_engine_full_run():
    """Vérifie la cohérence mathématique et la structure de la réponse de bout en bout."""
    payload = SimulationInputSchema(
        total_budget_fcfa=150000.0,
        audience=TargetAudienceSchema(
            age_range="18-35",
            gender=GenderEnum.ALL,
            interests=["Vêtements", "Accessoires"],
        ),
        objective=ObjectiveEnum.SALES,
        duration_days=14,
        target_zone="Douala",
        average_basket_fcfa=12000.0,
        daily_lead_capacity=25,
        facebook_followers=5000,
        whatsapp_contacts=800,
    )

    response = SimulationEngine.run(payload)

    # 1. Vérification de la somme des budgets
    total_allocated = (
        response.prescription.meta_ads_allocation.budget_fcfa
        + response.prescription.whatsapp_ads_allocation.budget_fcfa
    )
    assert pytest.approx(total_allocated, 0.01) == 150000.0

    # 2. Vérification des métriques estimées
    proj = response.projections
    assert proj.reach_min > 0
    assert proj.reach_min <= proj.reach_max
    assert proj.expected_impressions >= proj.reach_min
    assert proj.expected_leads > 0
    assert proj.expected_sales_min <= proj.expected_sales_mean <= proj.expected_sales_max
    assert proj.expected_revenue_fcfa_min <= proj.expected_revenue_fcfa_mean <= proj.expected_revenue_fcfa_max
    assert proj.roas_min <= proj.roas_mean <= proj.roas_max
    assert proj.cost_per_acquisition_fcfa > 0

    # 3. Vérification de l'indice de confiance
    assert 0.65 <= proj.confidence_score <= 0.95

    # 4. Formats, créneaux horaires et options d'allocation avec projections dédiées
    assert len(response.prescription.recommended_time_slots) >= 2
    assert len(response.prescription.recommended_formats) >= 2
    assert len(response.prescription.allocation_options) == 3

    for opt in response.prescription.allocation_options:
        assert opt.projections is not None
        assert opt.projections.expected_revenue_fcfa_mean >= 0
        assert opt.projections.reach_min > 0


def test_simulation_engine_invalid_budget():
    """Vérifie qu'une exception est levée si le budget est inférieur au seuil minimal journalier."""
    payload = SimulationInputSchema(
        total_budget_fcfa=5000.0,  # 5 000 FCFA pour 30 jours (trop faible, < 30 000 FCFA requis)
        audience=TargetAudienceSchema(
            age_range="25-45",
            gender=GenderEnum.ALL,
            interests=["Retail"],
        ),
        objective=ObjectiveEnum.AWARENESS,
        duration_days=30,
        target_zone="Yaoundé",
        average_basket_fcfa=10000.0,
        daily_lead_capacity=20,
    )

    with pytest.raises(ValueError, match="inférieur au seuil technique minimal"):
        SimulationEngine.run(payload)
