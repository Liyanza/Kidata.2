"""Benchmarks sectoriels Retail / E-commerce calibrés pour le Cameroun et l'Afrique Centrale (FCFA)."""
from typing import Any, Dict

# Benchmarks géographiques par défaut
DEFAULT_CITY = "DOUALA"

CITY_BENCHMARKS: Dict[str, Dict[str, Any]] = {
    "DOUALA": {
        "cpm_min_fcfa": 1400.0,
        "cpm_max_fcfa": 2200.0,
        "cpm_mean_fcfa": 1750.0,
        "ctr_mean": 0.021,  # 2.1% taux de clic moyen
        "cost_per_whatsapp_lead_fcfa": 200.0,  # Coût moyen par conversation engagée
        "ad_frequency_factor": 1.7,
    },
    "YAOUNDE": {
        "cpm_min_fcfa": 1250.0,
        "cpm_max_fcfa": 1950.0,
        "cpm_mean_fcfa": 1550.0,
        "ctr_mean": 0.019,
        "cost_per_whatsapp_lead_fcfa": 180.0,
        "ad_frequency_factor": 1.6,
    },
    "BAFOUSSAM": {
        "cpm_min_fcfa": 1100.0,
        "cpm_max_fcfa": 1600.0,
        "cpm_mean_fcfa": 1300.0,
        "ctr_mean": 0.016,
        "cost_per_whatsapp_lead_fcfa": 160.0,
        "ad_frequency_factor": 1.5,
    },
    "DEFAULT": {
        "cpm_min_fcfa": 1300.0,
        "cpm_max_fcfa": 2100.0,
        "cpm_mean_fcfa": 1650.0,
        "ctr_mean": 0.018,
        "cost_per_whatsapp_lead_fcfa": 190.0,
        "ad_frequency_factor": 1.6,      
    },
}

# Taux de conversion de fermeture commerciale (Closing WhatsApp -> Vente Retail)
CLOSING_RATE_BENCHMARKS = {
    "min": 0.10,   # 10%
    "mean": 0.13,  # 13%
    "max": 0.18,   # 18%
}

# Taux de conversion direct sur Meta Ads (Boutique en ligne / Catalogue)
DIRECT_WEB_CONVERSION_RATE = {
    "min": 0.008,  # 0.8%
    "mean": 0.015, # 1.5%
    "max": 0.022,  # 2.2%
}

# Répartition budgétaire cible théorique selon l'objectif (avant contrainte de capacité)
OBJECTIVE_DEFAULT_SPLIT = {
    "sales": {"whatsapp_ratio": 0.70, "meta_ratio": 0.30},
    "leads": {"whatsapp_ratio": 0.80, "meta_ratio": 0.20},
    "awareness": {"whatsapp_ratio": 0.15, "meta_ratio": 0.85},
}

# Créneaux horaires optimaux Retail en Afrique Centrale (Heure locale WAT / UTC+1)
RECOMMENDED_TIME_SLOTS = [
    {
        "start_time": "12:00",
        "end_time": "14:00",
        "rationale": "Pause déjeuner : forte réactivité aux messages WhatsApp et navigation active sur les flux sociaux.",
    },
    {
        "start_time": "18:30",
        "end_time": "22:00",
        "rationale": "Créneau de détente du soir : pic historique d'achats compulsifs et de consultations de catalogues produits.",
    },
]

# Formats publicitaires recommandés
RECOMMENDED_FORMATS = [
    {
        "channel": "Click-to-WhatsApp",
        "format_name": "Message Direct Amorcé (Bouton CTA 'Envoyer un message')",
        "description": "Image unique produit haute définition ou vidéo courte (15s) avec texte d'accroche direct sur le prix et la disponibilité immédiate.",
    },
    {
        "channel": "Meta Ads",
        "format_name": "Carrousel Produits Multi-articles & Reels Promotionnels",
        "description": "Mise en avant des 5 meilleures ventes avec étiquettes prix claires et preuve sociale (avis clients / unboxing vidéo).",
    },
]

# Paramètres de score de confiance statistique
BASE_CONFIDENCE_SCORE = 0.65
MIN_DAILY_BUDGET_META_FCFA = 1000.0
MIN_DAILY_BUDGET_WHATSAPP_FCFA = 1000.0
