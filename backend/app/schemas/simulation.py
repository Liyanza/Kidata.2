"""Schémas Pydantic v2 pour la validation des entrées et sorties de simulation."""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class GenderEnum(str, Enum):
    ALL = "all"
    WOMEN = "women"
    MEN = "men"


class ObjectiveEnum(str, Enum):
    SALES = "sales"
    LEADS = "leads"
    AWARENESS = "awareness"


class TargetAudienceSchema(BaseModel):
    age_range: str = Field(
        ...,
        description="Tranche d'âge cible au format 'MIN-MAX' (ex: '18-25', '25-35', '35-50')",
        examples=["25-35"],
    )
    gender: GenderEnum = Field(
        default=GenderEnum.ALL,
        description="Genre ciblé ('all', 'women', 'men')",
    )
    interests: List[str] = Field(
        default_factory=list,
        description="Centres d'intérêt retail ciblés (ex: ['Mode', 'Chaussures', 'Cosmétique'])",
    )

    @field_validator("age_range")
    @classmethod
    def validate_age_range_format(cls, v: str) -> str:
        parts = v.strip().split("-")
        if len(parts) != 2:
            raise ValueError("Le format de age_range doit être 'MIN-MAX' (ex: '18-35')")
        try:
            min_age, max_age = int(parts[0]), int(parts[1])
            if min_age < 13 or max_age > 85 or min_age >= max_age:
                raise ValueError("Tranche d'âge invalide (min >= 13, max <= 85 et min < max)")
        except ValueError as e:
            raise ValueError(f"Erreur de conversion de age_range : {str(e)}")
        return v


class SimulationInputSchema(BaseModel):
    total_budget_fcfa: float = Field(
        ...,
        gt=0,
        description="Budget total alloué à la campagne en FCFA (ex: 150000)",
        examples=[150000.0],
    )
    audience: TargetAudienceSchema = Field(
        ...,
        description="Détails démographiques de l'audience cible",
    )
    objective: ObjectiveEnum = Field(
        default=ObjectiveEnum.SALES,
        description="Objectif principal de la campagne ('sales', 'leads', 'awareness')",
    )
    duration_days: int = Field(
        ...,
        ge=1,
        le=90,
        description="Durée de diffusion de la campagne en jours",
        examples=[14],
    )
    target_zone: str = Field(
        ...,
        description="Zone géographique ciblée (ex: 'Douala', 'Yaoundé', 'Bafoussam')",
        examples=["Douala"],
    )
    average_basket_fcfa: float = Field(
        ...,
        gt=0,
        description="Panier moyen unitaire d'un article ou d'une commande en FCFA",
        examples=[12500.0],
    )
    daily_lead_capacity: int = Field(
        ...,
        ge=1,
        description="Capacité opérationnelle journalière de traitement des leads WhatsApp par l'équipe",
        examples=[30],
    )
    facebook_followers: Optional[int] = Field(
        default=0,
        ge=0,
        description="Nombre d'abonnés existants sur la page Facebook/Instagram (facteur d'amplification)",
    )
    whatsapp_contacts: Optional[int] = Field(
        default=0,
        ge=0,
        description="Nombre de contacts qualifiés existants dans le carnet d'adresses WhatsApp",
    )


class AllocationStrategyTypeEnum(str, Enum):
    RECOMMENDED = "recommended"
    MAX_CONVERSION = "max_conversion"
    MAX_REACH = "max_reach"


class ChannelAllocationSchema(BaseModel):
    budget_fcfa: float = Field(..., description="Budget alloué au canal en FCFA")
    budget_percentage: float = Field(..., description="Part relative du budget total en %")
    daily_budget_fcfa: float = Field(..., description="Budget moyen disponible par jour en FCFA")


class ProjectionOutputSchema(BaseModel):
    reach_min: int = Field(..., description="Portée unique minimale estimée")
    reach_max: int = Field(..., description="Portée unique maximale estimée")
    expected_impressions: int = Field(..., description="Volume total d'impressions publicitaires estimé")
    expected_clicks: int = Field(..., description="Nombre total de clics générés")
    expected_leads: int = Field(..., description="Nombre prévisionnel de conversations WhatsApp initiées")
    expected_sales_min: int = Field(..., description="Estimation basse du nombre de ventes conclues")
    expected_sales_max: int = Field(..., description="Estimation haute du nombre de ventes conclues")
    expected_sales_mean: int = Field(..., description="Nombre moyen prévisionnel de ventes")
    expected_revenue_fcfa_min: float = Field(..., description="Chiffre d'affaires prévisionnel bas en FCFA")
    expected_revenue_fcfa_max: float = Field(..., description="Chiffre d'affaires prévisionnel haut en FCFA")
    expected_revenue_fcfa_mean: float = Field(..., description="Chiffre d'affaires prévisionnel moyen en FCFA")
    cost_per_acquisition_fcfa: float = Field(..., description="Coût d'Acquisition Client (CAC) unitaire en FCFA")
    roas_min: float = Field(..., description="Retour sur dépenses publicitaires (ROAS) bas")
    roas_max: float = Field(..., description="Retour sur dépenses publicitaires (ROAS) haut")
    roas_mean: float = Field(..., description="Retour sur dépenses publicitaires (ROAS) moyen")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Indice de confiance statistique du modèle prédictif",
    )


class BudgetAllocationOptionSchema(BaseModel):
    strategy_type: AllocationStrategyTypeEnum = Field(..., description="Type de stratégie d'allocation")
    name: str = Field(..., description="Nom commercial de la stratégie d'allocation")
    tagline: str = Field(..., description="Accroche ou positionnement stratégique résumé")
    meta_ads_allocation: ChannelAllocationSchema = Field(..., description="Allocation Meta Ads")
    whatsapp_ads_allocation: ChannelAllocationSchema = Field(..., description="Allocation Click-to-WhatsApp")
    projections: Optional[ProjectionOutputSchema] = Field(None, description="Projections et impact CA spécifiques à cette stratégie")
    description: str = Field(..., description="Explication détaillée de la stratégie et des cas d'usage")


class TimeSlotSchema(BaseModel):
    start_time: str = Field(..., description="Heure de début (ex: '12:00')")
    end_time: str = Field(..., description="Heure de fin (ex: '14:00')")
    rationale: str = Field(..., description="Justification comportementale locale")


class FormatRecommendationSchema(BaseModel):
    channel: str = Field(..., description="Canal concerné ('Meta Ads' ou 'Click-to-WhatsApp')")
    format_name: str = Field(..., description="Nom du format publicitaire recommandé")
    description: str = Field(..., description="Directives créatives et d'accroche")


class PrescriptionOutputSchema(BaseModel):
    meta_ads_allocation: ChannelAllocationSchema
    whatsapp_ads_allocation: ChannelAllocationSchema
    allocation_options: List[BudgetAllocationOptionSchema] = Field(
        default_factory=list,
        description="Les 3 types d'allocation budgétaire recommandées (Équilibrée, Max Ventes, Max Visibilité)",
    )
    recommended_time_slots: List[TimeSlotSchema]
    recommended_formats: List[FormatRecommendationSchema]
    rationale: str = Field(..., description="Explication stratégique de la répartition")
    operational_bottleneck_detected: bool = Field(
        ...,
        description="Indique si la capacité WhatsApp a plafonné le budget WhatsApp au profit de Meta Ads",
    )
    max_supported_leads: int = Field(
        ...,
        description="Capacité totale maximale de leads traitables sur la durée de la campagne",
    )


class SimulationResponseSchema(BaseModel):
    input_summary: SimulationInputSchema
    prescription: PrescriptionOutputSchema
    projections: ProjectionOutputSchema
    created_at: datetime = Field(default_factory=datetime.utcnow)
