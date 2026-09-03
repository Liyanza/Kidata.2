"""Modèle de persistance des simulations et campagnes IA."""
import uuid
from typing import Any, Dict, Optional
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CampaignAI(Base):
    """Entité représentant une simulation et ses prescriptions générées par le moteur."""

    __tablename__ = "campaign_ai"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="Simulation Campagne Retail",
    )
    simulation_inputs: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Paramètres bruts fournis par le commerçant",
    )
    prescriptions: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Allocations budgétaires, créneaux et formats prescrits",
    )
    predicted_metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Projections statistiques (reach, leads, ventes, ROAS)",
    )
    actual_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Métriques réelles post-campagne pour calibration du modèle",
    )
