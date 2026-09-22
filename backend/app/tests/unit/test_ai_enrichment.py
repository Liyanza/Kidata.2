"""Tests unitaires pour la Base de Connaissances et le Service d'Enrichissement IA."""
import json
import pytest
from unittest.mock import patch, MagicMock

from app.schemas.simulation import (
    SimulationInputSchema,
    TargetAudienceSchema,
    ObjectiveEnum,
)
from app.services.campaign.knowledge.knowledge_base import KnowledgeBase
from app.services.campaign.knowledge.enrichment_service import CampaignAIEnricher
from app.services.campaign.simulation.engine import SimulationEngine


@pytest.fixture
def sample_payload():
    return SimulationInputSchema(
        total_budget_fcfa=150000.0,
        audience=TargetAudienceSchema(
            age_range="25-35",
            gender="all",
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


def test_knowledge_base_retrieval():
    """Vérifie le bon fonctionnement des sélecteurs de la Knowledge Base."""
    sector_mode = KnowledgeBase.get_sector_key(["Mode", "Sneakers"])
    assert sector_mode == "mode"

    sector_beaute = KnowledgeBase.get_sector_key(["Cosmétique", "Parfum"])
    assert sector_beaute == "beaute"

    sector_tech = KnowledgeBase.get_sector_key(["Smartphone", "Gadget"])
    assert sector_tech == "tech"

    sector_default = KnowledgeBase.get_sector_key(["Autre"])
    assert sector_default == "default"

    insights_douala = KnowledgeBase.get_city_insights("Douala")
    assert insights_douala["name"] == "Douala"

    insights_yaounde = KnowledgeBase.get_city_insights("Yaoundé")
    assert insights_yaounde["name"] == "Yaoundé"

    hooks = KnowledgeBase.get_hooks("mode", "Douala")
    assert len(hooks) > 0
    assert "Douala" in hooks[0]["hook"]

    scripts = KnowledgeBase.get_whatsapp_scripts("Douala")
    assert "welcome" in scripts
    assert "Douala" in scripts["welcome"]


def test_simulation_engine_includes_ai_enrichment(sample_payload):
    """Vérifie que SimulationEngine intègre l'enrichissement par défaut."""
    response = SimulationEngine.run(sample_payload, include_ai_enrichment=True)

    assert response.ai_enrichment is not None
    assert response.ai_enrichment.provider_used == "knowledge_base_rules"
    assert len(response.ai_enrichment.ad_copy_ideas) > 0
    assert response.ai_enrichment.whatsapp_sales_script.welcome != ""
    assert "Douala" in response.ai_enrichment.strategic_summary


def test_simulation_engine_disable_ai_enrichment(sample_payload):
    """Vérifie que l'enrichissement IA peut être désactivé."""
    response = SimulationEngine.run(sample_payload, include_ai_enrichment=False)
    assert response.ai_enrichment is None


def test_grok_llm_mock_call(sample_payload):
    """Vérifie l'appel et le parsing des réponses du LLM Grok (xAI) lorsque la clé API est configurée."""
    mock_grok_response = {
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "strategic_summary": "Analyse Grok : Très fort potentiel retail à Douala.",
                        "ad_copy_ideas": [
                            {
                                "hook": "🚀 Offre exclusive Grok à Douala !",
                                "angle": "Rareté",
                                "cta": "Acheter maintenant"
                            }
                        ],
                        "whatsapp_sales_script": {
                            "welcome": "Bienvenue via Grok !",
                            "follow_up_2h": "Des questions ?",
                            "closing": "Validez votre commande."
                        },
                        "market_insights": {"characteristics": "Marché très actif"}
                    })
                },
                "finish_reason": "stop"
            }
        ]
    }

    mock_http_response = MagicMock()
    mock_http_response.status = 200
    mock_http_response.read.return_value = json.dumps(mock_grok_response).encode("utf-8")
    mock_http_response.__enter__.return_value = mock_http_response

    with patch("app.core.config.settings.LLM_PROVIDER", "grok"), \
         patch("app.core.config.settings.GROK_API_KEY", "xai-test-key"), \
         patch("urllib.request.urlopen", return_value=mock_http_response):
        
        response = SimulationEngine.run(sample_payload, include_ai_enrichment=True)

        assert response.ai_enrichment is not None
        assert response.ai_enrichment.provider_used == "grok_llm"
        assert response.ai_enrichment.strategic_summary == "Analyse Grok : Très fort potentiel retail à Douala."
        assert len(response.ai_enrichment.ad_copy_ideas) == 1
        assert response.ai_enrichment.ad_copy_ideas[0].hook == "🚀 Offre exclusive Grok à Douala !"


def test_gemini_llm_mock_call(sample_payload):
    """Vérifie le parsing des réponses du LLM Gemini lorsqu'une clé API est configurée."""
    mock_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "strategic_summary": "Excellente opportunité à Douala pour la mode.",
                                "ad_copy_ideas": [
                                    {
                                        "hook": "🔥 Arrivage Douala !",
                                        "angle": "Nouveauté",
                                        "cta": "Commander"
                                    }
                                ],
                                "whatsapp_sales_script": {
                                    "welcome": "Bienvenue chez nous !",
                                    "follow_up_2h": "Toujours intéressé ?",
                                    "closing": "Envoyez vos coordonnées."
                                },
                                "market_insights": {"characteristics": "Marche réactif"}
                            })
                        }
                    ]
                }
            }
        ]
    }

    mock_http_response = MagicMock()
    mock_http_response.status = 200
    mock_http_response.read.return_value = json.dumps(mock_gemini_response).encode("utf-8")
    mock_http_response.__enter__.return_value = mock_http_response

    with patch("app.core.config.settings.LLM_PROVIDER", "gemini"), \
         patch("app.core.config.settings.GEMINI_API_KEY", "test-api-key"), \
         patch("urllib.request.urlopen", return_value=mock_http_response):
        
        response = SimulationEngine.run(sample_payload, include_ai_enrichment=True)

        assert response.ai_enrichment is not None
        assert response.ai_enrichment.provider_used == "gemini_llm"
        assert response.ai_enrichment.strategic_summary == "Excellente opportunité à Douala pour la mode."
        assert len(response.ai_enrichment.ad_copy_ideas) == 1
        assert response.ai_enrichment.ad_copy_ideas[0].hook == "🔥 Arrivage Douala !"

