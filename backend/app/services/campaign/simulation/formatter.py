"""Service de mise en forme commerciale et lisible des résultats de simulation LIYANZA."""
from app.schemas.simulation import SimulationResponseSchema


class SimulationFormatter:
    """Transforme la réponse technique Pydantic en rapport commercial clair et exploitable."""

    @classmethod
    def format_text_report(cls, response: SimulationResponseSchema) -> str:
        inp = response.input_summary
        pres = response.prescription
        proj = response.projections

        daily_budget = inp.total_budget_fcfa / inp.duration_days

        lines = [
            "================================================================================",
            " 📊 LIYANZA — RAPPORT DE PRESCRIPTION & PROJECTION COMMERCIALE",
            "================================================================================",
            "",
            "🎯 1. SYNTHÈSE DU PROFIL COMMERCIALE",
            f"  • Ville ciblée              : {inp.target_zone}",
            f"  • Durée de la campagne      : {inp.duration_days} jours",
            f"  • Budget publicitaire total : {inp.total_budget_fcfa:,.0f} FCFA ({daily_budget:,.0f} FCFA / jour)",
            f"  • Panier moyen par client   : {inp.average_basket_fcfa:,.0f} FCFA",
            f"  • Tranche d'âge ciblée      : {inp.audience.age_range} ans ({inp.audience.gender.value})",
            f"  • Centres d'intérêt         : {', '.join(inp.audience.interests) if inp.audience.interests else 'Général'}",
            "",
            "--------------------------------------------------------------------------------",
            " 💡 2. ALLOCATION RECOMMANDÉE DU BUDGET",
            "--------------------------------------------------------------------------------",
            f"  🔹 Meta Ads (Notoriété & Retargeting) : {pres.meta_ads_allocation.budget_fcfa:,.0f} FCFA ({pres.meta_ads_allocation.budget_percentage:.1f}%)"
            f" — [{pres.meta_ads_allocation.daily_budget_fcfa:,.0f} FCFA/j]",
            f"  🔹 Click-to-WhatsApp (Ventes directes) : {pres.whatsapp_ads_allocation.budget_fcfa:,.0f} FCFA ({pres.whatsapp_ads_allocation.budget_percentage:.1f}%)"
            f" — [{pres.whatsapp_ads_allocation.daily_budget_fcfa:,.0f} FCFA/j]",
            "",
        ]

        if pres.operational_bottleneck_detected:
            lines.extend([
                "  ⚠️ ALERTE CAPACITÉ COMMERCIAL :",
                f"     Votre équipe peut traiter au maximum {inp.daily_lead_capacity} prospects/jour (soit {pres.max_supported_leads} leads max sur {inp.duration_days} jours).",
                "     Pour éviter de gaspiller votre budget dans des messages non traités, le budget WhatsApp",
                "     a été automatiquement plafonné et le reliquat est réinvesti sur Meta Ads.",
                "",
            ])

        lines.extend([
            "  ⏰ MEILLEURS CRÉNEAUX DE DIFFUSION :",
        ])
        for slot in pres.recommended_time_slots:
            lines.append(f"     • {slot.start_time} - {slot.end_time} : {slot.rationale}")

        lines.extend([
            "",
            "  📱 FORMATS PUBLICITAIRES RECOMMANDÉS :",
        ])
        for fmt in pres.recommended_formats:
            lines.append(f"     • [{fmt.channel}] {fmt.format_name} : {fmt.description}")

        lines.extend([
            "",
            "--------------------------------------------------------------------------------",
            " 📈 3. PROJECTIONS ET IMPACT SUR VOTRE CHIFFRE D'AFFAIRES",
            "--------------------------------------------------------------------------------",
            "  👥 Visibilité & Portée :",
            f"     • Nombre de personnes touchées : {proj.reach_min:,} à {proj.reach_max:,} personnes",
            f"     • Affichages totaux (Impressions) : {proj.expected_impressions:,} vues",
            "",
            "  💬 Prospects & Conversations :",
            f"     • Contacts WhatsApp qualifiés générés : ~{proj.expected_leads:,} prospects",
            "",
            "  🛍️ Ventes & Chiffre d'Affaires Estimatifs :",
            f"     • Estimation des ventes      : {proj.expected_sales_mean} ventes (Fourchette : {proj.expected_sales_min} à {proj.expected_sales_max})",
            f"     • Chiffre d'Affaires estimé  : {proj.expected_revenue_fcfa_mean:,.0f} FCFA (Fourchette : {proj.expected_revenue_fcfa_min:,.0f} à {proj.expected_revenue_fcfa_max:,.0f} FCFA)",
            "",
            "  💶 Indicateurs de Rentabilité (KPIs Clés) :",
            f"     • Coût d'Acquisition Client (CAC) : {proj.cost_per_acquisition_fcfa:,.0f} FCFA par client",
            f"     • Retour sur Investissement (ROAS) : x {proj.roas_mean:.1f}",
            f"       👉 Pour chaque 1 000 FCFA investi en pub, vous générez environ {proj.roas_mean * 1000:,.0f} FCFA de CA.",
            "",
            f"  🎯 Indice de confiance statistique du modèle : {proj.confidence_score * 100:.0f}% (Haute fiabilité)",
            "================================================================================",
        ])

        return "\n".join(lines)
