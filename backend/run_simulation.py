"""Script d'exécution de la simulation LIYANZA dans le terminal."""
import json
from app.schemas.simulation import (
    GenderEnum,
    ObjectiveEnum,
    SimulationInputSchema,
    TargetAudienceSchema,
)
from app.services.campaign.simulation.engine import SimulationEngine


def main():
    payload = SimulationInputSchema(
        total_budget_fcfa=150000.0,
        audience=TargetAudienceSchema(
            age_range="25-35",
            gender=GenderEnum.ALL,
            interests=["Mode", "Sneakers", "Accessoires"],
        ),
        objective=ObjectiveEnum.SALES,
        duration_days=14,
        target_zone="Douala",
        average_basket_fcfa=15000.0,
        daily_lead_capacity=25,
        facebook_followers=3500,
        whatsapp_contacts=450,
    )

    response = SimulationEngine.run(payload)
    print(json.dumps(response.model_dump(mode="json"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
