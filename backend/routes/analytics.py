"""
API routes for analytics and company data.
"""

from fastapi import APIRouter, HTTPException, Query
from database.supabase_client import get_supabase_client
from typing import Optional, List, Dict, Any, Literal
from services.topic_average_rating_service import get_topic_rating_timeseries
from services.topic_definitions import EMPLOYEE_TOPIC_DEFINITIONS, CANDIDATE_TOPIC_DEFINITIONS
from services.statistical_validator import StatisticalValidator
from services.statistical_enrichment import (
    enrich_with_statistical_metadata,
    enrich_topic_analysis_with_metadata,
    enrich_comparison_with_metadata
)
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
import html
import random

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])
supabase = get_supabase_client()


def clean_html_text(text: str) -> str:
    """
    Clean HTML entities and tags from text.
    Removes <br/>, <br>, and other HTML tags, and decodes HTML entities.
    """
    if not text or not isinstance(text, str):
        return text
    
    # Decode HTML entities (&lt; &gt; &amp; etc.)
    text = html.unescape(text)
    
    # Replace <br/>- or <br>- patterns (bullet points with br tags)
    text = re.sub(r'<br\s*/?\s*>\s*-\s*', '\n• ', text, flags=re.IGNORECASE)
    
    # Replace remaining <br/>, <br>, <br /> with newlines
    text = re.sub(r'<br\s*/?\s*>', '\n', text, flags=re.IGNORECASE)
    
    # Remove any other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up patterns like "- text -" at line boundaries (incomplete bullet points)
    text = re.sub(r'^-\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^-\s+', '• ', text, flags=re.MULTILINE)
    
    # Clean up multiple newlines (max 2 consecutive newlines)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Remove trailing dashes and whitespace from lines
    text = re.sub(r'\s+-\s*$', '', text, flags=re.MULTILINE)
    
    # Trim whitespace
    text = text.strip()
    
    return text


@router.get("/company/{company_id}/overview")
async def get_company_overview(company_id: int):
    """Get overall statistics for a company."""
    try:
        # Get candidates data
        candidates_response = supabase.table("candidates")\
            .select("durchschnittsbewertung, datum")\
            .eq("company_id", company_id)\
            .execute()
        
        # Get employee data
        employee_response = supabase.table("employee")\
            .select("durchschnittsbewertung, datum")\
            .eq("company_id", company_id)\
            .execute()
        
        candidates_data = candidates_response.data or []
        employee_data = employee_response.data or []
        
        # Calculate average score
        all_ratings = [
            float(r["durchschnittsbewertung"]) 
            for r in candidates_data + employee_data 
            if r.get("durchschnittsbewertung")
        ]
        
        avg_score = round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else 0
        
        # Calculate trend (comparing last 30 days vs previous 30 days)
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)

        def _parse_datum(d: str) -> datetime:
            dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None) if dt.tzinfo else dt

        recent_ratings = [
            float(r["durchschnittsbewertung"])
            for r in candidates_data + employee_data
            if r.get("durchschnittsbewertung") and r.get("datum")
            and _parse_datum(r["datum"]) >= thirty_days_ago
        ]

        previous_ratings = [
            float(r["durchschnittsbewertung"])
            for r in candidates_data + employee_data
            if r.get("durchschnittsbewertung") and r.get("datum")
            and sixty_days_ago <= _parse_datum(r["datum"]) < thirty_days_ago
        ]
        
        recent_avg = sum(recent_ratings) / len(recent_ratings) if recent_ratings else 0
        previous_avg = sum(previous_ratings) / len(previous_ratings) if previous_ratings else 0
        trend = round(recent_avg - previous_avg, 2)
        
        # Find most critical category
        critical_category = await get_most_critical_category(company_id)
        
        return {
            "average_score": avg_score,
            "trend": trend,
            "total_reviews": len(candidates_data) + len(employee_data),
            "candidate_reviews": len(candidates_data),
            "employee_reviews": len(employee_data),
            "most_critical": critical_category
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching company overview: {str(e)}")


@router.get("/company/{company_id}/timeline")
async def get_company_timeline(
    company_id: int,
    days: int = Query(default=365, description="Number of days to include"),
    forecast_months: int = Query(default=12, description="Number of months to forecast"),
    source: str = Query(default="all", description="Data source: 'employee', 'candidates', or 'all'")
):
    """Get timeline data for ratings over time with forecast."""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        timeline_data = []
        
        # Get candidates data (if source is 'candidates' or 'all')
        if source in ["candidates", "all"]:
            candidates_response = supabase.table("candidates")\
                .select("durchschnittsbewertung, datum")\
                .eq("company_id", company_id)\
                .gte("datum", cutoff_date.isoformat())\
                .order("datum")\
                .execute()
            
            candidates_data = candidates_response.data or []
            for item in candidates_data:
                if item.get("datum") and item.get("durchschnittsbewertung"):
                    timeline_data.append({
                        "date": item["datum"],
                        "score": float(item["durchschnittsbewertung"]),
                        "type": "candidate"
                    })
        
        # Get employee data (if source is 'employee' or 'all')
        if source in ["employee", "all"]:
            employee_response = supabase.table("employee")\
                .select("durchschnittsbewertung, datum")\
                .eq("company_id", company_id)\
                .gte("datum", cutoff_date.isoformat())\
                .order("datum")\
                .execute()
            
            employee_data = employee_response.data or []
            for item in employee_data:
                if item.get("datum") and item.get("durchschnittsbewertung"):
                    timeline_data.append({
                        "date": item["datum"],
                        "score": float(item["durchschnittsbewertung"]),
                        "type": "employee"
                    })
        
        # Sort by date
        timeline_data.sort(key=lambda x: x["date"])
        
        # Group by month for aggregation
        monthly_data = defaultdict(list)
        for item in timeline_data:
            try:
                date = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
                month_key = date.strftime("%Y-%m")
                monthly_data[month_key].append(item["score"])
            except:
                pass
        
        # Create aggregated monthly timeline
        aggregated_timeline = []
        for month_key in sorted(monthly_data.keys()):
            scores = monthly_data[month_key]
            date_obj = datetime.strptime(month_key, "%Y-%m")
            aggregated_timeline.append({
                "date": month_key,
                "date_display": date_obj.strftime("%b %Y"),
                "score": round(sum(scores) / len(scores), 2),
                "count": len(scores),
                "is_forecast": False
            })
        
        # Calculate forecast using Holt's method
        forecast_data = calculate_forecast(aggregated_timeline, forecast_months)
        
        return {
            "timeline": aggregated_timeline,
            "forecast": forecast_data,
            "total_points": len(timeline_data),
            "current_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching timeline: {str(e)}")


def _fallback_forecast_average(
    historical_data: List[Dict[str, Any]], months: int, y_values: List[float]
) -> List[Dict[str, Any]]:
    """Fallback forecast using average of historical scores (used when Holt fails)."""
    avg_score = sum(y_values) / len(y_values)
    forecast = []
    last_date = datetime.strptime(historical_data[-1]["date"], "%Y-%m")
    for i in range(1, months + 1):
        month_offset = last_date.month + i
        year_offset = (month_offset - 1) // 12
        month = ((month_offset - 1) % 12) + 1
        next_month = last_date.replace(year=last_date.year + year_offset, month=month)
        forecast.append({
            "date": next_month.strftime("%Y-%m"),
            "date_display": next_month.strftime("%b %Y"),
            "score": round(avg_score, 2),
            "is_forecast": True
        })
    return forecast


def calculate_forecast(historical_data: List[Dict[str, Any]], months: int) -> List[Dict[str, Any]]:
    """
    Calculate forecast from historical monthly data using Holt's method
    (exponential smoothing with trend). Forecasts are clamped to the rating bounds [0, 5].
    Falls back to average of historical scores if Holt fails (e.g. too little data).
    """
    if months <= 0:
        return []
    if len(historical_data) < 2:
        return []

    y_values = [point["score"] for point in historical_data]
    last_date = datetime.strptime(historical_data[-1]["date"], "%Y-%m")

    try:
        from statsmodels.tsa.holtwinters import Holt  # type: ignore[import-untyped]
        import numpy as np

        series = np.asarray(y_values, dtype=float)
        model = Holt(series)
        fit = model.fit()
        preds = fit.forecast(steps=months)
    except Exception:
        return _fallback_forecast_average(historical_data, months, y_values)

    forecast = []
    for i in range(months):
        month_offset = last_date.month + (i + 1)
        year_offset = (month_offset - 1) // 12
        month = ((month_offset - 1) % 12) + 1
        next_month = last_date.replace(year=last_date.year + year_offset, month=month)
        score = float(preds[i])
        score = max(0.0, min(5.0, score))
        forecast.append({
            "date": next_month.strftime("%Y-%m"),
            "date_display": next_month.strftime("%b %Y"),
            "score": round(score, 2),
            "is_forecast": True
        })
    return forecast


@router.get("/company/{company_id}/category-ratings")
async def get_category_ratings(company_id: int):
    """Get average ratings for each category."""
    try:
        # Get all rating columns for candidates
        candidates_response = supabase.table("candidates")\
            .select("*")\
            .eq("company_id", company_id)\
            .execute()
        
        # Get all rating columns for employees
        employee_response = supabase.table("employee")\
            .select("*")\
            .eq("company_id", company_id)\
            .execute()
        
        candidates_data = candidates_response.data or []
        employee_data = employee_response.data or []
        
        # Calculate averages for candidate categories
        candidate_categories = {}
        candidate_rating_fields = [
            col for col in (candidates_data[0].keys() if candidates_data else [])
            if col.startswith("sternebewertung_")
        ]
        
        for field in candidate_rating_fields:
            ratings = [
                float(r[field]) for r in candidates_data 
                if r.get(field) is not None
            ]
            if ratings:
                category_name = field.replace("sternebewertung_", "").replace("_", " ").title()
                candidate_categories[category_name] = round(sum(ratings) / len(ratings), 2)
        
        # Calculate averages for employee categories
        employee_categories = {}
        employee_rating_fields = [
            col for col in (employee_data[0].keys() if employee_data else [])
            if col.startswith("sternebewertung_")
        ]
        
        for field in employee_rating_fields:
            ratings = [
                float(r[field]) for r in employee_data 
                if r.get(field) is not None
            ]
            if ratings:
                category_name = field.replace("sternebewertung_", "").replace("_", " ").title()
                employee_categories[category_name] = round(sum(ratings) / len(ratings), 2)
        
        return {
            "candidate_categories": candidate_categories,
            "employee_categories": employee_categories
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching category ratings: {str(e)}")


async def get_most_critical_category(company_id: int) -> Dict[str, Any]:
    """Helper function to find the most critical (lowest rated) category."""
    try:
        category_data = await get_category_ratings(company_id)
        
        all_categories = {
            **category_data["candidate_categories"],
            **category_data["employee_categories"]
        }
        
        if not all_categories:
            return {"category": "N/A", "score": 0}
        
        lowest = min(all_categories.items(), key=lambda x: x[1])
        return {
            "category": lowest[0],
            "score": lowest[1]
        }
        
    except Exception:
        return {"category": "N/A", "score": 0}


@router.get("/company/{company_id}/reviews")
async def get_company_reviews(
    company_id: int,
    limit: int = Query(default=50, description="Maximum number of reviews to return"),
    source: Optional[str] = Query(default=None, description="Filter by source: 'candidates' or 'employee'")
):
    """Get detailed reviews for a company."""
    try:
        reviews = []
        
        if source is None or source == "candidates":
            candidates_response = supabase.table("candidates")\
                .select("*")\
                .eq("company_id", company_id)\
                .order("datum", desc=True)\
                .limit(limit if source == "candidates" else limit // 2)\
                .execute()
            
            for item in candidates_response.data or []:
                reviews.append({
                    "id": item["id"],
                    "type": "candidate",
                    "date": item.get("datum"),
                    "score": float(item.get("durchschnittsbewertung", 0)),
                    "title": item.get("titel", ""),
                    "description": item.get("stellenbeschreibung", ""),
                    "improvements": item.get("verbesserungsvorschlaege", "")
                })
        
        if source is None or source == "employee":
            employee_response = supabase.table("employee")\
                .select("*")\
                .eq("company_id", company_id)\
                .order("datum", desc=True)\
                .limit(limit if source == "employee" else limit // 2)\
                .execute()
            
            for item in employee_response.data or []:
                reviews.append({
                    "id": item["id"],
                    "type": "employee",
                    "date": item.get("datum"),
                    "score": float(item.get("durchschnittsbewertung", 0)),
                    "title": item.get("titel", ""),
                    "job_description": item.get("jobbeschreibung", ""),
                    "positive": item.get("gut_am_arbeitgeber_finde_ich", ""),
                    "negative": item.get("schlecht_am_arbeitgeber_finde_ich", ""),
                    "improvements": item.get("verbesserungsvorschlaege", "")
                })
        
        # Sort by date
        reviews.sort(key=lambda x: x.get("date") or "", reverse=True)
        
        return {
            "reviews": reviews[:limit],
            "total": len(reviews)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching reviews: {str(e)}")


@router.get("/company/{company_id}/negative-topics")
async def get_negative_topics(company_id: int):
    """Get the most mentioned negative topics."""
    try:
        # Get employee negative feedback
        employee_response = supabase.table("employee")\
            .select("schlecht_am_arbeitgeber_finde_ich, durchschnittsbewertung")\
            .eq("company_id", company_id)\
            .execute()
        
        # Get candidate improvement suggestions
        candidates_response = supabase.table("candidates")\
            .select("verbesserungsvorschlaege, durchschnittsbewertung")\
            .eq("company_id", company_id)\
            .execute()
        
        employee_data = employee_response.data or []
        candidates_data = candidates_response.data or []
        
        # Collect negative texts
        negative_texts = []
        for item in employee_data:
            if item.get("schlecht_am_arbeitgeber_finde_ich"):
                negative_texts.append(item["schlecht_am_arbeitgeber_finde_ich"])
        
        for item in candidates_data:
            if item.get("verbesserungsvorschlaege"):
                negative_texts.append(item["verbesserungsvorschlaege"])
        
        # Simple keyword analysis (can be enhanced with NLP)
        keywords = {}
        negative_keywords = [
            "gehalt", "kommunikation", "management", "work-life-balance", 
            "stress", "überstunden", "kollegen", "chef", "führung",
            "bezahlung", "karriere", "entwicklung", "atmosphäre"
        ]
        
        for text in negative_texts:
            text_lower = text.lower()
            for keyword in negative_keywords:
                if keyword in text_lower:
                    keywords[keyword] = keywords.get(keyword, 0) + 1
        
        # Sort by frequency
        sorted_topics = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "negative_topics": [
                {"topic": topic, "count": count} 
                for topic, count in sorted_topics[:10]
            ],
            "total_negative_mentions": sum(keywords.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching negative topics: {str(e)}")


@router.get("/company/{company_id}/topic-overview")
async def get_topic_overview(
    company_id: int,
    source: Optional[str] = Query(default=None, description="Filter by source: 'candidates' or 'employee'"),
    start_date: Optional[str] = Query(default=None, description="Filter reviews from this date (YYYY-MM-DD)")
):
    """
    Get topic overview data formatted for the frontend TopicOverviewCard.

    This endpoint analyzes reviews and extracts topics with their frequency,
    average rating, sentiment, and timeline data - matching the format of
    the dummy data in TopicOverviewCard.jsx.

    Args:
        company_id: Company ID to analyze
        source: Optional filter - 'candidates' for Bewerber or 'employee' for Mitarbeiter
        start_date: Optional date string (YYYY-MM-DD) to filter reviews from that date onward
    """
    try:
        # Get reviews based on source filter
        candidates_data = []
        employee_data = []

        if source is None or source == "candidates":
            candidates_query = supabase.table("candidates")\
                .select("*")\
                .eq("company_id", company_id)
            if start_date:
                candidates_query = candidates_query.gte("datum", start_date)
            candidates_data = candidates_query.execute().data or []

        if source is None or source == "employee":
            employee_query = supabase.table("employee")\
                .select("*")\
                .eq("company_id", company_id)
            if start_date:
                employee_query = employee_query.gte("datum", start_date)
            employee_data = employee_query.execute().data or []
        
        all_reviews = candidates_data + employee_data
        
        if not all_reviews:
            return {
                "topics": [],
                "total_reviews": 0,
                "message": "No reviews found for this company"
            }
        
        # Topic-Definitionen zentral in services/topic_definitions.py
        # (werden auch von der Erklärungsgenerierung genutzt)
        employee_topic_definitions = EMPLOYEE_TOPIC_DEFINITIONS
        candidate_topic_definitions = CANDIDATE_TOPIC_DEFINITIONS

        # Wähle die richtigen Topic-Definitionen basierend auf der Quelle
        if source == "employee":
            topic_definitions = employee_topic_definitions
            reviews_to_analyze = employee_data
        elif source == "candidates":
            topic_definitions = candidate_topic_definitions
            reviews_to_analyze = candidates_data
        else:
            # Wenn keine Quelle angegeben oder "alle", kombiniere beide
            topic_definitions = {**employee_topic_definitions, **candidate_topic_definitions}
            reviews_to_analyze = all_reviews
        
        # Analyze each topic
        topics_data = []
        
        for topic_name, topic_config in topic_definitions.items():
            topic_analysis = analyze_topic(
                topic_name=topic_name,
                keywords=topic_config["keywords"],
                rating_fields=topic_config["rating_fields"],
                all_reviews=reviews_to_analyze
            )
            
            if topic_analysis["frequency"] > 0:  # Only include topics that were found
                topics_data.append(topic_analysis)
        
        # Sort by frequency
        topics_data.sort(key=lambda x: x["frequency"], reverse=True)
        
        # Add IDs
        for idx, topic in enumerate(topics_data, start=1):
            topic["id"] = idx
        
        # STATISTICAL ENRICHMENT: Add statistical metadata to each topic
        total_reviews = len(reviews_to_analyze)
        enriched_topics = enrich_topic_analysis_with_metadata(topics_data, total_reviews)
        
        # Add overall statistical assessment
        result = {
            "topics": enriched_topics,
            "total_reviews": total_reviews,
            "total_topics": len(enriched_topics)
        }
        
        # Add overall statistical metadata
        result = enrich_with_statistical_metadata(
            result,
            sample_size=total_reviews,
            analysis_type="anova"
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating topic overview: {str(e)}")

#sara: topicRatingCard
@router.get("/company/{company_id}/topic-ratings-timeseries")
async def topic_ratings_timeseries(
    company_id: int,
    source: Literal["employee", "candidates"] = Query(..., description="employee or candidates"),
    granularity: Literal["month", "year"] = Query("month", description="month or year"),
    start: Optional[str] = Query(None, description="ISO date/time, e.g. 2023-01-01"),
    end: Optional[str] = Query(None, description="ISO date/time, e.g. 2024-12-31"),
):
    """
    Returns average star-ratings per topic grouped by month/year for a company.
    Output format fits a line chart: [{period: 'YYYY-MM', topicA: 3.2, ...}, ...]
    """
    try:
        return get_topic_rating_timeseries(
            source=source,
            company_id=company_id,
            granularity=granularity,
            start=start,
            end=end,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building topic ratings timeseries: {str(e)}")


def analyze_topic(
    topic_name: str,
    keywords: List[str],
    rating_fields: List[str],
    all_reviews: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze a specific topic across all reviews.
    
    Returns a dictionary matching the format expected by TopicOverviewCard.jsx
    """
    # Text fields to search
    text_fields = [
        'stellenbeschreibung', 'verbesserungsvorschlaege',  # candidates
        'jobbeschreibung', 'gut_am_arbeitgeber_finde_ich',  # employee
        'schlecht_am_arbeitgeber_finde_ich', 'titel'
    ]
    
    # Find mentions and collect data
    mentions = []
    ratings = []
    monthly_ratings = defaultdict(list)
    example_texts = []
    typical_statements = []
    review_details = []
    
    for review in all_reviews:
        # Check if topic is mentioned in text fields
        mentioned = False
        mention_texts = []
        full_review_text = []
        
        for field in text_fields:
            text = review.get(field, "")
            if text and isinstance(text, str):
                text_lower = text.lower()
                for keyword_pattern in keywords:
                    if re.search(keyword_pattern, text_lower, re.IGNORECASE):
                        mentioned = True
                        # Extract sentence containing keyword
                        sentences = re.split(r'[.!?]+', text)
                        for sentence in sentences:
                            if re.search(keyword_pattern, sentence, re.IGNORECASE) and len(sentence.strip()) > 20:
                                mention_texts.append(sentence.strip())
                                break
                        
                        # Collect full text from all relevant fields
                        full_review_text.append(f"{field}: {text}")
                        break
        
        if mentioned:
            mentions.append(review)
            
            # Determine source type (employee or candidate)
            source_type = "Mitarbeiter" if 'gut_am_arbeitgeber_finde_ich' in review else "Bewerber"
            
            # Get employee status if available
            employer_status = review.get("status", "Unbekannt")
            
            # Collect example texts with full review details
            if mention_texts:
                for text in mention_texts[:3]:
                    example_texts.append(clean_html_text(text))
                    review_details.append({
                        "id": review.get("id"),
                        "preview": clean_html_text(text),
                        "fullReview": {
                            "titel": clean_html_text(review.get("titel", "Keine Titel")),
                            "datum": review.get("datum"),
                            "durchschnittsbewertung": review.get("durchschnittsbewertung"),
                            "status": employer_status,
                            "sourceType": source_type,
                            "gut_am_arbeitgeber": clean_html_text(review.get("gut_am_arbeitgeber_finde_ich", "")),
                            "schlecht_am_arbeitgeber": clean_html_text(review.get("schlecht_am_arbeitgeber_finde_ich", "")),
                            "verbesserungsvorschlaege": clean_html_text(review.get("verbesserungsvorschlaege", "")),
                            "stellenbeschreibung": clean_html_text(review.get("stellenbeschreibung", "")),
                            "jobbeschreibung": clean_html_text(review.get("jobbeschreibung", "")),
                            # Include all star ratings
                            "ratings": {
                                "arbeitsatmosphaere": review.get("sternebewertung_arbeitsatmosphaere"),
                                "image": review.get("sternebewertung_image"),
                                "work_life_balance": review.get("sternebewertung_work_life_balance"),
                                "karriere_weiterbildung": review.get("sternebewertung_karriere_weiterbildung"),
                                "gehalt_sozialleistungen": review.get("sternebewertung_gehalt_sozialleistungen"),
                                "kollegenzusammenhalt": review.get("sternebewertung_kollegenzusammenhalt"),
                                "umwelt_sozialbewusstsein": review.get("sternebewertung_umwelt_sozialbewusstsein"),
                                "vorgesetztenverhalten": review.get("sternebewertung_vorgesetztenverhalten"),
                                "kommunikation": review.get("sternebewertung_kommunikation"),
                                "interessante_aufgaben": review.get("sternebewertung_interessante_aufgaben"),
                                "umgang_mit_aelteren_kollegen": review.get("sternebewertung_umgang_mit_aelteren_kollegen"),
                                "arbeitsbedingungen": review.get("sternebewertung_arbeitsbedingungen"),
                                "gleichberechtigung": review.get("sternebewertung_gleichberechtigung")
                            }
                        }
                    })
            
            # Collect ratings — topic-specific fields take priority.
            # Using both durchschnittsbewertung AND the specific field would
            # double-count and bias the topic average toward the overall mean.
            topic_specific = []
            for field in rating_fields:
                field_rating = review.get(field)
                if field_rating is not None:
                    try:
                        topic_specific.append(float(field_rating))
                    except (TypeError, ValueError):
                        pass

            if topic_specific:
                ratings.extend(topic_specific)
            else:
                # No topic-specific rating available — use overall avg as fallback
                avg_rating_val = review.get("durchschnittsbewertung")
                if avg_rating_val is not None:
                    try:
                        ratings.append(float(avg_rating_val))
                    except (TypeError, ValueError):
                        pass
            
            # Group by month for timeline
            date_str = review.get("datum")
            if date_str:
                try:
                    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    month_key = date.strftime("%b")
                    if avg_rating:
                        monthly_ratings[month_key].append(float(avg_rating))
                except:
                    pass
    
    # Calculate average rating
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 0.0
    
    # Determine sentiment based on rating
    if avg_rating >= 3.5:
        sentiment = "Positiv"
        color = "green"
    elif avg_rating >= 2.5:
        sentiment = "Neutral"
        color = "orange"
    else:
        sentiment = "Negativ"
        color = "red"
    
    # Create timeline data (all available months, sorted chronologically)
    timeline_data = []
    months_order = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    
    # Collect all dates from reviews to determine the full time range
    all_dates = []
    for review in mentions:
        date_str = review.get("datum")
        if date_str:
            try:
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                all_dates.append(date)
            except:
                pass
    
    if all_dates:
        # Find the earliest and latest dates
        min_date = min(all_dates)
        max_date = max(all_dates)
        
        # Generate all months between min and max date
        current_date = min_date.replace(day=1)
        end_date = max_date.replace(day=1)
        
        # Create a dictionary to store month-year combinations with their ratings
        monthly_data = defaultdict(list)
        for review in mentions:
            date_str = review.get("datum")
            avg_rating_review = review.get("durchschnittsbewertung")
            if date_str and avg_rating_review:
                try:
                    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    month_year_key = f"{months_order[date.month - 1]} {date.year}"
                    monthly_data[month_year_key].append(float(avg_rating_review))
                except:
                    pass
        
        # Generate timeline for all months in range
        while current_date <= end_date:
            month_name = months_order[current_date.month - 1]
            month_year_key = f"{month_name} {current_date.year}"
            
            if month_year_key in monthly_data and monthly_data[month_year_key]:
                month_avg = sum(monthly_data[month_year_key]) / len(monthly_data[month_year_key])
                timeline_data.append({
                    "month": month_year_key,
                    "rating": round(month_avg, 1),
                    "year": current_date.year,
                    "monthNum": current_date.month
                })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
    
    # Select typical statements (up to 13 most relevant - 3 for "Typische Aussagen" + 10 for "Beispiel-Review")
    # Score each statement by relevance instead of random selection
    def _richness_score(detail):
        """Score a review by how complete its text content is across all fields."""
        fr = detail.get("fullReview") or {}
        fields = [
            fr.get("gut_am_arbeitgeber", "") or "",
            fr.get("schlecht_am_arbeitgeber", "") or "",
            fr.get("verbesserungsvorschlaege", "") or "",
            fr.get("stellenbeschreibung", "") or "",
            fr.get("jobbeschreibung", "") or "",
        ]
        filled = sum(1 for f in fields if len(f.strip()) > 20)
        total_chars = sum(len(f) for f in fields)
        gut = fr.get("gut_am_arbeitgeber", "") or ""
        schlecht = fr.get("schlecht_am_arbeitgeber", "") or ""
        both_bonus = 15 if (len(gut.strip()) > 20 and len(schlecht.strip()) > 20) else 0
        return filled * 10 + both_bonus + min(total_chars / 100, 20)

    if review_details:
        # Score each review_detail by how "typical"/representative it is
        def score_statement(detail):
            text = detail.get("preview", "")
            text_lower = text.lower()
            score = 0.0

            # 1. Keyword density: more keyword matches = more relevant
            keyword_hits = 0
            for kw in keywords:
                keyword_hits += len(re.findall(kw, text_lower, re.IGNORECASE))
            score += keyword_hits * 10

            # 2. Ideal sentence length (40-200 chars is most readable/informative)
            length = len(text)
            if 40 <= length <= 200:
                score += 8
            elif 25 <= length <= 300:
                score += 4
            elif length > 300:
                score += 1  # too long, less "typical"
            # very short (<25) gets 0 bonus

            # 3. Penalize generic/uninformative text
            generic_patterns = [
                r'^(ja|nein|ok|gut|schlecht|nichts|keine ahnung|kein kommentar)',
                r'^(s\.?\s*o\.?|siehe oben|wie gesagt)',
                r'^[-–—•\s]*$',
            ]
            for pattern in generic_patterns:
                if re.search(pattern, text_lower.strip()):
                    score -= 15

            # 4. Bonus for substantive content (contains verbs/descriptive words)
            substantive_indicators = [
                r'\b(ist|sind|war|wurde|haben|kann|sollte|muss|finde|denke|fühle)\b',
                r'\b(sehr|besonders|leider|leicht|schwer|gut|toll|super|schlecht|mangelhaft)\b',
            ]
            for pattern in substantive_indicators:
                if re.search(pattern, text_lower):
                    score += 2

            # 5. Review richness: prioritize reviews with more filled text fields
            score += _richness_score(detail) * 0.4  # weighted: relevant but secondary to keyword match

            return score
        
        # Score and sort by relevance
        scored = [(score_statement(d), i, d) for i, d in enumerate(review_details)]
        scored.sort(key=lambda x: -x[0])  # highest score first
        
        # Deduplicate: skip statements that are too similar to already-selected ones
        selected_reviews = []
        selected_texts = []
        
        def is_too_similar(new_text, existing_texts, threshold=0.6):
            """Check if new_text is too similar to any existing text using word overlap."""
            new_words = set(new_text.lower().split())
            if len(new_words) < 3:
                return any(new_text.lower().strip() == e.lower().strip() for e in existing_texts)
            for existing in existing_texts:
                existing_words = set(existing.lower().split())
                if not existing_words or not new_words:
                    continue
                overlap = len(new_words & existing_words)
                max_len = max(len(new_words), len(existing_words))
                if max_len > 0 and overlap / max_len > threshold:
                    return True
            return False
        
        for _score, _idx, detail in scored:
            if len(selected_reviews) >= 13:
                break
            preview = detail.get("preview", "")
            # Nur Statements aufnehmen, die mindestens ein Keyword enthalten (Topic-Relevanz)
            preview_lower = preview.lower()
            has_keyword = any(re.search(kw, preview_lower, re.IGNORECASE) for kw in keywords)
            if has_keyword and not is_too_similar(preview, selected_texts):
                selected_reviews.append(detail)
                selected_texts.append(preview)
        
        # Falls nach Keyword-Filter + Dedup weniger als 13: restliche auffüllen (mit Keyword-Check)
        if len(selected_reviews) < 13:
            for _score, _idx, detail in scored:
                if len(selected_reviews) >= 13:
                    break
                if detail not in selected_reviews:
                    preview = detail.get("preview", "")
                    preview_lower = preview.lower()
                    has_keyword = any(re.search(kw, preview_lower, re.IGNORECASE) for kw in keywords)
                    if has_keyword:
                        selected_reviews.append(detail)
        
        # First 3 = relevanz-sortierte "Typische Aussagen" (bleiben stabil)
        # Ab Index 3 = "Beispiel-Review" → nach Kommentar-Reichhaltigkeit sortiert
        top_statements = selected_reviews[:3]
        example_pool = selected_reviews[3:]
        example_pool.sort(key=_richness_score, reverse=True)
        selected_reviews = top_statements + example_pool
        
        typical_statements = [detail["preview"] for detail in selected_reviews]
    else:
        typical_statements = [f"Keine spezifischen Aussagen zu {topic_name} gefunden"]
        selected_reviews = [{
            "id": None,
            "preview": typical_statements[0],
            "fullReview": None
        }]
    
    # Select one example
    example = typical_statements[0] if typical_statements else f"Thema: {topic_name}"
    if len(example) > 80:
        example = example[:77] + "..."
    
    return {
        "topic": topic_name,
        "frequency": len(mentions),
        "avgRating": avg_rating,
        "sentiment": sentiment,
        "example": example,
        "color": color,
        "timelineData": timeline_data,
        "typicalStatements": typical_statements,
        "reviewDetails": selected_reviews  # Relevanz-sortierte Reviews
    }


def extract_short_kritikpunkt(text: str, max_words: int = 4) -> str:
    """
    Extrahiert einen kurzen, sinnvollen Kritikpunkt aus einem negativen Text (2-4 Wörter).
    Fokussiert auf negative Phrasen wie "schlechte Kommunikation", "keine Wertschätzung".
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Clean text
    text = clean_html_text(text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    
    # 1. PRIORITÄT: Suche nach typischen negativen Mustern
    negative_patterns = [
        # "keine/kein X" Muster
        r'keine?\s+(\w+)',
        # "schlechte/r/s X" Muster  
        r'schlechte[rns]?\s+(\w+)',
        # "fehlende X" Muster
        r'fehlende[rns]?\s+(\w+)',
        # "mangelnde X" Muster
        r'mangelnde[rns]?\s+(\w+)',
        # "wenig X" Muster
        r'wenig\s+(\w+)',
        # "zu wenig X" Muster
        r'zu\s+wenig\s+(\w+)',
        # "kaum X" Muster
        r'kaum\s+(\w+)',
    ]
    
    # Negative Adjektive die wir behalten wollen
    negative_adjectives = {
        'schlechte', 'schlechter', 'schlechtes', 'schlecht',
        'fehlende', 'fehlender', 'fehlendes', 'fehlend',
        'mangelnde', 'mangelnder', 'mangelndes', 'mangelnd',
        'keine', 'kein', 'keiner', 'keines',
        'wenig', 'kaum', 'niedrige', 'niedriger', 'niedriges',
        'unklare', 'unklarer', 'unklares',
        'langsame', 'langsamer', 'langsames',
        'starre', 'starrer', 'starres',
        'veraltete', 'veralteter', 'veraltetes',
        'toxische', 'toxischer', 'toxisches',
    }
    
    # Wichtige Substantive für Kritik
    important_nouns = {
        'kommunikation', 'führung', 'management', 'vorgesetzte', 'chef',
        'gehalt', 'bezahlung', 'vergütung', 'wertschätzung', 'respekt',
        'transparenz', 'feedback', 'entwicklung', 'karriere', 'weiterbildung',
        'arbeitsatmosphäre', 'atmosphäre', 'klima', 'kultur', 'umgang',
        'prozesse', 'strukturen', 'entscheidungen', 'hierarchie',
        'work-life-balance', 'überstunden', 'arbeitszeit', 'druck',
        'zusammenhalt', 'teamarbeit', 'kollegen', 'mitarbeiter',
    }
    
    # Suche nach Mustern
    for pattern in negative_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match in important_nouns or len(match) > 5:
                # Finde das vollständige Match mit Adjektiv
                full_match = re.search(rf'(\w+\s+{match})', text)
                if full_match:
                    result = full_match.group(1).strip()
                    # Kapitalisiere
                    return result[0].upper() + result[1:]
    
    # 2. FALLBACK: Suche nach negativem Adjektiv + Substantiv
    words = text.split()
    for i, word in enumerate(words):
        clean_word = re.sub(r'[^\wäöüß]', '', word)
        if clean_word in negative_adjectives and i + 1 < len(words):
            next_word = re.sub(r'[^\wäöüß]', '', words[i + 1])
            if len(next_word) >= 4:
                result = f"{clean_word} {next_word}"
                return result[0].upper() + result[1:]
    
    # 3. LETZTER FALLBACK: Nimm wichtiges Substantiv allein
    for word in words:
        clean_word = re.sub(r'[^\wäöüß]', '', word)
        if clean_word in important_nouns:
            return clean_word[0].upper() + clean_word[1:]
    
    return ""
    
    return ""


@router.get("/company/{company_id}/negative-kritikpunkte")
async def get_negative_kritikpunkte(company_id: int):
    """
    Findet das negativste Topic und extrahiert 2 kurze Kritikpunkte 
    aus den schlechtesten Bewertungen.
    
    Returns:
        {
            "topic": "Führungsqualität",
            "kritikpunkte": ["schlechte Kommunikation", "keine Wertschätzung"],
            "avg_rating": 1.8,
            "negative_share_percent": 70
        }
    """
    try:
        # Hole Employee-Daten (haben meist mehr kritische Bewertungen)
        employee_response = supabase.table("employee")\
            .select("*")\
            .eq("company_id", company_id)\
            .execute()
        
        employee_data = employee_response.data or []
        
        if not employee_data:
            return {
                "topic": None,
                "kritikpunkte": [],
                "avg_rating": None,
                "negative_share_percent": None,
                "message": "Keine Bewertungen gefunden"
            }
        
        # Finde die schlechtesten Bewertungen (Rating <= 2.5)
        negative_reviews = [
            r for r in employee_data 
            if r.get("durchschnittsbewertung") and float(r["durchschnittsbewertung"]) <= 2.5
        ]
        
        # Wenn nicht genug negative, nimm die schlechtesten allgemein
        if len(negative_reviews) < 2:
            sorted_reviews = sorted(
                [r for r in employee_data if r.get("durchschnittsbewertung")],
                key=lambda x: float(x["durchschnittsbewertung"])
            )
            negative_reviews = sorted_reviews[:5]
        
        # Sortiere nach Rating (niedrigste zuerst)
        negative_reviews.sort(key=lambda x: float(x.get("durchschnittsbewertung", 5)))
        
        # Extrahiere Kritikpunkte NUR aus "schlecht_am_arbeitgeber_finde_ich"
        kritikpunkte = []
        seen_texts = set()
        
        for review in negative_reviews:
            # NUR aus schlecht_am_arbeitgeber - das ist garantiert negativ!
            text = review.get("schlecht_am_arbeitgeber_finde_ich", "")
            
            if not text or not isinstance(text, str) or len(text.strip()) < 10:
                continue
            
            # Extrahiere mehrere Sätze aus dem Text
            sentences = re.split(r'[.!?\n]+', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 15:
                    continue
                    
                kritikpunkt = extract_short_kritikpunkt(sentence, max_words=4)
                
                # Vermeide Duplikate und zu kurze Ergebnisse
                if kritikpunkt and len(kritikpunkt) >= 8 and kritikpunkt.lower() not in seen_texts:
                    kritikpunkte.append(kritikpunkt)
                    seen_texts.add(kritikpunkt.lower())
                
                if len(kritikpunkte) >= 2:
                    break
            
            if len(kritikpunkte) >= 2:
                break
        
        # Bestimme das Haupt-Topic basierend auf Keywords
        topic_keywords = {
            "Führungsqualität": ["führung", "vorgesetzte", "chef", "management", "leitung"],
            "Kommunikation": ["kommunikation", "information", "transparenz", "feedback"],
            "Gehalt & Benefits": ["gehalt", "bezahlung", "lohn", "vergütung", "benefits"],
            "Work-Life Balance": ["work-life", "überstunden", "arbeitszeit", "balance"],
            "Teamzusammenhalt": ["team", "kollegen", "zusammenhalt", "atmosphäre"],
            "Karriereentwicklung": ["karriere", "weiterbildung", "entwicklung", "aufstieg"]
        }
        
        # Zähle Keyword-Treffer in negativen Reviews
        topic_scores = defaultdict(int)
        for review in negative_reviews:
            text_fields = [
                review.get("schlecht_am_arbeitgeber_finde_ich", ""),
                review.get("verbesserungsvorschlaege", ""),
                review.get("titel", "")
            ]
            combined_text = " ".join(str(t) for t in text_fields if t).lower()
            
            for topic, keywords in topic_keywords.items():
                for keyword in keywords:
                    if keyword in combined_text:
                        topic_scores[topic] += 1
        
        # Wähle das Topic mit den meisten Treffern
        main_topic = max(topic_scores.items(), key=lambda x: x[1])[0] if topic_scores else "Allgemein"
        
        # Berechne Statistiken
        total_reviews = len(employee_data)
        negative_count = len([r for r in employee_data if r.get("durchschnittsbewertung") and float(r["durchschnittsbewertung"]) <= 2.5])
        negative_share = round((negative_count / total_reviews) * 100) if total_reviews > 0 else 0
        
        avg_rating = sum(float(r["durchschnittsbewertung"]) for r in negative_reviews if r.get("durchschnittsbewertung")) / len(negative_reviews) if negative_reviews else None
        
        return {
            "topic": main_topic,
            "kritikpunkte": kritikpunkte[:2],
            "avg_rating": round(avg_rating, 1) if avg_rating else None,
            "negative_share_percent": negative_share,
            "categories": [main_topic]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATISTICAL VALIDATION ENDPOINTS
# ============================================================================

@router.get("/statistical/validate-sample-size")
async def validate_sample_size(
    n: int = Query(..., description="Sample size to validate", ge=1)
) -> Dict[str, Any]:
    """
    Validate sample size adequacy for statistical analysis.
    
    Returns comprehensive assessment including:
    - Risk level (limited/constrained/acceptable/solid)
    - CLT approximation quality
    - Power considerations
    - Confidence interval width estimate
    - Methodological recommendations
    
    Based on established literature:
    - Rice (2006): CLT heuristic n≈30
    - Cohen (1988): Power analysis n≈64 for d=0.5
    - Maxwell et al. (2008): AIPE approach n≈100 for MoE≤±0.20
    """
    try:
        validator = StatisticalValidator()
        assessment = validator.assess_sample_size(n)
        return assessment.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistical/validate-comparison")
async def validate_comparison(
    n1: int = Query(..., description="Size of group 1 (or total n for ANOVA)", ge=1),
    n2: int = Query(..., description="Size of group 2 (or k groups for ANOVA)", ge=1),
    comparison_type: Literal["two_group", "anova"] = Query(
        "two_group", 
        description="Type of comparison: two_group (t-test) or anova"
    )
) -> Dict[str, Any]:
    """
    Validate sample sizes for group comparisons.
    
    For two_group (t-test):
    - n1, n2 = sizes of the two groups
    - Returns assessment for both groups
    
    For anova:
    - n1 = total sample size
    - n2 = number of groups (k)
    - Returns assessment based on average group size
    """
    try:
        validator = StatisticalValidator()
        assessment = validator.assess_comparison(n1, n2, comparison_type)
        return assessment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistical/validate-correlation")
async def validate_correlation(
    n: int = Query(..., description="Sample size for correlation analysis", ge=1)
) -> Dict[str, Any]:
    """
    Validate sample size for correlation analysis.
    
    Based on Schönbrodt & Perugini (2013): 
    Correlations stabilize around n≈250
    """
    try:
        validator = StatisticalValidator()
        assessment = validator.validate_correlation_stability(n)
        return assessment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{company_id}/statistical-assessment")
async def get_company_statistical_assessment(company_id: int) -> Dict[str, Any]:
    """
    Get comprehensive statistical assessment for company's review data.
    
    Includes:
    - Sample size validation for employee and candidate reviews
    - Topic-wise sample size assessment (ANOVA context)
    - Recommendations for statistical analysis
    """
    try:
        validator = StatisticalValidator()
        
        # Get employee reviews count
        employee_response = supabase.table("employee")\
            .select("id", count="exact")\
            .eq("company_id", company_id)\
            .execute()
        
        # Get candidate reviews count
        candidate_response = supabase.table("candidates")\
            .select("id", count="exact")\
            .eq("company_id", company_id)\
            .execute()
        
        employee_count = employee_response.count or 0
        candidate_count = candidate_response.count or 0
        total_count = employee_count + candidate_count
        
        # Overall assessment
        overall_assessment = validator.assess_sample_size(total_count)
        
        # Employee-specific assessment
        employee_assessment = validator.assess_sample_size(employee_count)
        
        # Candidate-specific assessment
        candidate_assessment = validator.assess_sample_size(candidate_count)
        
        # Comparison assessment (employee vs candidate)
        comparison_assessment = validator.assess_comparison(
            employee_count, 
            candidate_count, 
            "two_group"
        ) if employee_count > 0 and candidate_count > 0 else None
        
        # Topic analysis considerations (for ANOVA)
        # Assuming 13 topics as per methodology document
        k_topics = 13
        topic_assessment = validator.assess_comparison(
            total_count,
            k_topics,
            "anova"
        ) if total_count > 0 else None
        
        return {
            "company_id": company_id,
            "sample_sizes": {
                "total": total_count,
                "employee": employee_count,
                "candidate": candidate_count
            },
            "overall_assessment": overall_assessment.to_dict(),
            "employee_assessment": employee_assessment.to_dict(),
            "candidate_assessment": candidate_assessment.to_dict(),
            "comparison_assessment": comparison_assessment,
            "topic_anova_assessment": topic_assessment,
            "summary": {
                "data_quality": overall_assessment.risk_level.value,
                "can_compare_employee_candidate": employee_count >= 30 and candidate_count >= 30,
                "can_perform_topic_analysis": total_count >= (k_topics * 30),
                "primary_limitation": (
                    "Sample size below CLT heuristic - prefer non-parametric tests"
                    if total_count < validator.HEURISTIC_CLT
                    else "Power may be insufficient for small effects"
                    if total_count < validator.HEURISTIC_POWER
                    else "Confidence intervals may be wide"
                    if total_count < validator.HEURISTIC_PRECISION
                    else "Sample size adequate for robust analysis"
                )
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        raise HTTPException(status_code=500, detail=f"Error fetching negative kritikpunkte: {str(e)}")