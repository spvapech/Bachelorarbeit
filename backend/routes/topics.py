"""
API routes for LDA Topic Model functionality.
Provides endpoints for training, analyzing, and managing topic models.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from models.lda_topic_model import LDATopicAnalyzer
from services.topic_model_service import TopicModelDatabase
from services.topic_rating_service import TopicRatingAnalyzer
import os

router = APIRouter(prefix="/api/topics", tags=["Topic Modeling"])

# Global model instance
_topic_analyzer: Optional[LDATopicAnalyzer] = None
_topic_db = TopicModelDatabase()
_topic_rating_analyzer = TopicRatingAnalyzer()


class TrainModelRequest(BaseModel):
    """Request model for training LDA model."""
    source: str = Field(
        default="both", 
        description="Data source: 'candidates', 'employee', or 'both'"
    )
    num_topics: int = Field(
        default=5, 
        ge=2, 
        le=20, 
        description="Number of topics to extract"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of records to use per source"
    )
    use_employee_weighting: bool = Field(
        default=True,
        description="Whether to apply weighting based on employee type (Student, Employee, Manager, Nicht-Employee)"
    )


class PredictTopicsRequest(BaseModel):
    """Request model for predicting topics."""
    text: str = Field(..., description="Text to analyze")
    threshold: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Minimum probability threshold"
    )


class AnalyzeRecordRequest(BaseModel):
    """Request model for analyzing a specific record."""
    record_id: int = Field(..., description="ID of the record")
    source: str = Field(..., description="Source: 'candidates' or 'employee'")
    fields: Optional[List[str]] = Field(
        default=None,
        description="Specific fields to analyze"
    )


@router.get("/status")
async def get_model_status():
    """Get current model status and information."""
    global _topic_analyzer
    
    if _topic_analyzer is None:
        return {
            "status": "not_initialized",
            "message": "No model has been trained yet"
        }
    
    model_info = _topic_analyzer.get_model_info()
    return model_info


@router.get("/database/stats")
async def get_database_stats():
    """Get database statistics for topic modeling."""
    try:
        stats = _topic_db.get_statistics()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/train")
async def train_model(request: TrainModelRequest):
    """
    Train a new LDA topic model on data from the database.
    
    This endpoint fetches text data from the specified source(s) and trains
    an LDA model to discover topics.
    """
    global _topic_analyzer
    
    try:
        # Fetch text data from database with metadata if weighting is enabled
        data = _topic_db.get_all_texts(
            source=request.source,
            limit=request.limit,
            include_metadata=request.use_employee_weighting
        )
        
        if not data["texts"]:
            raise HTTPException(
                status_code=400,
                detail="No text data found in database. Please add data first."
            )
        
        # Initialize new analyzer
        _topic_analyzer = LDATopicAnalyzer(num_topics=request.num_topics)
        
        # Train model with or without metadata for weighting
        if request.use_employee_weighting and "detailed_metadata" in data:
            result = _topic_analyzer.train_model(
                data["texts"], 
                metadata=data["detailed_metadata"]
            )
        else:
            result = _topic_analyzer.train_model(data["texts"])
        
        # Add metadata
        result["data_sources"] = data["metadata"]
        result["employee_weighting_enabled"] = request.use_employee_weighting
        
        # Save model
        try:
            model_path = _topic_analyzer.save_model()
            result["model_saved"] = True
            result["model_path"] = model_path
        except Exception as e:
            result["model_saved"] = False
            result["save_error"] = str(e)
        
        return {
            "status": "success",
            "message": f"Model trained successfully on {data['metadata']['total_count']} documents",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to train model: {str(e)}"
        )


@router.get("/topics")
async def get_topics(num_words: int = 10):
    """
    Get all discovered topics with their top words.
    
    Args:
        num_words: Number of top words to return per topic (default: 10)
    """
    global _topic_analyzer
    
    if _topic_analyzer is None:
        raise HTTPException(
            status_code=400,
            detail="No model trained yet. Please train a model first."
        )
    
    try:
        topics = _topic_analyzer.get_topics(num_words=num_words)
        return {
            "status": "success",
            "num_topics": len(topics),
            "topics": topics
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get topics: {str(e)}"
        )


@router.post("/predict")
async def predict_topics(request: PredictTopicsRequest):
    """
    Predict topics for a given text.
    
    This endpoint analyzes the provided text and returns the most relevant topics
    with their probabilities.
    """
    global _topic_analyzer
    
    if _topic_analyzer is None:
        raise HTTPException(
            status_code=400,
            detail="No model trained yet. Please train a model first."
        )
    
    try:
        topics = _topic_analyzer.predict_topics(
            text=request.text,
            threshold=request.threshold
        )
        
        return {
            "status": "success",
            "text_preview": request.text[:100] + "..." if len(request.text) > 100 else request.text,
            "num_topics_found": len(topics),
            "topics": topics
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to predict topics: {str(e)}"
        )


@router.post("/analyze-record")
async def analyze_record(request: AnalyzeRecordRequest):
    """
    Analyze a specific record from the database.
    
    This endpoint fetches a record by ID and analyzes its text content
    to determine relevant topics.
    """
    global _topic_analyzer
    
    if _topic_analyzer is None:
        raise HTTPException(
            status_code=400,
            detail="No model trained yet. Please train a model first."
        )
    
    try:
        # Fetch record
        if request.source == "candidates":
            record = _topic_db.get_candidate_by_id(request.record_id)
            default_fields = ['stellenbeschreibung', 'verbesserungsvorschlaege']
        elif request.source == "employee":
            record = _topic_db.get_employee_by_id(request.record_id)
            default_fields = [
                'jobbeschreibung',
                'gut_am_arbeitgeber_finde_ich',
                'schlecht_am_arbeitgeber_finde_ich',
                'verbesserungsvorschlaege'
            ]
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid source. Must be 'candidates' or 'employee'"
            )
        
        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"Record with ID {request.record_id} not found in {request.source}"
            )
        
        # Get fields to analyze
        fields_to_analyze = request.fields if request.fields else default_fields
        
        # Combine text from specified fields
        combined_text = ' '.join([
            str(record.get(field, ''))
            for field in fields_to_analyze
            if record.get(field)
        ])
        
        if not combined_text.strip():
            return {
                "status": "no_content",
                "message": "No text content found in specified fields",
                "record_id": request.record_id,
                "source": request.source
            }
        
        # Analyze topics
        topics = _topic_analyzer.predict_topics(combined_text)
        
        # Extract company information if available
        company_info = None
        if "companies" in record and record["companies"]:
            company_info = record["companies"]
        elif "company_id" in record and record["company_id"]:
            company_info = {"id": record["company_id"]}
        
        return {
            "status": "success",
            "record_id": request.record_id,
            "source": request.source,
            "fields_analyzed": fields_to_analyze,
            "text_length": len(combined_text),
            "topics": topics,
            "record_data": {
                "titel": record.get("titel"),
                "status": record.get("status"),
                "datum": record.get("datum"),
                "company": company_info
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze record: {str(e)}"
        )


@router.get("/models/list")
async def list_saved_models():
    """List all saved model files."""
    models_dir = "models/saved_models"
    
    if not os.path.exists(models_dir):
        return {
            "status": "success",
            "models": [],
            "message": "No models directory found"
        }
    
    # Find all .model files
    model_files = [
        f.replace(".model", "")
        for f in os.listdir(models_dir)
        if f.endswith(".model")
    ]
    
    return {
        "status": "success",
        "count": len(model_files),
        "models": sorted(model_files, reverse=True)
    }


@router.post("/models/load")
async def load_saved_model(model_name: str):
    """Load a previously saved model."""
    global _topic_analyzer
    
    models_dir = "models/saved_models"
    model_path = os.path.join(models_dir, model_name)
    
    if not os.path.exists(f"{model_path}.model"):
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_name}' not found"
        )
    
    try:
        _topic_analyzer = LDATopicAnalyzer()
        metadata = _topic_analyzer.load_model(model_path)
        
        return {
            "status": "success",
            "message": f"Model '{model_name}' loaded successfully",
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load model: {str(e)}"
        )


@router.get("/analyze/employee-reviews-with-ratings")
async def analyze_employee_reviews_with_ratings(limit: Optional[int] = None):
    """
    Analyze employee reviews combining topics, sentiment analysis, and star ratings.
    
    This endpoint provides a comprehensive analysis that includes:
    - Topic modeling (LDA) on text fields
    - Sentiment analysis (positive/neutral/negative)
    - Star ratings from database
    - Correlation between topics and ratings
    
    Args:
        limit: Maximum number of reviews to analyze (optional)
    
    Returns:
        Detailed analysis with topics, sentiment, and ratings per review
    """
    if not _topic_analyzer:
        raise HTTPException(
            status_code=400,
            detail="Model not trained. Please train a model first using /api/topics/train"
        )
    
    try:
        result = _topic_rating_analyzer.analyze_employee_reviews_with_ratings(
            _topic_analyzer,
            limit=limit
        )
        
        return {
            "status": "success",
            "analysis": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/analyze/candidate-reviews-with-ratings")
async def analyze_candidate_reviews_with_ratings(limit: Optional[int] = None):
    """
    Analyze candidate reviews combining topics, sentiment analysis, and star ratings.
    
    Args:
        limit: Maximum number of reviews to analyze (optional)
    
    Returns:
        Detailed analysis with topics, sentiment, and ratings per review
    """
    if not _topic_analyzer:
        raise HTTPException(
            status_code=400,
            detail="Model not trained. Please train a model first using /api/topics/train"
        )
    
    try:
        result = _topic_rating_analyzer.analyze_candidate_reviews_with_ratings(
            _topic_analyzer,
            limit=limit
        )
        
        return {
            "status": "success",
            "analysis": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/analyze/topic-rating-correlation")
async def get_topic_rating_correlation(limit: Optional[int] = None):
    """
    Get correlation analysis between discovered topics and star ratings.
    
    This endpoint aggregates data to show:
    - Which topics appear most frequently
    - Average star ratings for each topic
    - Sentiment distribution per topic
    - Top words for each topic
    
    Args:
        limit: Maximum number of reviews to analyze (optional)
    
    Returns:
        Aggregated topic-rating correlation data
    """
    if not _topic_analyzer:
        raise HTTPException(
            status_code=400,
            detail="Model not trained. Please train a model first using /api/topics/train"
        )
    
    try:
        result = _topic_rating_analyzer.get_topic_rating_correlation(
            _topic_analyzer,
            limit=limit
        )
        
        return {
            "status": "success",
            "correlation": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/company/{company_id}/negative-topics")
async def get_negative_topics_by_company(company_id: int, limit: Optional[int] = None):
    """
    Return topics with negative sentiment for a given company id.

    Uses the TopicRatingAnalyzer company-scoped aggregation and filters topics
    where negative sentiment dominates or avg_sentiment_polarity is negative.
    """
    global _topic_analyzer, _topic_rating_analyzer

    if _topic_analyzer is None:
        return {"negative_topics": [], "company_id": company_id, "total": 0}

    try:
        result = _topic_rating_analyzer.get_topic_rating_correlation_for_company(
            _topic_analyzer,
            company_id,
            limit=limit
        )

        def negative_share(t: dict) -> float:
            s = t.get("sentiments", {}) or {}
            neg = float(s.get("negative", 0) or 0)
            pos = float(s.get("positive", 0) or 0)
            neu = float(s.get("neutral", 0) or 0)

            total = neg + pos + neu
            if total <= 0:
                total = float(t.get("mention_count", 0) or 0)
            if total <= 0:
                return 0.0
            return neg / total

        def extract_words(t: dict) -> list[str]:
            w = t.get("topic_words") or t.get("words") or t.get("keywords") or t.get("top_words") or t.get("terms") or []
            if isinstance(w, str):
                return [x.strip() for x in w.split(",") if x.strip()]
            if isinstance(w, (list, tuple)):
                out: list[str] = []
                for x in w:
                    if isinstance(x, dict):
                        word = x.get("word") or x.get("term") or x.get("label") or ""
                        if word:
                            out.append(str(word).strip())
                    elif x:
                        out.append(str(x).strip())
                return out
            return []

        # Filter negative topics: avg_sentiment_polarity < 0 or more negative mentions than positive
        negative_topics = [
            t for t in result.get('topics', [])
            if t.get('avg_sentiment_polarity', 0) < 0 or t.get('sentiments', {}).get('negative', 0) > t.get('sentiments', {}).get('positive', 0)
        ]

        # Sort by most negative (lowest avg_sentiment_polarity) then by mention_count
        negative_topics.sort(key=lambda x: (x.get('avg_sentiment_polarity', 0), -x.get('mention_count', 0)))

        # Enrich for frontend modal
        enriched = []
        for t in negative_topics:
            topic_words = extract_words(t)
            topic_words = [w for w in topic_words if w]

            # Build a concise, readable topic label
            # Prefer existing label/topic field or category, fall back to top topic words
            topic_label = None
            existing_label = t.get("topic_label") or t.get("topic") or t.get("label") or ""
            existing_label = existing_label.strip()
            if existing_label and len(existing_label) <= 30:
                topic_label = existing_label[:1].upper() + existing_label[1:]
            elif topic_words:
                # Pick the shortest meaningful word (>=4 chars) from top-3 words as label
                candidates = [w for w in topic_words[:3] if len(w) >= 4]
                if candidates:
                    best = min(candidates, key=len)
                else:
                    best = topic_words[0]
                topic_label = best[:1].upper() + best[1:]

            enriched_topic = dict(t)
            enriched_topic["topic_words"] = topic_words
            enriched_topic["topic_text"] = ", ".join(topic_words)
            enriched_topic["topic_label"] = topic_label
            enriched_topic["negative_share_percent"] = round(negative_share(t) * 100)

            # Compute kritikpunkte + betroffene Kategorien from employee reviews mentioning topic words
            try:
                kritikpunkte = extract_kritikpunkte_for_topic(company_id, topic_words, max_points=3, max_rows=200)
                categories = extract_affected_categories_for_topic(company_id, topic_words, max_categories=2, max_rows=200)
            except Exception:
                kritikpunkte = []
                categories = []

            if kritikpunkte:
                enriched_topic["kritikpunkte"] = kritikpunkte
            if categories:
                enriched_topic["categories"] = categories

            enriched.append(enriched_topic)

        return {
            "status": "success",
            "company_id": company_id,
            "negative_topics": enriched,
            "total_negative": len(enriched)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get negative topics: {str(e)}")


@router.get("/company/{company_id}/most-critical")
async def get_most_critical_topic_by_company(
    company_id: int,
    limit: Optional[int] = None,
    threshold: float = Query(
        default=3.5,
        ge=0.0,
        le=5.0,
        description="Critical threshold for topic score (avg rating). Topics below this threshold are considered critical.",
    ),
    weighting: str = Query(
        default="sqrt",
        description="Weighting strategy for volume. One of: none, sqrt, log.",
    ),
    trend_window_days: int = Query(
        default=30,
        ge=7,
        le=365,
        description="Window size (days) used for topic trend calculation (last N days vs previous N days).",
    ),
):
    """
    Return a single most critical topic for a given company id.

    Definition (robust + explainable):
        criticality = max(0, threshold - score) * weight
    where score is the topic's avg_rating and weight is derived from review volume.

    Also returns trend info (rating and negative share) comparing the last N days vs the previous N days.
    """
    global _topic_analyzer, _topic_rating_analyzer

    if _topic_analyzer is None:
        raise HTTPException(
            status_code=400,
            detail="No model trained. Please train a model first using /api/topics/train"
        )

    try:
        result = _topic_rating_analyzer.get_topic_rating_correlation_for_company(
            _topic_analyzer,
            company_id,
            limit=limit
        )

        topics = result.get("topics", []) or []
        if not topics:
            return {
                "status": "success",
                "most_critical": None
            }

        def negative_share(t: dict) -> float:
            s = t.get("sentiments", {}) or {}
            neg = float(s.get("negative", 0) or 0)
            pos = float(s.get("positive", 0) or 0)
            neu = float(s.get("neutral", 0) or 0)

            total = neg + pos + neu
            if total <= 0:
                total = float(t.get("mention_count", 0) or 0)

            if total <= 0:
                return 0.0
            return neg / total

        def review_count(t: dict) -> int:
            s = t.get("sentiments", {}) or {}
            try:
                return int((s.get("positive", 0) or 0) + (s.get("neutral", 0) or 0) + (s.get("negative", 0) or 0))
            except Exception:
                return 0

        def score_value(t: dict) -> Optional[float]:
            v = t.get("score")
            if v is None:
                v = t.get("avg_rating")
            if v is None:
                return None
            try:
                num = float(v)
            except Exception:
                return None
            if not (num == num):
                return None
            return num

        def weight_for(t: dict) -> tuple[float, int, str]:
            base = review_count(t)
            base_label = "review_count"
            if base <= 0:
                base = int(t.get("mention_count", 0) or 0)
                base_label = "mention_count"

            if base < 0:
                base = 0

            if weighting == "none":
                return 1.0, base, base_label

            if weighting == "log":
                import math
                return float(math.log1p(base)), base, base_label

            # default: sqrt
            import math
            return float(math.sqrt(base)), base, base_label

        def criticality_for(t: dict) -> tuple[float, float, float, int, str]:
            score = score_value(t)
            if score is None:
                return 0.0, 0.0, 0.0, 0, "review_count"

            shortfall = max(0.0, float(threshold) - float(score))
            w, base, base_label = weight_for(t)
            return shortfall * w, shortfall, w, base, base_label

        def extract_words(t: dict) -> list[str]:
            # Unterstützt verschiedene Feldnamen je nach Analyzer-Output
            w = t.get("words") or t.get("keywords") or t.get("top_words") or t.get("terms") or []
            if isinstance(w, str):
                return [x.strip() for x in w.split(",") if x.strip()]
            if isinstance(w, (list, tuple)):
                result = []
                for x in w:
                    if isinstance(x, dict):
                        # Extrahiere 'word' aus {'word': '...', 'weight': ...}
                        word = x.get("word") or x.get("term") or x.get("label") or ""
                        if word:
                            result.append(str(word).strip())
                    elif x:
                        result.append(str(x).strip())
                return result
            return []

        # Prefer topics with an actual rating signal; fallback to all topics if none qualify
        rated_topics = [t for t in topics if score_value(t) is not None and (t.get("ratings") or [])]
        candidate_topics = rated_topics or topics

        # If any topic is below threshold, select by maximum criticality.
        # Otherwise, select the lowest score (still the most concerning), then by volume.
        any_below = any((score_value(t) is not None and score_value(t) < threshold) for t in candidate_topics)

        if any_below:
            most = max(
                candidate_topics,
                key=lambda t: (
                    criticality_for(t)[0],
                    weight_for(t)[1],
                    negative_share(t),
                ),
            )
        else:
            most = min(
                candidate_topics,
                key=lambda t: (
                    score_value(t) if score_value(t) is not None else float("inf"),
                    -weight_for(t)[1],
                    -negative_share(t),
                ),
            )

        topic_words = extract_words(most)
        if limit is not None and isinstance(limit, int) and limit > 0:
            topic_words = topic_words[:limit]

        # topic id (robust)
        topic_id = most.get("topic_id")
        if topic_id is None:
            topic_id = most.get("topic")
        if topic_id is None:
            topic_id = most.get("id")

        # Calculate trends: compare old vs new reviews for this topic
        trend_negative = calculate_topic_trend(company_id, topic_id, topic_words, window_days=trend_window_days)
        trend_rating = calculate_topic_rating_trend(company_id, topic_words, window_days=trend_window_days)

        # build final object for frontend
        most_copy = dict(most)
        most_copy["topic_id"] = topic_id
        most_copy["topic_words"] = topic_words
        most_copy["topic_text"] = ", ".join(topic_words)  # <- das ist dein "Topic" Text
        score = score_value(most)
        crit, shortfall, w, w_base, w_base_label = criticality_for(most)

        # provide consistent score fields for frontend
        if score is not None:
            most_copy["score"] = float(score)

        most_copy["threshold"] = float(threshold)
        most_copy["shortfall"] = round(float(shortfall), 4)
        most_copy["weight"] = round(float(w), 4)
        most_copy["weight_base"] = int(w_base)
        most_copy["weight_base_label"] = str(w_base_label)
        most_copy["criticality"] = round(float(crit), 6)
        most_copy["review_count"] = int(review_count(most))
        most_copy["rating_count"] = len(most.get("ratings") or [])

        most_copy["negative_share_percent"] = round(negative_share(most) * 100)
        most_copy["trend"] = {
            "window_days": int(trend_window_days),
            "negative_share": trend_negative,
            "rating": trend_rating,
        }

        # Affected categories (for UI display)
        try:
            categories = extract_affected_categories_for_topic(company_id, topic_words, max_categories=2, max_rows=300)
        except Exception:
            categories = []
        if categories:
            most_copy["categories"] = categories

        if not any_below:
            most_copy["note"] = "No topic is currently below the configured threshold; returning the lowest-scoring topic."

        return {
            "status": "success",
            "company_id": company_id,
            "threshold": float(threshold),
            "weighting": weighting,
            "trend_window_days": int(trend_window_days),
            "most_critical": most_copy,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get most critical topic: {str(e)}"
        )


def calculate_topic_trend(company_id: int, topic_id: int, topic_words: list[str], window_days: int = 30) -> dict:
    """
    Calculate trend by comparing negative share in old vs new reviews.
    
    Returns:
        dict with 'delta' (change in negative share %), 'direction' (up/down/stable), 
        'old_negative_share', 'new_negative_share'
    """
    from database.supabase_client import get_supabase_client
    from datetime import datetime, timedelta, timezone
    
    supabase = get_supabase_client()
    
    try:
        # Define time periods: last N days vs previous N days
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=window_days)
        old_cutoff = now - timedelta(days=window_days * 2)
        
        # Fetch all employee reviews for this company
        response = supabase.table("employee")\
            .select("datum, created_at, gut_am_arbeitgeber_finde_ich, schlecht_am_arbeitgeber_finde_ich, verbesserungsvorschlaege")\
            .eq("company_id", company_id)\
            .gte("datum", old_cutoff.isoformat())\
            .execute()
        
        reviews = response.data if response.data else []
        
        if len(reviews) < 2:
            return {"delta": 0, "direction": "stable", "message": "Not enough data"}
        
        # Analyze each review for topic presence and sentiment
        # Use transformer mode for accurate trend analysis
        from models.sentiment_analyzer import SentimentAnalyzer
        sentiment_analyzer = SentimentAnalyzer(mode="transformer")
        
        old_reviews = []  # Reviews from 60-30 days ago
        new_reviews = []  # Reviews from last 30 days
        
        for review in reviews:
            review_date = datetime.fromisoformat(review.get("datum").replace("Z", "+00:00")) if review.get("datum") else datetime.fromisoformat(review.get("created_at").replace("Z", "+00:00"))
            
            # Combine text fields
            text = " ".join([
                str(review.get("gut_am_arbeitgeber_finde_ich", "")),
                str(review.get("schlecht_am_arbeitgeber_finde_ich", "")),
                str(review.get("verbesserungsvorschlaege", ""))
            ]).lower()
            
            # Check if any topic word appears in the review
            contains_topic = any(word.lower() in text for word in topic_words)
            
            if not contains_topic:
                continue
            
            # Analyze sentiment
            sentiment_result = sentiment_analyzer.analyze_sentiment(text)
            is_negative = sentiment_result.get("label", "").lower() == "negative"
            
            # Categorize by time period
            if review_date < cutoff_date:
                old_reviews.append({"negative": is_negative})
            else:
                new_reviews.append({"negative": is_negative})
        
        # Calculate negative share for each period
        old_negative_count = sum(1 for r in old_reviews if r["negative"])
        new_negative_count = sum(1 for r in new_reviews if r["negative"])
        
        old_negative_share = (old_negative_count / len(old_reviews) * 100) if old_reviews else 0
        new_negative_share = (new_negative_count / len(new_reviews) * 100) if new_reviews else 0
        
        # Calculate delta (positive delta means it got WORSE, more negative)
        delta = round(new_negative_share - old_negative_share, 1)
        
        # Determine direction
        if abs(delta) < 5:  # Less than 5% change is stable
            direction = "stable"
        elif delta > 0:
            direction = "up"  # More negative = worse
        else:
            direction = "down"  # Less negative = better
        
        return {
            "delta": delta,
            "direction": direction,
            "old_negative_share": round(old_negative_share, 1),
            "new_negative_share": round(new_negative_share, 1),
            "old_review_count": len(old_reviews),
            "new_review_count": len(new_reviews)
        }
        
    except Exception as e:
        print(f"Error calculating trend: {str(e)}")
        return {"delta": 0, "direction": "stable", "error": str(e)}


def extract_kritikpunkte_for_topic(
    company_id: int,
    topic_words: list[str],
    max_points: int = 3,
    max_rows: int = 200,
) -> list[str]:
    from database.supabase_client import get_supabase_client
    import re
    from collections import Counter

    supabase = get_supabase_client()
    if not topic_words:
        return []

    response = supabase.table("employee")\
        .select("schlecht_am_arbeitgeber_finde_ich, verbesserungsvorschlaege")\
        .eq("company_id", company_id)\
        .limit(max_rows)\
        .execute()

    rows = response.data or []
    texts: list[str] = []
    topic_words_l = [w.lower() for w in topic_words if w]

    for r in rows:
        neg = str(r.get("schlecht_am_arbeitgeber_finde_ich") or "")
        imp = str(r.get("verbesserungsvorschlaege") or "")
        combined = (neg + " " + imp).strip()
        if not combined:
            continue
        cl = combined.lower()
        if not any(w in cl for w in topic_words_l):
            continue
        # focus on negative-ish text fields
        if neg.strip():
            texts.append(neg)
        if imp.strip():
            texts.append(imp)

    if not texts:
        return []

    stop = {
        "und","oder","aber","dass","das","der","die","den","dem","des","ein","eine","einer","eines",
        "mit","ohne","für","auf","im","in","am","an","zu","von","bei","als","auch","nicht","nur",
        "ist","sind","war","waren","wird","werden","ich","wir","man","sehr","mehr","weniger","noch",
        "kein","keine","keinen","keiner","keines","über","unter","vor","nach","aus","um","wie","weil",
    }

    token_re = re.compile(r"[a-zA-ZäöüÄÖÜß]+", re.UNICODE)
    tokens: list[str] = []
    for t in texts:
        toks = [x.lower() for x in token_re.findall(t)]
        toks = [x for x in toks if len(x) >= 3 and x not in stop]
        tokens.extend(toks)

    if len(tokens) < 4:
        return []

    bigrams = Counter()
    trigrams = Counter()
    for i in range(len(tokens) - 1):
        bigrams[(tokens[i], tokens[i + 1])] += 1
    for i in range(len(tokens) - 2):
        trigrams[(tokens[i], tokens[i + 1], tokens[i + 2])] += 1

    phrases: list[tuple[str, int]] = []
    for (a, b, c), cnt in trigrams.most_common(50):
        if cnt < 2:
            break
        phrases.append((f"{a} {b} {c}", cnt))
    if len(phrases) < max_points:
        for (a, b), cnt in bigrams.most_common(50):
            if cnt < 2:
                break
            phrases.append((f"{a} {b}", cnt))

    # de-dup and return top N
    seen = set()
    out: list[str] = []
    for p, _ in sorted(phrases, key=lambda x: (-x[1], x[0])):
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
        if len(out) >= max_points:
            break
    return out


def extract_affected_categories_for_topic(
    company_id: int,
    topic_words: list[str],
    max_categories: int = 2,
    max_rows: int = 200,
) -> list[str]:
    from database.supabase_client import get_supabase_client

    supabase = get_supabase_client()
    if not topic_words:
        return []

    rating_fields = {
        "arbeitsatmosphaere": "sternebewertung_arbeitsatmosphaere",
        "image": "sternebewertung_image",
        "work_life_balance": "sternebewertung_work_life_balance",
        "karriere_weiterbildung": "sternebewertung_karriere_weiterbildung",
        "gehalt_sozialleistungen": "sternebewertung_gehalt_sozialleistungen",
        "kollegenzusammenhalt": "sternebewertung_kollegenzusammenhalt",
        "umwelt_sozialbewusstsein": "sternebewertung_umwelt_sozialbewusstsein",
        "vorgesetztenverhalten": "sternebewertung_vorgesetztenverhalten",
        "kommunikation": "sternebewertung_kommunikation",
        "interessante_aufgaben": "sternebewertung_interessante_aufgaben",
        "umgang_mit_aelteren_kollegen": "sternebewertung_umgang_mit_aelteren_kollegen",
        "arbeitsbedingungen": "sternebewertung_arbeitsbedingungen",
        "gleichberechtigung": "sternebewertung_gleichberechtigung",
    }

    label_map = {
        "arbeitsatmosphaere": "Arbeitsatmosphäre",
        "image": "Image",
        "work_life_balance": "Work-Life-Balance",
        "karriere_weiterbildung": "Karriere/Weiterbildung",
        "gehalt_sozialleistungen": "Gehalt/Sozialleistungen",
        "kollegenzusammenhalt": "Kollegenzusammenhalt",
        "umwelt_sozialbewusstsein": "Umwelt-/Sozialbewusstsein",
        "vorgesetztenverhalten": "Vorgesetztenverhalten",
        "kommunikation": "Kommunikation",
        "interessante_aufgaben": "Interessante Aufgaben",
        "umgang_mit_aelteren_kollegen": "Umgang mit älteren Kollegen",
        "arbeitsbedingungen": "Arbeitsbedingungen",
        "gleichberechtigung": "Gleichberechtigung",
    }

    select_cols = ["gut_am_arbeitgeber_finde_ich", "schlecht_am_arbeitgeber_finde_ich", "verbesserungsvorschlaege"]
    select_cols += list(rating_fields.values())
    response = supabase.table("employee")\
        .select(", ".join(select_cols))\
        .eq("company_id", company_id)\
        .limit(max_rows)\
        .execute()

    rows = response.data or []
    topic_words_l = [w.lower() for w in topic_words if w]
    if not rows:
        return []

    sums: dict[str, float] = {}
    counts: dict[str, int] = {}

    for r in rows:
        text = " ".join([
            str(r.get("gut_am_arbeitgeber_finde_ich") or ""),
            str(r.get("schlecht_am_arbeitgeber_finde_ich") or ""),
            str(r.get("verbesserungsvorschlaege") or ""),
        ]).lower()
        if not text.strip():
            continue
        if not any(w in text for w in topic_words_l):
            continue

        for key, col in rating_fields.items():
            val = r.get(col)
            if val is None:
                continue
            try:
                num = float(val)
            except Exception:
                continue
            sums[key] = sums.get(key, 0.0) + num
            counts[key] = counts.get(key, 0) + 1

    avgs = []
    for key, total in sums.items():
        cnt = counts.get(key, 0)
        if cnt <= 0:
            continue
        avgs.append((key, total / cnt, cnt))

    if not avgs:
        return []

    avgs.sort(key=lambda x: (x[1], -x[2]))
    out: list[str] = []
    for key, _, _ in avgs[:max_categories]:
        out.append(label_map.get(key, key.replace("_", " ").title()))
    return out


def calculate_topic_rating_trend(company_id: int, topic_words: list[str], window_days: int = 30) -> dict:
    """Calculate trend in avg_rating for reviews that mention the topic words.

    Compares average 'durchschnittsbewertung' for reviews in the last N days vs the previous N days.

    Returns:
        dict with 'delta' (new - old), 'direction' (up/down/stable),
        'old_avg_rating', 'new_avg_rating', 'old_review_count', 'new_review_count'
    """
    from database.supabase_client import get_supabase_client
    from datetime import datetime, timedelta, timezone

    supabase = get_supabase_client()

    try:
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=window_days)
        old_cutoff = now - timedelta(days=window_days * 2)

        response = supabase.table("employee")\
            .select("datum, created_at, durchschnittsbewertung, gut_am_arbeitgeber_finde_ich, schlecht_am_arbeitgeber_finde_ich, verbesserungsvorschlaege")\
            .eq("company_id", company_id)\
            .gte("datum", old_cutoff.isoformat())\
            .execute()

        reviews = response.data if response.data else []
        if len(reviews) < 2:
            return {"delta": 0, "direction": "stable", "message": "Not enough data"}

        old_ratings: list[float] = []
        new_ratings: list[float] = []

        for review in reviews:
            date_raw = review.get("datum") or review.get("created_at")
            if not date_raw:
                continue

            try:
                review_date = datetime.fromisoformat(str(date_raw).replace("Z", "+00:00"))
            except Exception:
                continue

            text = " ".join([
                str(review.get("gut_am_arbeitgeber_finde_ich", "")),
                str(review.get("schlecht_am_arbeitgeber_finde_ich", "")),
                str(review.get("verbesserungsvorschlaege", "")),
            ]).lower()

            if not any(word.lower() in text for word in topic_words):
                continue

            rating_raw = review.get("durchschnittsbewertung")
            if rating_raw is None:
                continue

            try:
                rating = float(rating_raw)
            except Exception:
                continue

            if review_date < cutoff_date:
                old_ratings.append(rating)
            else:
                new_ratings.append(rating)

        if not old_ratings and not new_ratings:
            return {"delta": 0, "direction": "stable", "message": "No topic-matching ratings"}

        old_avg = (sum(old_ratings) / len(old_ratings)) if old_ratings else 0.0
        new_avg = (sum(new_ratings) / len(new_ratings)) if new_ratings else 0.0

        delta = round(new_avg - old_avg, 2)

        if abs(delta) < 0.05:
            direction = "stable"
        elif delta > 0:
            direction = "up"  # rating increased (better)
        else:
            direction = "down"  # rating decreased (worse)

        return {
            "delta": delta,
            "direction": direction,
            "old_avg_rating": round(old_avg, 2),
            "new_avg_rating": round(new_avg, 2),
            "old_review_count": len(old_ratings),
            "new_review_count": len(new_ratings),
        }

    except Exception as e:
        print(f"Error calculating rating trend: {str(e)}")
        return {"delta": 0, "direction": "stable", "error": str(e)}