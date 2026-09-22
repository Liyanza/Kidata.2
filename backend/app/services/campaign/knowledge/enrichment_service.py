"""Service d'enrichissement IA et Knowledge Base pour les simulations de campagne."""
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from app.core.config import settings
from app.schemas.simulation import (
    SimulationInputSchema,
    PrescriptionOutputSchema,
    ProjectionOutputSchema,
    AIEnrichmentSchema,
    AdCopyIdeaSchema,
    WhatsAppSalesScriptSchema,
)
from app.services.campaign.knowledge.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class CampaignAIEnricher:
    """Service hybride d'enrichissement : Combine la Knowledge Base locale et les LLMs (Grok / Gemini)."""

    @classmethod
    def _clean_json_response(cls, text: str) -> str:
        """Nettoie une réponse texte pour en extraire le JSON brut sans balises markdown."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

    @classmethod
    def enrich(
        cls,
        form: SimulationInputSchema,
        prescription: PrescriptionOutputSchema,
        projections: ProjectionOutputSchema,
    ) -> AIEnrichmentSchema:
        """Génère l'enrichissement stratégique et créatif pour la simulation."""
        sector_key = KnowledgeBase.get_sector_key(form.audience.interests)
        city_insights = KnowledgeBase.get_city_insights(form.target_zone)
        raw_hooks = KnowledgeBase.get_hooks(sector_key, form.target_zone)
        scripts = KnowledgeBase.get_whatsapp_scripts(form.target_zone)

        provider = (settings.LLM_PROVIDER or "grok").lower()
        grok_key = settings.GROK_API_KEY or settings.XAI_API_KEY

        # 1. Tenter d'enrichir via Grok LLM (xAI) si configuré ou disponible
        if provider in ("grok", "xai", "auto") and grok_key:
            try:
                grok_result = cls._call_grok_llm(form, prescription, projections, city_insights, grok_key)
                if grok_result:
                    return grok_result
            except Exception as e:
                logger.warning(f"Échec de l'appel Grok LLM, tentative de secours : {e}")

        # 2. Tenter d'enrichir via Gemini LLM si configuré ou en secours
        if provider in ("gemini", "auto") or (provider == "grok" and settings.GEMINI_API_KEY):
            if settings.GEMINI_API_KEY:
                try:
                    gemini_result = cls._call_gemini_llm(form, prescription, projections, city_insights)
                    if gemini_result:
                        return gemini_result
                except Exception as e:
                    logger.warning(f"Échec de l'appel Gemini LLM, basculement sur la Knowledge Base locale : {e}")

        # 3. Reconstitution via la Knowledge Base locale (Fallback déterministe)
        return cls._build_rule_based_enrichment(
            form=form,
            prescription=prescription,
            projections=projections,
            city_insights=city_insights,
            raw_hooks=raw_hooks,
            scripts=scripts,
        )

    @classmethod
    def _build_rule_based_enrichment(
        cls,
        form: SimulationInputSchema,
        prescription: PrescriptionOutputSchema,
        projections: ProjectionOutputSchema,
        city_insights: Dict[str, Any],
        raw_hooks: list,
        scripts: dict,
    ) -> AIEnrichmentSchema:
        """Génère un enrichissement de haute qualité basé sur la Knowledge Base locale."""
        budget_fmt = f"{form.total_budget_fcfa:,.0f}".replace(",", " ")
        summary = (
            f"Campagne Retail à {form.target_zone} ({form.duration_days} jours, Budget: {budget_fmt} FCFA). "
            f"Objectif ciblé : {form.objective.upper()}. "
            f"Spécificité locale : {city_insights['characteristics']} "
            f"Projections moyennes : {projections.expected_sales_mean} ventes estimées (ROAS moyen: {projections.roas_mean:.2f})."
        )
        if prescription.operational_bottleneck_detected:
            summary += (
                f" ⚠️ Capacité opérationnelle WhatsApp plafonnée à {prescription.max_supported_leads} leads. "
                "Le budget excédentaire a été réalloué sur Meta Ads pour maximiser la notoriété."
            )

        ad_copy_ideas = [
            AdCopyIdeaSchema(
                hook=h["hook"],
                angle=h["angle"],
                cta=h["cta"],
            )
            for h in raw_hooks
        ]

        sales_script = WhatsAppSalesScriptSchema(
            welcome=scripts["welcome"],
            follow_up_2h=scripts["follow_up_2h"],
            closing=scripts["closing"],
        )

        return AIEnrichmentSchema(
            strategic_summary=summary,
            ad_copy_ideas=ad_copy_ideas,
            whatsapp_sales_script=sales_script,
            market_insights=city_insights,
            provider_used="knowledge_base_rules",
        )

    @classmethod
    def _get_prompt_text(
        cls,
        form: SimulationInputSchema,
        prescription: PrescriptionOutputSchema,
        projections: ProjectionOutputSchema,
        city_insights: Dict[str, Any],
    ) -> str:
        """Construit le prompt commun pour l'analyse stratégique LLM."""
        return f"""Tu es un expert en Media Planning et Marketing Digital pour le commerce Retail en Afrique Centrale (Zone FCFA).
Analyse les résultats de cette simulation de campagne et génère un enrichissement stratégique au format JSON strict.

DONNÉES DE LA SIMULATION :
- Zone cible : {form.target_zone}
- Durée : {form.duration_days} jours
- Budget total : {form.total_budget_fcfa} FCFA
- Objectif : {form.objective}
- Centres d'intérêt : {", ".join(form.audience.interests)}
- Capacité WhatsApp : {form.daily_lead_capacity} leads/jour
- Allocation Meta Ads : {prescription.meta_ads_allocation.budget_fcfa} FCFA ({prescription.meta_ads_allocation.budget_percentage}%)
- Allocation WhatsApp Ads : {prescription.whatsapp_ads_allocation.budget_fcfa} FCFA ({prescription.whatsapp_ads_allocation.budget_percentage}%)
- Projections : {projections.expected_sales_mean} ventes moyennes, ROAS moyen {projections.roas_mean:.2f}
- Caractéristiques marché local : {city_insights.get('characteristics', '')}

Formate TA RÉPONSE STRICTEMENT sous la forme d'un objet JSON valide contenant les clés :
{{
  "strategic_summary": "Une analyse synthétique claire de 3-4 phrases en français",
  "ad_copy_ideas": [
    {{"hook": "Accroche 1", "angle": "Angle 1", "cta": "Appel à l'action 1"}},
    {{"hook": "Accroche 2", "angle": "Angle 2", "cta": "Appel à l'action 2"}}
  ],
  "whatsapp_sales_script": {{
    "welcome": "Message d'accueil WhatsApp",
    "follow_up_2h": "Relance 2h",
    "closing": "Script de closing"
  }},
  "market_insights": {{
    "characteristics": "Résumé du marché",
    "advice": "Conseil spécifique"
  }}
}}
Ne mets aucun texte avant ou après le JSON.
"""

    @classmethod
    def _call_grok_llm(
        cls,
        form: SimulationInputSchema,
        prescription: PrescriptionOutputSchema,
        projections: ProjectionOutputSchema,
        city_insights: Dict[str, Any],
        api_key: str,
    ) -> Optional[AIEnrichmentSchema]:
        """Invoque l'API Grok (xAI) pour générer un enrichissement contextuel rédigé par LLM."""
        base_url = (settings.GROK_API_BASE or "https://api.x.ai/v1").rstrip("/")
        url = f"{base_url}/chat/completions"
        prompt = cls._get_prompt_text(form, prescription, projections, city_insights)

        payload = {
            "model": settings.GROK_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es un assistant IA spécialisé en conseils marketing et media planning publicitaire. Réponds toujours en JSON valide.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "stream": False,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    res_data = json.loads(response.read().decode("utf-8"))
                    choices = res_data.get("choices", [])
                    if choices:
                        text_content = choices[0]["message"]["content"]
                        cleaned_json = cls._clean_json_response(text_content)
                        parsed_json = json.loads(cleaned_json)

                        ad_copy_ideas = [
                            AdCopyIdeaSchema(**item) for item in parsed_json.get("ad_copy_ideas", [])
                        ]
                        sales_script = WhatsAppSalesScriptSchema(
                            **parsed_json.get("whatsapp_sales_script", {})
                        )

                        return AIEnrichmentSchema(
                            strategic_summary=parsed_json.get("strategic_summary", ""),
                            ad_copy_ideas=ad_copy_ideas,
                            whatsapp_sales_script=sales_script,
                            market_insights=parsed_json.get("market_insights", city_insights),
                            provider_used="grok_llm",
                        )
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            logger.warning(f"Détail erreur HTTP Grok xAI ({e.code}): {err_body}")
            raise Exception(f"HTTP {e.code}: {err_body}")
        return None

    @classmethod
    def _call_gemini_llm(
        cls,
        form: SimulationInputSchema,
        prescription: PrescriptionOutputSchema,
        projections: ProjectionOutputSchema,
        city_insights: Dict[str, Any],
    ) -> Optional[AIEnrichmentSchema]:
        """Invoque l'API Gemini pour générer un enrichissement contextuel rédigé par LLM."""
        model_name = settings.GEMINI_MODEL
        model_path = model_name if model_name.startswith("models/") else f"models/{model_name}"
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={settings.GEMINI_API_KEY}"

        prompt = cls._get_prompt_text(form, prescription, projections, city_insights)

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"},
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=8) as response:
            if response.status == 200:
                res_data = json.loads(response.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if candidates:
                    text_content = candidates[0]["content"]["parts"][0]["text"]
                    cleaned_json = cls._clean_json_response(text_content)
                    parsed_json = json.loads(cleaned_json)

                    ad_copy_ideas = [
                        AdCopyIdeaSchema(**item) for item in parsed_json.get("ad_copy_ideas", [])
                    ]
                    sales_script = WhatsAppSalesScriptSchema(
                        **parsed_json.get("whatsapp_sales_script", {})
                    )

                    return AIEnrichmentSchema(
                        strategic_summary=parsed_json.get("strategic_summary", ""),
                        ad_copy_ideas=ad_copy_ideas,
                        whatsapp_sales_script=sales_script,
                        market_insights=parsed_json.get("market_insights", city_insights),
                        provider_used="gemini_llm",
                    )
        return None
