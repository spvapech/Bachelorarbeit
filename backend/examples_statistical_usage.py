"""
Practical Examples: Statistical Validation in Action
Demonstriert reale Anwendungsfälle der statistischen Validierung.
"""

from services.statistical_validator import StatisticalValidator
from services.statistical_enrichment import (
    enrich_topic_analysis_with_metadata,
    enrich_comparison_with_metadata,
    get_ui_badge_config,
    get_methodological_notes
)


def example_1_topic_analysis():
    """
    Beispiel 1: Topic-Analyse mit statistischer Bewertung
    Use Case: Analysiere Topics in Employee-Reviews
    """
    print("\n" + "=" * 80)
    print("BEISPIEL 1: Topic-Analyse mit statistischer Validierung")
    print("=" * 80)
    
    # Simuliere Topic-Analyse Ergebnisse
    topics = [
        {
            "name": "Work-Life Balance",
            "count": 45,
            "avg_rating": 3.2,
            "sentiment": "mixed",
            "trend": "stable"
        },
        {
            "name": "Gehalt & Benefits",
            "count": 28,
            "avg_rating": 2.8,
            "sentiment": "negative",
            "trend": "declining"
        },
        {
            "name": "Karriere",
            "count": 15,
            "avg_rating": 3.5,
            "sentiment": "positive",
            "trend": "improving"
        },
        {
            "name": "Führungskultur",
            "count": 52,
            "avg_rating": 2.9,
            "sentiment": "negative",
            "trend": "stable"
        }
    ]
    
    total_reviews = 88
    
    # Anreichern mit statistischen Metadaten
    enriched_topics = enrich_topic_analysis_with_metadata(topics, total_reviews)
    
    print(f"\nGesamt-Reviews: {total_reviews}")
    print("\nTopic-Übersicht mit statistischer Bewertung:\n")
    
    for topic in enriched_topics:
        meta = topic['statistical_meta']
        badge = get_ui_badge_config(meta['risk_level'])
        
        print(f"📊 {topic['name']}")
        print(f"   Bewertung: {topic['avg_rating']}★ | Reviews: {topic['count']} ({meta['share_of_total']}%)")
        print(f"   {badge['icon']} {badge['label']}")
        print(f"   CI-Breite: ±{meta['ci_width_estimate']}★")
        
        if 'warning' in meta:
            print(f"   ⚠️  {meta['warning']}")
        
        print()
    
    print("\n💡 Interpretation:")
    print("   - Work-Life Balance & Führungskultur: Aussagekräftigere Basis (n>40)")
    print("   - Gehalt: Eingeschränkte Aussagekraft (n=28)")
    print("   - Karriere: Vorsicht geboten (n=15) - Trend möglicherweise nicht belastbar")


def example_2_employee_vs_candidate():
    """
    Beispiel 2: Vergleich Mitarbeiter vs. Bewerber
    Use Case: Sind Mitarbeiter-Reviews kritischer als Bewerber-Reviews?
    """
    print("\n" + "=" * 80)
    print("BEISPIEL 2: Mitarbeiter vs. Bewerber Vergleich")
    print("=" * 80)
    
    # Simuliere Vergleichsdaten
    employee_data = {
        "n": 85,
        "avg_rating": 3.2,
        "std": 1.1,
        "negative_share": 28
    }
    
    candidate_data = {
        "n": 45,
        "avg_rating": 3.8,
        "std": 0.9,
        "negative_share": 15
    }
    
    # Statistische Bewertung
    validator = StatisticalValidator()
    
    print(f"\n👥 Mitarbeiter: n={employee_data['n']}, ⭐ {employee_data['avg_rating']}")
    employee_assessment = validator.assess_sample_size(employee_data['n'])
    print(f"   {get_ui_badge_config(employee_assessment.risk_level.value)['icon']} "
          f"{employee_assessment.risk_description}")
    print(f"   CI-Breite: ±{employee_assessment.ci_width_estimate}★")
    
    print(f"\n🎯 Bewerber: n={candidate_data['n']}, ⭐ {candidate_data['avg_rating']}")
    candidate_assessment = validator.assess_sample_size(candidate_data['n'])
    print(f"   {get_ui_badge_config(candidate_assessment.risk_level.value)['icon']} "
          f"{candidate_assessment.risk_description}")
    print(f"   CI-Breite: ±{candidate_assessment.ci_width_estimate}★")
    
    # Vergleichsanalyse
    comparison_result = {"difference": 0.6}
    enriched = enrich_comparison_with_metadata(
        comparison_result,
        employee_data['n'],
        candidate_data['n'],
        "Mitarbeiter",
        "Bewerber"
    )
    
    print(f"\n📊 Vergleich:")
    print(f"   Differenz: {comparison_result['difference']}★ (Bewerber besser)")
    print(f"   Overall Risk: {enriched['comparison_meta']['overall_risk']}")
    
    if 'warning' in enriched['comparison_meta']:
        print(f"   ⚠️  {enriched['comparison_meta']['warning']}")
    
    print("\n💡 Empfehlung:")
    print("   - Effektstärke (Cohen's d) berechnen und berichten")
    print("   - Mann-Whitney-U Test als Sensitivitätsanalyse")
    print("   - Bewerber-Gruppe limitiert Gesamtaussagekraft (n=45)")


def example_3_small_sample_warning():
    """
    Beispiel 3: Kleine Stichprobe - Warnung und Empfehlungen
    Use Case: Neues Unternehmen mit wenigen Reviews
    """
    print("\n" + "=" * 80)
    print("BEISPIEL 3: Kleine Stichprobe - Kritische Bewertung")
    print("=" * 80)
    
    n = 18
    
    validator = StatisticalValidator()
    assessment = validator.assess_sample_size(n)
    
    print(f"\n⚠️  WARNUNG: Nur {n} Reviews verfügbar")
    print(f"\nRisiko-Einschätzung: {assessment.risk_level.value.upper()}")
    print(f"UI-Label: {assessment.risk_description}")
    
    print(f"\n📐 Statistische Kennzahlen:")
    print(f"   - Konfidenzintervall-Breite: ±{assessment.ci_width_estimate}★")
    print(f"   - CLT-Bewertung: {assessment.clt_assessment[:100]}...")
    print(f"   - Power-Bewertung: {assessment.power_assessment[:100]}...")
    
    print(f"\n✅ Methodische Empfehlungen:")
    for i, rec in enumerate(assessment.recommendations, 1):
        print(f"   {i}. {rec}")
    
    print("\n💡 Dashboard-Empfehlung:")
    print("   ⚠️  Prominent anzeigen: 'Begrenzte Datenbasis - Interpretation mit Vorsicht'")
    print("   📊 Nur deskriptive Statistiken anzeigen (Median, IQR)")
    print("   🚫 Keine Signifikanztests durchführen")
    print("   📈 Trend-Analysen NICHT anzeigen")


def example_4_anova_topic_distribution():
    """
    Beispiel 4: ANOVA für Topic-Vergleiche
    Use Case: Sind Bewertungen zwischen Topics signifikant verschieden?
    """
    print("\n" + "=" * 80)
    print("BEISPIEL 4: ANOVA für Topic-Vergleiche (k=13 Topics)")
    print("=" * 80)
    
    # Simuliere Topic-Verteilung
    total_reviews = 390
    k_topics = 13
    
    validator = StatisticalValidator()
    anova_assessment = validator.assess_comparison(total_reviews, k_topics, "anova")
    
    print(f"\n📊 ANOVA-Setup:")
    print(f"   Gesamt-Reviews: {anova_assessment['total_n']}")
    print(f"   Anzahl Topics: {anova_assessment['k_groups']}")
    print(f"   Durchschnitt pro Topic: {anova_assessment['avg_per_group']}")
    
    assessment = anova_assessment['assessment']
    print(f"\n📈 Statistische Bewertung:")
    print(f"   Risk Level: {assessment['risk_level']}")
    print(f"   Beschreibung: {assessment['risk_description']}")
    print(f"   CI-Breite: ±{assessment['ci_width_estimate']}★")
    
    print(f"\n📝 ANOVA-Spezifische Hinweise:")
    for note in anova_assessment['notes']:
        print(f"   • {note}")
    
    # Zeige ungleiche Verteilung
    print("\n⚠️  Simulation: Ungleiche Topic-Verteilung")
    topic_sizes = [65, 52, 45, 38, 35, 30, 28, 25, 22, 18, 15, 10, 7]
    print(f"   Topic-Größen: {topic_sizes}")
    print(f"   → Größtes Topic: n={max(topic_sizes)} (robust)")
    print(f"   → Kleinstes Topic: n={min(topic_sizes)} (begrenzt)")
    print("\n💡 Konsequenz:")
    print("   - Post-hoc-Tests für kleine Topics weniger aussagekräftig")
    print("   - Kruskal-Wallis als nicht-parametrische Alternative empfohlen")


def example_5_report_generation():
    """
    Beispiel 5: Methodische Notizen für Bericht-Export
    Use Case: Generiere methodischen Abschnitt für PDF-Export
    """
    print("\n" + "=" * 80)
    print("BEISPIEL 5: Methodische Notizen für Berichts-Export")
    print("=" * 80)
    
    n = 125
    
    print(f"\n📄 Methodischer Abschnitt (n={n}):\n")
    print("-" * 80)
    
    notes = get_methodological_notes(n, "comparison")
    
    print("METHODISCHE ANMERKUNGEN ZUR STICHPROBE\n")
    
    for i, note in enumerate(notes, 1):
        print(f"{i}. {note}\n")
    
    print("-" * 80)
    
    print("\n💡 Diese Notizen können direkt in PDF-Berichte übernommen werden")
    print("   um Transparenz und wissenschaftliche Nachvollziehbarkeit zu gewährleisten.")


def example_6_ui_integration():
    """
    Beispiel 6: UI-Integration - Badge & Tooltip
    Use Case: Frontend-Entwickler möchte Risk-Level anzeigen
    """
    print("\n" + "=" * 80)
    print("BEISPIEL 6: UI-Integration - Badge Konfigurationen")
    print("=" * 80)
    
    risk_levels = ["limited", "constrained", "acceptable", "solid"]
    sample_sizes = [20, 45, 80, 150]
    
    print("\n🎨 Badge-Konfigurationen für alle Risk Levels:\n")
    
    for level, n in zip(risk_levels, sample_sizes):
        config = get_ui_badge_config(level)
        print(f"n={n:3d} → {config['icon']} {config['label']:<30s} (Farbe: {config['color']})")
        print(f"        Beschreibung: {config['description']}")
        print()
    
    print("\n💡 Frontend-Code-Beispiel (React/JSX):")
    print("""
    const StatisticalBadge = ({ riskLevel, sampleSize }) => {
        const config = {
            limited: { color: 'red', icon: '⚠️', label: 'Begrenzte Datenbasis' },
            constrained: { color: 'orange', icon: '⚡', label: 'Eingeschränkt' },
            acceptable: { color: 'yellow', icon: '✓', label: 'Akzeptabel' },
            solid: { color: 'green', icon: '✓✓', label: 'Solide Basis' }
        }[riskLevel];
        
        return (
            <Badge color={config.color}>
                {config.icon} {config.label} (n={sampleSize})
            </Badge>
        );
    };
    """)


def run_all_examples():
    """Führe alle Beispiele aus."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "PRAKTISCHE BEISPIELE" + " " * 39 + "║")
    print("║" + " " * 15 + "Statistische Validierung im Einsatz" + " " * 28 + "║")
    print("╚" + "═" * 78 + "╝")
    
    example_1_topic_analysis()
    example_2_employee_vs_candidate()
    example_3_small_sample_warning()
    example_4_anova_topic_distribution()
    example_5_report_generation()
    example_6_ui_integration()
    
    print("\n" + "=" * 80)
    print("✅ Alle Beispiele erfolgreich ausgeführt")
    print("=" * 80)
    print("\n📚 Weitere Informationen:")
    print("   - STATISTICAL_SAMPLE_SIZE_METHODOLOGY.md (Methodische Grundlagen)")
    print("   - STATISTICAL_IMPLEMENTATION.md (Technische Dokumentation)")
    print("   - test_statistical_implementation.py (Automatisierte Tests)")
    print("\n")


if __name__ == "__main__":
    run_all_examples()
