"""Script d'exécution de la simulation LIYANZA avec rendu commercial lisible."""
import argparse
import json
import sys
from app.schemas.simulation import (
    GenderEnum,
    ObjectiveEnum,
    SimulationInputSchema,
    TargetAudienceSchema,
)
from app.services.campaign.simulation.engine import SimulationEngine
from app.services.campaign.simulation.formatter import SimulationFormatter

# Assurer l'encodage UTF-8 dans les terminaux Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Exécuteur de simulation publicitaire LIYANZA")
    parser.add_argument(
        "--json", action="store_true", help="Afficher le résultat brut en JSON"
    )
    args = parser.parse_args()

    payload = SimulationInputSchema(
        total_budget_fcfa=450000.0,
        audience=TargetAudienceSchema(
            age_range="19-25",
            gender=GenderEnum.ALL,
            interests=["Mode", "Sneakers", "Accessoires"],
        ),
        objective=ObjectiveEnum.SALES,
        duration_days=28,
        target_zone="Bafoussam",
        average_basket_fcfa=30000.0,
        daily_lead_capacity=30,
        facebook_followers=25000,
        whatsapp_contacts=385,
    )

    response = SimulationEngine.run(payload)

    if args.json:
        print(json.dumps(response.model_dump(mode="json"), indent=2, ensure_ascii=False))
    else:
        print(SimulationFormatter.format_text_report(response))


if __name__ == "__main__":
    main()
