# LIYANZA — Moteur de Simulation & Prescription Digitale

Moteur décisionnel stateless et modulaire d'aide à la décision publicitaire, spécialement calibré pour les acteurs du **Commerce et Retail en Afrique Centrale (montants en FCFA)**.

---

## 1. Présentation Générale

Le moteur de simulation LIYANZA résout la complexité du media-planning digital pour les commerçants :
- **Zéro friction technique** : L'utilisateur ne manipule jamais de métriques publicitaires abstraites (CPM, CPC, CTR). Celles-ci sont automatiquement calibrées via des priors sectoriels et géographiques (`constants.py`).
- **Double fonction intégrée** :
  1. **Prescription** : Répartition budgétaire optimale entre **Meta Ads** (Notoriété, Catalogue & Retargeting) et **Click-to-WhatsApp Ads** (Conversion directe), avec prescription des créneaux horaires locaux et des formats créatifs.
  2. **Projection** : Estimation probabiliste des retombées commerciales (portée unique, volume de leads, fourchettes de ventes, chiffre d'affaires prévisionnel, CAC unitaire et ROAS).

---

## 2. Arborescence du Projet

```text
backend/app/
├── api/
│   └── v1/
│       ├── __init__.py
│       ├── deps.py
│       ├── router.py
│       └── endpoints/
│           ├── __init__.py
│           └── simulation.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   └── database.py
├── models/
│   ├── __init__.py
│   ├── base.py
│   └── campaign_ai.py
├── schemas/
│   ├── __init__.py
│   └── simulation.py
├── services/
│   └── campaign/
│       └── simulation/
│           ├── __init__.py
│           ├── constants.py
│           ├── form_parser.py
│           ├── budget_allocator.py
│           ├── metrics_estimator.py
│           └── engine.py
└── tests/
    ├── __init__.py
    └── unit/
        ├── test_budget_allocator.py
        └── test_simulation_engine.py
```

---

## 3. Contrat d'Interface API

### Endpoint : `POST /api/v1/campaigns/simulate`
- **Type** : Stateless (sans état)
- **Validation** : Schémas Pydantic v2 stricts

#### Exemple de Payload d'Entrée (`SimulationInputSchema`)
```json
{
  "total_budget_fcfa": 150000.0,
  "audience": {
    "age_range": "25-35",
    "gender": "all",
    "interests": ["Mode", "Sneakers", "Accessoires"]
  },
  "objective": "sales",
  "duration_days": 14,
  "target_zone": "Douala",
  "average_basket_fcfa": 15000.0,
  "daily_lead_capacity": 25,
  "facebook_followers": 3500,
  "whatsapp_contacts": 450
}
```

#### Exemple de Réponse JSON (`SimulationResponseSchema`)
```json
{
  "input_summary": {
    "total_budget_fcfa": 150000.0,
    "audience": {
      "age_range": "25-35",
      "gender": "all",
      "interests": ["Mode", "Sneakers", "Accessoires"]
    },
    "objective": "sales",
    "duration_days": 14,
    "target_zone": "Douala",
    "average_basket_fcfa": 15000.0,
    "daily_lead_capacity": 25,
    "facebook_followers": 3500,
    "whatsapp_contacts": 450
  },
  "prescription": {
    "meta_ads_allocation": {
      "budget_fcfa": 80000.0,
      "budget_percentage": 53.33,
      "daily_budget_fcfa": 5714.29
    },
    "whatsapp_ads_allocation": {
      "budget_fcfa": 70000.0,
      "budget_percentage": 46.67,
      "daily_budget_fcfa": 5000.0
    },
    "recommended_time_slots": [
      {
        "start_time": "12:00",
        "end_time": "14:00",
        "rationale": "Pause déjeuner : forte réactivité aux messages WhatsApp et navigation active sur les flux sociaux."
      },
      {
        "start_time": "18:30",
        "end_time": "22:00",
        "rationale": "Créneau de détente du soir : pic historique d'achats compulsifs et de consultations de catalogues produits."
      }
    ],
    "recommended_formats": [
      {
        "channel": "Click-to-WhatsApp",
        "format_name": "Message Direct Amorcé (Bouton CTA 'Envoyer un message')",
        "description": "Image unique produit haute définition ou vidéo courte (15s) avec texte d'accroche direct sur le prix et la disponibilité immédiate."
      },
      {
        "channel": "Meta Ads",
        "format_name": "Carrousel Produits Multi-articles & Reels Promotionnels",
        "description": "Mise en avant des 5 meilleures ventes avec étiquettes prix claires et preuve sociale (avis clients / unboxing vidéo)."
      }
    ],
    "rationale": "Stratégie orientée 'SALES' pour la zone de Douala sur 14 jours...",
    "operational_bottleneck_detected": true,
    "max_supported_leads": 350
  },
  "projections": {
    "reach_min": 55320,
    "reach_max": 86940,
    "expected_impressions": 88710,
    "expected_clicks": 1862,
    "expected_leads": 350,
    "expected_sales_min": 41,
    "expected_sales_max": 72,
    "expected_sales_mean": 54,
    "expected_revenue_fcfa_min": 615000.0,
    "expected_revenue_fcfa_max": 1080000.0,
    "expected_revenue_fcfa_mean": 810000.0,
    "cost_per_acquisition_fcfa": 2777.78,
    "roas_min": 4.10,
    "roas_max": 7.20,
    "roas_mean": 5.40,
    "confidence_score": 0.86
  },
  "created_at": "2026-09-03T16:10:00Z"
}
```

---

## 4. Fonctionnement des Algorithmes Clés

### A. Optimisation sous Contrainte Opérationnelle (`budget_allocator.py`)
1. **Plafond de capacité absorbable** :
   $$C_{\max} = \text{daily\_lead\_capacity} \times \text{duration\_days}$$
2. **Budget WhatsApp maximal absorbable** :
   $$B_{WA,\max} = C_{\max} \times \text{CPC}_{WA}$$
3. **Protection contre le gaspillage publicitaire** :
   Si le budget WhatsApp cible ($B_{WA,\text{cible}} = \text{Budget Total} \times \text{Ratio}$) dépasse $B_{WA,\max}$, le budget WhatsApp est bridé à $B_{WA,\max}$, l'indicateur `operational_bottleneck_detected` est activé, et tout le reliquat est réinjecté sur Meta Ads (notoriété, carrousels produits et retargeting).

### B. Projections Commerciales & Statistiques (`metrics_estimator.py`)
- **Portée unique & Impressions** : Dérivées des CPM locaux (1 200 à 2 200 FCFA selon la ville) corrigés de la fréquence publicitaire (1.5 - 1.7) et du facteur d'amplification des abonnés organiques existants.
- **Conversions et Ventes** :
  - Flux WhatsApp : $\text{Leads} \times \text{Taux de Closing Retail}$ (10% à 18%).
  - Flux Meta Ads direct : $\text{Clics Catalogue} \times \text{Taux de Conversion}$ (0.8% à 2.2%).
- **CAC & ROAS** :
  $$\text{CAC} = \frac{\text{Budget Total}}{\text{Ventes Moyennes}}, \quad \text{ROAS} = \frac{\text{Chiffre d'Affaires Prévisionnel}}{\text{Budget Total}}$$
- **Indice de Confiance Statistique** : Calibré à partir d'une base froide ($0.65$), bonifié par la durée ($\ge 7\text{j}$ et $\ge 14\text{j}$), la densité budgétaire ($\ge 5\text{ }000\text{ FCFA/j}$) et la présence d'actifs sociaux (abonnés / contacts).

---

## 5. Installation & Exécution des Tests

### Installation des Dépendances
```bash
pip install fastapi pydantic pydantic-settings sqlalchemy asyncpg uvicorn pytest pytest-asyncio
```

### Exécution des Tests Unitaires
Depuis le dossier `backend` :
```bash
pytest app/tests/unit/ -v
```
