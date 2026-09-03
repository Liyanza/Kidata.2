"""Tests unitaires pour l'allocateur de budget sous contrainte de capacité."""
import pytest
from app.schemas.simulation import (
    GenderEnum,
    ObjectiveEnum,
    SimulationInputSchema,
    TargetAudienceSchema,
)
from app.services.campaign.simulation.budget_allocator import BudgetAllocator
from app.services.campaign.simulation.constants import CITY_BENCHMARKS


@pytest.fixture
def douala_benchmark():
    return CITY_BENCHMARKS["DOUALA"]


def test_budget_allocator_normal_capacity(douala_benchmark):
    """Vérifie l'allocation standard lorsque la capacité de l'équipe commerciale est suffisante."""
    form = SimulationInputSchema(
        total_budget_fcfa=100000.0,
        audience=TargetAudienceSchema(
            age_range="25-35",
            gender=GenderEnum.ALL,
            interests=["Mode", "Sneakers"],
        ),
        objective=ObjectiveEnum.SALES,
        duration_days=10,
        target_zone="Douala",
        average_basket_fcfa=15000.0,
        daily_lead_capacity=50,  # 500 leads max sur 10 jours = 100 000 FCFA d'absorption WhatsApp possible
        facebook_followers=1000,
        whatsapp_contacts=200,
    )

    allocator = BudgetAllocator(douala_benchmark)
    prescription = allocator.allocate(form)

    # 70% attendu sur WhatsApp pour 'sales' (70 000 FCFA) et 30% sur Meta Ads (30 000 FCFA)
    assert prescription.whatsapp_ads_allocation.budget_fcfa == 70000.0
    assert prescription.meta_ads_allocation.budget_fcfa == 30000.0
    assert prescription.whatsapp_ads_allocation.budget_percentage == 70.0
    assert prescription.meta_ads_allocation.budget_percentage == 30.0
    assert not prescription.operational_bottleneck_detected
    assert prescription.max_supported_leads == 500


def test_budget_allocator_bottleneck_capping(douala_benchmark):
    """Vérifie que le budget WhatsApp est bridé et que le surplus est réinjecté sur Meta Ads si la capacité est faible."""
    form = SimulationInputSchema(
        total_budget_fcfa=200000.0,
        audience=TargetAudienceSchema(
            age_range="20-45",
            gender=GenderEnum.WOMEN,
            interests=["Cosmétiques", "Soins de la peau"],
        ),
        objective=ObjectiveEnum.SALES,
        duration_days=10,
        target_zone="Douala",
        average_basket_fcfa=20000.0,
        daily_lead_capacity=10,  # Seulement 10 leads/jour -> 100 leads sur 10 jours * 200 FCFA = 20 000 FCFA max
        facebook_followers=500,
        whatsapp_contacts=50,
    )

    allocator = BudgetAllocator(douala_benchmark)
    prescription = allocator.allocate(form)

    # Le budget WhatsApp doit être bridé à 20 000 FCFA au lieu de 140 000 FCFA (70%)
    assert prescription.whatsapp_ads_allocation.budget_fcfa == 20000.0
    # Le surplus (180 000 FCFA) doit être transféré sur Meta Ads
    assert prescription.meta_ads_allocation.budget_fcfa == 180000.0
    assert prescription.operational_bottleneck_detected is True
    assert prescription.max_supported_leads == 100
    assert "Alerte Capacité Commerciale" in prescription.rationale
