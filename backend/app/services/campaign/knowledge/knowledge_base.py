"""Base de connaissances structurée du commerce retail en Afrique Centrale (Zone FCFA).

Fournit des règles métier, des hooks publicitaires sectoriels, des insights géographiques
et des scripts de conversion WhatsApp réutilisables ou alimentant le context LLM.
"""
import re
from typing import Dict, List, Any


class KnowledgeBase:
    """Gestionnaire de la base de connaissances Retail & Media Planning Afrique Centrale."""


    SECTOR_HOOKS: Dict[str, List[Dict[str, str]]] = {
        "mode": [
            {
                "hook": "🔥 Arrivage exclusif à {target_zone} ! Style tendance à prix imbattable.",
                "angle": "Nouveauté & Rareté",
                "cta": "Commander sur WhatsApp",
            },
            {
                "hook": "Ne payez qu'à la livraison à {target_zone} 🚚 ! Essayez avant d'adopter.",
                "angle": "Rassurance & Sécurité",
                "cta": "Voir le catalogue WhatsApp",
            },
        ],
        "beaute": [
            {
                "hook": "Révélez votre éclat naturel ✨. Produit certifié disponible immédiatement à {target_zone}.",
                "angle": "Qualité & Preuve sociale",
                "cta": "Discuter avec notre conseillère",
            },
            {
                "hook": "Stock limité ! Offre spéciale valide uniquement cette semaine à {target_zone}.",
                "angle": "Urgence & Rareté",
                "cta": "Réserver mon pack sur WhatsApp",
            },
        ],
        "tech": [
            {
                "hook": "📱 Les meilleurs smartphones & accessoires garantis à {target_zone} !",
                "angle": "Garantie & Performance",
                "cta": "Vérifier la disponibilité sur WhatsApp",
            },
            {
                "hook": "Livraison express en 2h chrono à {target_zone}. Paiement à la réception.",
                "angle": "Rapidité & Commodité",
                "cta": "Passer commande direct",
            },
        ],
        "default": [
            {
                "hook": "👉 Offre spéciale réservée aux clients de {target_zone} !",
                "angle": "Ciblage Local",
                "cta": "En savoir plus sur WhatsApp",
            },
            {
                "hook": "Qualité supérieure garantie avec livraison rapide à {target_zone} 🚚",
                "angle": "Rassurance",
                "cta": "Contactez-nous sur WhatsApp",
            },
        ],
    }

    CITY_INSIGHTS: Dict[str, Dict[str, Any]] = {
        "douala": {
            "name": "Douala",
            "characteristics": "Capitale économique dynamique. Audience très réactive aux publicités vidéo courtes et carrousels. Réponse WhatsApp rapide indispensable (< 15 min).",
            "peak_buying_periods": "Du 25 au 5 du mois (période de paie) et les fins de semaine.",
            "preferred_payment_methods": "Orange Money, MTN Mobile Money, Paiement à la livraison",
        },
        "yaounde": {
            "name": "Yaoundé",
            "characteristics": "Capitale administrative. Audience attentive aux détails de qualité et aux garanties. Décisions d'achat légèrement plus réfléchies.",
            "peak_buying_periods": "Mid-mois et périodes de paie (25-30 du mois).",
            "preferred_payment_methods": "Paiement à la livraison, MTN Mobile Money, Orange Money",
        },
        "bafoussam": {
            "name": "Bafoussam",
            "characteristics": "Hub commercial de l'Ouest. Forte sensibilité au rapport qualité/prix. Rassurance nécessaire sur la livraison.",
            "peak_buying_periods": "Jours de marché et week-ends.",
            "preferred_payment_methods": "Paiement à la livraison, Mobile Money",
        },
        "default": {
            "name": "Zone Régionale",
            "characteristics": "Marché local dynamique. Forte préférence pour le contact humain direct sur WhatsApp et le paiement à la livraison.",
            "peak_buying_periods": "Fin de mois et jours de paie.",
            "preferred_payment_methods": "Paiement cash à la livraison, Mobile Money",
        },
    }

    WHATSAPP_CLOSING_SCRIPTS: Dict[str, Dict[str, str]] = {
        "welcome": (
            "Bonjour 👋 ! Merci d'avoir contacté notre boutique.\n"
            "Nous avons bien reçu votre demande concernant nos produits.\n"
            "Voici nos modèles actuellement disponibles avec livraison rapide à {target_zone} 👇\n"
            "Lequel préférez-vous ?"
        ),
        "follow_up_2h": (
            "Bonjour ! Avez-vous pu faire votre choix ? 😊\n"
            "Il nous reste quelques pièces en stock pour la livraison d'aujourd'hui à {target_zone}."
        ),
        "closing": (
            "Parfait ! Pour valider votre commande et programmer la livraison à {target_zone} :\n"
            "1️⃣ Votre Nom complet\n"
            "2️⃣ Quartier / Repère de livraison\n"
            "3️⃣ Numéro de téléphone pour le livreur\n"
            "Paiement à la livraison après vérification du colis 📦 !"
        ),
    }

    @classmethod
    def get_sector_key(cls, interests: List[str]) -> str:
        """Détermine la catégorie sectorielle à partir des centres d'intérêt ciblés."""
        interests_lower = " ".join([i.lower() for i in interests])
        if any(w in interests_lower for w in ["mode", "chaussure", "vêtement", "sneaker", "sac", "accessoire"]):
            return "mode"
        if any(w in interests_lower for w in ["beauté", "cosmétique", "soin", "parfum", "cheveux"]):
            return "beaute"
        if any(w in interests_lower for w in ["tech", "téléphone", "smartphone", "électronique", "gadget"]):
            return "tech"
        return "default"

    @classmethod
    def get_city_insights(cls, target_zone: str) -> Dict[str, Any]:
        """Récupère les insights comportementaux pour une ville donnée."""
        zone_clean = target_zone.strip().lower()
        zone_clean = re.sub(r"[éèêë]", "e", zone_clean)
        zone_clean = re.sub(r"[àâä]", "a", zone_clean)
        return cls.CITY_INSIGHTS.get(zone_clean, cls.CITY_INSIGHTS["default"])

    @classmethod
    def get_hooks(cls, sector_key: str, target_zone: str) -> List[Dict[str, str]]:
        """Génère des accroches formattées avec la zone ciblée."""
        templates = cls.SECTOR_HOOKS.get(sector_key, cls.SECTOR_HOOKS["default"])
        formatted_hooks = []
        for t in templates:
            formatted_hooks.append({
                "hook": t["hook"].format(target_zone=target_zone),
                "angle": t["angle"],
                "cta": t["cta"],
            })
        return formatted_hooks

    @classmethod
    def get_whatsapp_scripts(cls, target_zone: str) -> Dict[str, str]:
        """Retourne les scripts de conversion WhatsApp personnalisés par zone."""
        return {
            key: script.format(target_zone=target_zone)
            for key, script in cls.WHATSAPP_CLOSING_SCRIPTS.items()
        }
