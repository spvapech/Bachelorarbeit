"""
Statistical Enrichment Utilities
Automatically adds statistical validation metadata to analysis results.
"""

from typing import Dict, Any, List, Optional
from services.statistical_validator import StatisticalValidator, RiskLevel


def enrich_with_statistical_metadata(
    data: Dict[str, Any],
    sample_size: int,
    analysis_type: str = "general"
) -> Dict[str, Any]:
    """
    Enrich analysis results with statistical validation metadata.
    
    Args:
        data: Original analysis results
        sample_size: Sample size used in analysis
        analysis_type: Type of analysis (general, comparison, anova, correlation)
        
    Returns:
        Enriched data with statistical_meta field
    """
    validator = StatisticalValidator()
    assessment = validator.assess_sample_size(sample_size)
    
    data["statistical_meta"] = {
        "sample_size": sample_size,
        "risk_level": assessment.risk_level.value,
        "risk_description": assessment.risk_description,
        "ci_width_estimate": assessment.ci_width_estimate,
        "requires_nonparametric": assessment.requires_nonparametric,
        "analysis_type": analysis_type
    }
    
    # Add warnings if needed
    warnings = []
    if assessment.risk_level == RiskLevel.LIMITED:
        warnings.append({
            "severity": "high",
            "message": "Begrenzte Datenbasis: Ergebnisse mit Vorsicht interpretieren",
            "details": assessment.clt_assessment
        })
    elif assessment.risk_level == RiskLevel.CONSTRAINED:
        warnings.append({
            "severity": "medium",
            "message": "Eingeschränkte Aussagekraft: Breite Konfidenzintervalle",
            "details": assessment.power_assessment
        })
    
    if warnings:
        data["statistical_meta"]["warnings"] = warnings
    
    return data


def enrich_topic_analysis_with_metadata(
    topics_data: List[Dict[str, Any]],
    total_sample_size: int
) -> List[Dict[str, Any]]:
    """
    Enrich topic analysis results with per-topic statistical metadata.
    
    Each topic gets its own risk assessment based on its sample size.
    
    Args:
        topics_data: List of topic analysis results
        total_sample_size: Total reviews analyzed
        
    Returns:
        Enriched topics with statistical_meta for each
    """
    validator = StatisticalValidator()
    
    enriched_topics = []
    for topic in topics_data:
        enriched_topic = topic.copy()
        
        # Get topic-specific sample size
        # Check for frequency first (used by analyze_topic), then other field names
        topic_n = topic.get("frequency", 0) or topic.get("count", 0) or topic.get("review_count", 0) or 0
        
        if topic_n > 0:
            assessment = validator.assess_sample_size(topic_n)
            
            enriched_topic["statistical_meta"] = {
                "sample_size": topic_n,
                "risk_level": assessment.risk_level.value,
                "risk_description": assessment.risk_description,
                "ci_width_estimate": assessment.ci_width_estimate,
                "share_of_total": round((topic_n / total_sample_size) * 100, 1) if total_sample_size > 0 else 0
            }
            
            # Add topic-specific warnings
            if assessment.risk_level == RiskLevel.LIMITED:
                enriched_topic["statistical_meta"]["warning"] = (
                    f"Nur {topic_n} Reviews - statistische Aussagekraft begrenzt"
                )
        
        enriched_topics.append(enriched_topic)
    
    return enriched_topics


def enrich_comparison_with_metadata(
    data: Dict[str, Any],
    n1: int,
    n2: int,
    group1_label: str = "Gruppe 1",
    group2_label: str = "Gruppe 2"
) -> Dict[str, Any]:
    """
    Enrich group comparison results with statistical metadata.
    
    Args:
        data: Original comparison results
        n1: Size of group 1
        n2: Size of group 2
        group1_label: Label for group 1
        group2_label: Label for group 2
        
    Returns:
        Enriched data with comparison_meta field
    """
    validator = StatisticalValidator()
    comparison = validator.assess_comparison(n1, n2, "two_group")
    
    data["comparison_meta"] = {
        "groups": {
            group1_label: {
                "n": n1,
                "risk_level": comparison["group1"]["risk_level"],
                "risk_description": comparison["group1"]["risk_description"]
            },
            group2_label: {
                "n": n2,
                "risk_level": comparison["group2"]["risk_level"],
                "risk_description": comparison["group2"]["risk_description"]
            }
        },
        "overall_risk": comparison["overall_risk"],
        "notes": comparison["notes"]
    }
    
    # Add warnings for unbalanced groups
    if abs(n1 - n2) > max(n1, n2) * 0.5:  # More than 50% difference
        data["comparison_meta"]["warning"] = (
            f"Ungleiche Gruppengrößen ({n1} vs {n2}) - "
            "kleinere Gruppe limitiert Aussagekraft"
        )
    
    return data


def get_methodological_notes(
    sample_size: int,
    analysis_type: str = "general"
) -> List[str]:
    """
    Get methodological notes for documentation/reporting.
    
    Args:
        sample_size: Sample size used
        analysis_type: Type of analysis
        
    Returns:
        List of methodological notes to include in reports
    """
    validator = StatisticalValidator()
    assessment = validator.assess_sample_size(sample_size)
    
    notes = [
        f"Stichprobengröße: n={sample_size} ({assessment.risk_description})",
        f"Geschätzte Margin of Error: ±{assessment.ci_width_estimate}★ (95% CI)",
    ]
    
    # Add key recommendations
    notes.extend(assessment.recommendations[:3])
    
    # Analysis-specific notes
    if analysis_type == "comparison":
        notes.append(
            "Effektstärken (Cohen's d) und Konfidenzintervalle werden zusätzlich zu p-Werten berichtet"
        )
    elif analysis_type == "anova":
        notes.append(
            "Bei ungleicher Topic-Verteilung sinkt die Power für kleinere Gruppen"
        )
    
    return notes


def should_use_nonparametric(sample_size: int) -> bool:
    """
    Quick check if non-parametric tests should be preferred.
    
    Args:
        sample_size: Sample size to check
        
    Returns:
        True if non-parametric tests strongly recommended
    """
    validator = StatisticalValidator()
    return sample_size < validator.HEURISTIC_CLT


def get_ui_badge_config(risk_level: str) -> Dict[str, str]:
    """
    Get UI badge configuration for risk level display.
    
    Args:
        risk_level: Risk level (limited/constrained/acceptable/solid)
        
    Returns:
        Dict with color, icon, and label for UI display
    """
    configs = {
        "limited": {
            "color": "red",
            "icon": "⚠️",
            "label": "Begrenzte Datenbasis",
            "description": "Statistische Aussagekraft eingeschränkt"
        },
        "constrained": {
            "color": "orange",
            "icon": "⚡",
            "label": "Eingeschränkte Aussagekraft",
            "description": "Moderate statistische Robustheit"
        },
        "acceptable": {
            "color": "yellow",
            "icon": "✓",
            "label": "Akzeptable Basis",
            "description": "Gute statistische Basis"
        },
        "solid": {
            "color": "green",
            "icon": "✓✓",
            "label": "Solide Datenbasis",
            "description": "Robuste statistische Grundlage"
        }
    }
    
    return configs.get(risk_level, configs["limited"])


# Example usage
if __name__ == "__main__":
    # Example: Enrich topic analysis
    sample_topics = [
        {"name": "Work-Life Balance", "count": 45, "avg_rating": 3.2},
        {"name": "Gehalt", "count": 28, "avg_rating": 2.8},
        {"name": "Karriere", "count": 15, "avg_rating": 3.5}
    ]
    
    enriched = enrich_topic_analysis_with_metadata(sample_topics, total_sample_size=88)
    
    print("Enriched Topic Analysis:")
    for topic in enriched:
        print(f"\n{topic['name']}:")
        print(f"  Count: {topic['count']}")
        print(f"  Risk: {topic['statistical_meta']['risk_description']}")
        if 'warning' in topic['statistical_meta']:
            print(f"  ⚠️  {topic['statistical_meta']['warning']}")
