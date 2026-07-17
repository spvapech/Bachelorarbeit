"""
Example script for Topic-Rating Analysis
Demonstrates how to use the combined topic modeling, sentiment analysis, and ratings features.
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def train_model(source: str = "employee", num_topics: int = 5) -> Dict[str, Any]:
    """Train the LDA model."""
    print(f"\n🔄 Training model with {num_topics} topics from {source}...")
    
    response = requests.post(
        f"{BASE_URL}/api/topics/train",
        json={
            "source": source,
            "num_topics": num_topics
        }
    )
    
    result = response.json()
    
    if response.status_code == 200:
        print(f"✅ Model trained successfully!")
        print(f"   Documents: {result.get('num_documents')}")
        print(f"   Topics: {result.get('num_topics')}")
        print(f"   Vocabulary: {result.get('vocabulary_size')} words")
        
        # Show discovered topics
        print(f"\n📊 Discovered Topics:")
        for topic in result.get('topics', [])[:3]:  # Show first 3 topics
            print(f"\n   Topic {topic['topic_id']}:")
            words = [f"{w['word']} ({w['weight']:.3f})" for w in topic['words'][:5]]
            print(f"   Words: {', '.join(words)}")
    else:
        print(f"❌ Training failed: {result}")
    
    return result


def analyze_employee_reviews(limit: int = 10) -> Dict[str, Any]:
    """Analyze employee reviews with ratings."""
    print(f"\n🔍 Analyzing employee reviews (limit={limit})...")
    
    response = requests.get(
        f"{BASE_URL}/api/topics/analyze/employee-reviews-with-ratings",
        params={"limit": limit}
    )
    
    result = response.json()
    
    if response.status_code == 200:
        analysis = result['analysis']
        print(f"✅ Analyzed {analysis['total_reviews']} reviews")
        
        # Show first review as example
        if analysis['reviews']:
            review = analysis['reviews'][0]
            print(f"\n📝 Example Review (ID: {review['id']}):")
            print(f"   Titel: {review.get('titel', 'N/A')}")
            print(f"   Durchschnittsbewertung: {review.get('durchschnittsbewertung', 'N/A')} ⭐")
            
            if review.get('overall_sentiment'):
                sentiment = review['overall_sentiment']
                print(f"   Overall Sentiment: {sentiment['sentiment']} ({sentiment['avg_polarity']:.2f})")
            
            if review.get('topics_summary'):
                print(f"   Main Topics:")
                for topic in review['topics_summary'][:3]:
                    print(f"     - Topic {topic['topic_id']}: {topic['mentions']} mentions "
                          f"(prob: {topic['avg_probability']:.2f})")
            
            if review.get('ratings'):
                print(f"   Star Ratings:")
                for category, rating in list(review['ratings'].items())[:5]:
                    print(f"     - {category}: {rating} ⭐")
    else:
        print(f"❌ Analysis failed: {result}")
    
    return result


def analyze_topic_rating_correlation(limit: int = None) -> Dict[str, Any]:
    """Get topic-rating correlation."""
    print(f"\n📈 Analyzing topic-rating correlation...")
    
    params = {}
    if limit:
        params['limit'] = limit
    
    response = requests.get(
        f"{BASE_URL}/api/topics/analyze/topic-rating-correlation",
        params=params
    )
    
    result = response.json()
    
    if response.status_code == 200:
        correlation = result['correlation']
        print(f"✅ Correlation analysis complete")
        print(f"   Total topics: {correlation['total_topics']}")
        print(f"   Reviews analyzed: {correlation['summary']['total_reviews_analyzed']}")
        
        print(f"\n🎯 Topic-Rating Correlation:")
        for topic in correlation['topics'][:5]:  # Top 5 topics
            print(f"\n   Topic {topic['topic_id']}:")
            print(f"     Mentions: {topic['mention_count']}")
            print(f"     Avg Rating: {topic['avg_rating']:.2f} ⭐")
            print(f"     Sentiments: ✅ {topic['sentiments']['positive']} "
                  f"| ➖ {topic['sentiments']['neutral']} "
                  f"| ❌ {topic['sentiments']['negative']}")
            
            if topic.get('top_words'):
                words = [w['word'] for w in topic['top_words'][:5]]
                print(f"     Keywords: {', '.join(words)}")
    else:
        print(f"❌ Analysis failed: {result}")
    
    return result


def predict_with_sentiment(text: str) -> Dict[str, Any]:
    """Predict topics with sentiment for a text."""
    print(f"\n🔮 Predicting topics with sentiment...")
    print(f"   Text: '{text[:80]}...'")
    
    response = requests.post(
        f"{BASE_URL}/api/topics/predict-with-sentiment",
        json={
            "text": text,
            "threshold": 0.1
        }
    )
    
    result = response.json()
    
    if response.status_code == 200:
        print(f"✅ Prediction complete")
        
        if result.get('topics'):
            for topic in result['topics']:
                print(f"\n   Topic {topic['topic_id']}:")
                print(f"     Probability: {topic['probability']:.2f}")
                
                if topic.get('sentiment'):
                    sent = topic['sentiment']
                    emoji = "✅" if sent['sentiment'] == "positive" else "❌" if sent['sentiment'] == "negative" else "➖"
                    print(f"     Sentiment: {emoji} {sent['sentiment']} (polarity: {sent['polarity']:.2f})")
                    print(f"     Confidence: {sent['confidence']:.2f}")
        else:
            print("   No topics found for this text")
    else:
        print(f"❌ Prediction failed: {result}")
    
    return result


def main():
    """Run all examples."""
    print("=" * 80)
    print("🎯 Topic-Rating Analysis Examples")
    print("=" * 80)
    
    # 1. Train model
    train_model(source="employee", num_topics=5)
    
    # 2. Analyze employee reviews
    analyze_employee_reviews(limit=10)
    
    # 3. Get topic-rating correlation
    analyze_topic_rating_correlation(limit=50)
    
    # 4. Test with sample texts
    print("\n" + "=" * 80)
    print("📝 Testing with sample texts")
    print("=" * 80)
    
    sample_texts = [
        "Die Arbeitsatmosphäre ist sehr gut und das Team ist super zusammengewachsen.",
        "Das Gehalt könnte deutlich besser sein für die geleistete Arbeit.",
        "Work-Life-Balance ist ausgezeichnet, flexible Arbeitszeiten sind möglich.",
    ]
    
    for text in sample_texts:
        predict_with_sentiment(text)
    
    print("\n" + "=" * 80)
    print("✅ All examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to backend!")
        print("   Make sure the backend is running:")
        print("   cd backend && uv run uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")

