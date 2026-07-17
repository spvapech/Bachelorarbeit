"""
Sentiment Analysis Accuracy Test
Compares Lexicon vs Transformer mode accuracy on real German review data.
"""

import sys
from typing import List, Dict, Any
from models.sentiment_analyzer import SentimentAnalyzer
from database.supabase_client import get_supabase_client

def get_test_reviews() -> List[Dict[str, Any]]:
    """
    Fetch a sample of real reviews from database for testing.
    Returns reviews with their text and star ratings.
    """
    supabase = get_supabase_client()
    
    # Get diverse sample: some positive, some negative, some neutral
    # The employee table has separate fields for positive/negative comments and overall rating
    response = supabase.table("employee")\
        .select("id, gut_am_arbeitgeber_finde_ich, schlecht_am_arbeitgeber_finde_ich, durchschnittsbewertung")\
        .not_.is_("gut_am_arbeitgeber_finde_ich", "null")\
        .not_.is_("schlecht_am_arbeitgeber_finde_ich", "null")\
        .not_.is_("durchschnittsbewertung", "null")\
        .limit(150)\
        .execute()
    
    reviews = []
    for review in response.data:
        positive_text = review.get("gut_am_arbeitgeber_finde_ich", "")
        negative_text = review.get("schlecht_am_arbeitgeber_finde_ich", "")
        rating = review.get("durchschnittsbewertung")
        
        # Add positive comments (should be classified as positive)
        if positive_text and len(positive_text.strip()) > 20:
            reviews.append({
                "id": f"{review['id']}_pos",
                "text": positive_text,
                "stars": rating,
                "expected_type": "positive"  # These are explicitly positive comments
            })
        
        # Add negative comments (should be classified as negative)
        if negative_text and len(negative_text.strip()) > 20:
            reviews.append({
                "id": f"{review['id']}_neg",
                "text": negative_text,
                "stars": rating,
                "expected_type": "negative"  # These are explicitly negative comments
            })
    
    return reviews

def map_stars_to_sentiment(stars: float, expected_type: str = None) -> str:
    """
    Map star rating and expected type to sentiment category.
    If expected_type is provided (from field type), use that.
    Otherwise use star rating:
    1-2 stars = negative
    2.5-3.5 stars = neutral
    4-5 stars = positive
    """
    if expected_type:
        return expected_type
    
    if stars <= 2.5:
        return "negative"
    elif stars <= 3.5:
        return "neutral"
    else:
        return "positive"

def calculate_accuracy(predictions: List[str], expected: List[str]) -> Dict[str, Any]:
    """
    Calculate accuracy metrics.
    """
    total = len(predictions)
    correct = sum(1 for p, e in zip(predictions, expected) if p == e)
    
    # Per-class accuracy
    positive_correct = sum(1 for p, e in zip(predictions, expected) if p == e and e == "positive")
    negative_correct = sum(1 for p, e in zip(predictions, expected) if p == e and e == "negative")
    neutral_correct = sum(1 for p, e in zip(predictions, expected) if p == e and e == "neutral")
    
    positive_total = expected.count("positive")
    negative_total = expected.count("negative")
    neutral_total = expected.count("neutral")
    
    return {
        "overall_accuracy": (correct / total * 100) if total > 0 else 0,
        "correct": correct,
        "total": total,
        "positive_accuracy": (positive_correct / positive_total * 100) if positive_total > 0 else 0,
        "negative_accuracy": (negative_correct / negative_total * 100) if negative_total > 0 else 0,
        "neutral_accuracy": (neutral_correct / neutral_total * 100) if neutral_total > 0 else 0,
        "class_distribution": {
            "positive": positive_total,
            "negative": negative_total,
            "neutral": neutral_total
        }
    }

def analyze_misclassifications(reviews: List[Dict], predictions: List[str], expected: List[str]) -> List[Dict]:
    """
    Identify and analyze misclassified examples.
    """
    misclassified = []
    
    for review, pred, exp in zip(reviews, predictions, expected):
        if pred != exp:
            misclassified.append({
                "text": review["text"][:200] + "..." if len(review["text"]) > 200 else review["text"],
                "stars": review["stars"],
                "expected": exp,
                "predicted": pred
            })
    
    return misclassified[:10]  # Return top 10 misclassifications

def test_sentiment_modes():
    """
    Test and compare both sentiment analysis modes.
    """
    print("=" * 80)
    print("SENTIMENT ANALYSIS ACCURACY TEST")
    print("=" * 80)
    print()
    
    # Fetch test data
    print("📊 Fetching test reviews from database...")
    reviews = get_test_reviews()
    print(f"✅ Loaded {len(reviews)} review texts")
    print(f"   (from 'gut_am_arbeitgeber' and 'schlecht_am_arbeitgeber' fields)")
    print()
    
    # Prepare expected sentiments based on field type and star ratings
    expected_sentiments = [map_stars_to_sentiment(r["stars"], r.get("expected_type")) for r in reviews]
    
    # Test Lexicon Mode
    print("-" * 80)
    print("🔤 TESTING LEXICON MODE")
    print("-" * 80)
    
    try:
        analyzer_lexicon = SentimentAnalyzer(mode="lexicon")
        lexicon_predictions = []
        lexicon_details = []
        
        for review in reviews:
            result = analyzer_lexicon.analyze_sentiment(review["text"])
            lexicon_predictions.append(result["sentiment"])
            lexicon_details.append(result)
        
        lexicon_accuracy = calculate_accuracy(lexicon_predictions, expected_sentiments)
        
        print(f"Overall Accuracy: {lexicon_accuracy['overall_accuracy']:.2f}%")
        print(f"Correct: {lexicon_accuracy['correct']}/{lexicon_accuracy['total']}")
        print()
        print("Per-Class Accuracy:")
        print(f"  ✅ Positive: {lexicon_accuracy['positive_accuracy']:.2f}% ({lexicon_accuracy['class_distribution']['positive']} samples)")
        print(f"  ⚪ Neutral:  {lexicon_accuracy['neutral_accuracy']:.2f}% ({lexicon_accuracy['class_distribution']['neutral']} samples)")
        print(f"  ❌ Negative: {lexicon_accuracy['negative_accuracy']:.2f}% ({lexicon_accuracy['class_distribution']['negative']} samples)")
        print()
        
        # Show average confidence and polarity
        avg_confidence = sum(d["confidence"] for d in lexicon_details) / len(lexicon_details)
        avg_polarity = sum(d["polarity"] for d in lexicon_details) / len(lexicon_details)
        print(f"Average Confidence: {avg_confidence:.3f}")
        print(f"Average Polarity: {avg_polarity:.3f}")
        print()
        
        lexicon_misclassified = analyze_misclassifications(reviews, lexicon_predictions, expected_sentiments)
        
    except Exception as e:
        print(f"❌ Error testing Lexicon mode: {e}")
        lexicon_accuracy = None
        lexicon_misclassified = []
    
    # Test Transformer Mode
    print("-" * 80)
    print("🤖 TESTING TRANSFORMER MODE")
    print("-" * 80)
    
    try:
        analyzer_transformer = SentimentAnalyzer(mode="transformer")
        
        if not analyzer_transformer._transformer_available:
            print("⚠️  Transformer mode not available - skipping")
            transformer_accuracy = None
            transformer_misclassified = []
        else:
            transformer_predictions = []
            transformer_details = []
            
            print("Processing reviews...")
            for i, review in enumerate(reviews):
                if (i + 1) % 10 == 0:
                    print(f"  Processed {i + 1}/{len(reviews)}...")
                result = analyzer_transformer.analyze_sentiment(review["text"])
                transformer_predictions.append(result["sentiment"])
                transformer_details.append(result)
            
            transformer_accuracy = calculate_accuracy(transformer_predictions, expected_sentiments)
            
            print()
            print(f"Overall Accuracy: {transformer_accuracy['overall_accuracy']:.2f}%")
            print(f"Correct: {transformer_accuracy['correct']}/{transformer_accuracy['total']}")
            print()
            print("Per-Class Accuracy:")
            print(f"  ✅ Positive: {transformer_accuracy['positive_accuracy']:.2f}% ({transformer_accuracy['class_distribution']['positive']} samples)")
            print(f"  ⚪ Neutral:  {transformer_accuracy['neutral_accuracy']:.2f}% ({transformer_accuracy['class_distribution']['neutral']} samples)")
            print(f"  ❌ Negative: {transformer_accuracy['negative_accuracy']:.2f}% ({transformer_accuracy['class_distribution']['negative']} samples)")
            print()
            
            # Show average confidence and polarity
            avg_confidence = sum(d["confidence"] for d in transformer_details) / len(transformer_details)
            avg_polarity = sum(d["polarity"] for d in transformer_details) / len(transformer_details)
            print(f"Average Confidence: {avg_confidence:.3f}")
            print(f"Average Polarity: {avg_polarity:.3f}")
            print()
            
            transformer_misclassified = analyze_misclassifications(reviews, transformer_predictions, expected_sentiments)
    
    except Exception as e:
        print(f"❌ Error testing Transformer mode: {e}")
        transformer_accuracy = None
        transformer_misclassified = []
    
    # Comparison Summary
    print("=" * 80)
    print("📊 COMPARISON SUMMARY")
    print("=" * 80)
    print()
    
    if lexicon_accuracy and transformer_accuracy:
        print(f"{'Metric':<30} {'Lexicon':<15} {'Transformer':<15} {'Improvement'}")
        print("-" * 80)
        print(f"{'Overall Accuracy':<30} {lexicon_accuracy['overall_accuracy']:>6.2f}%       {transformer_accuracy['overall_accuracy']:>6.2f}%       {transformer_accuracy['overall_accuracy'] - lexicon_accuracy['overall_accuracy']:>+6.2f}%")
        print(f"{'Positive Accuracy':<30} {lexicon_accuracy['positive_accuracy']:>6.2f}%       {transformer_accuracy['positive_accuracy']:>6.2f}%       {transformer_accuracy['positive_accuracy'] - lexicon_accuracy['positive_accuracy']:>+6.2f}%")
        print(f"{'Neutral Accuracy':<30} {lexicon_accuracy['neutral_accuracy']:>6.2f}%       {transformer_accuracy['neutral_accuracy']:>6.2f}%       {transformer_accuracy['neutral_accuracy'] - lexicon_accuracy['neutral_accuracy']:>+6.2f}%")
        print(f"{'Negative Accuracy':<30} {lexicon_accuracy['negative_accuracy']:>6.2f}%       {transformer_accuracy['negative_accuracy']:>6.2f}%       {transformer_accuracy['negative_accuracy'] - lexicon_accuracy['negative_accuracy']:>+6.2f}%")
        print()
        
        improvement = transformer_accuracy['overall_accuracy'] - lexicon_accuracy['overall_accuracy']
        if improvement > 5:
            print(f"✅ Transformer shows significant improvement: +{improvement:.2f}%")
        elif improvement > 0:
            print(f"✅ Transformer shows slight improvement: +{improvement:.2f}%")
        else:
            print(f"⚠️  Lexicon performs better or equally well: {improvement:.2f}%")
    
    print()
    print("-" * 80)
    print("🔍 EXAMPLE MISCLASSIFICATIONS (Lexicon)")
    print("-" * 80)
    for i, mis in enumerate(lexicon_misclassified[:5], 1):
        print(f"\n{i}. Stars: {mis['stars']} | Expected: {mis['expected']} | Predicted: {mis['predicted']}")
        print(f"   Text: {mis['text']}")
    
    if transformer_accuracy:
        print()
        print("-" * 80)
        print("🔍 EXAMPLE MISCLASSIFICATIONS (Transformer)")
        print("-" * 80)
        for i, mis in enumerate(transformer_misclassified[:5], 1):
            print(f"\n{i}. Stars: {mis['stars']} | Expected: {mis['expected']} | Predicted: {mis['predicted']}")
            print(f"   Text: {mis['text']}")
    
    print()
    print("=" * 80)
    print("✅ TEST COMPLETED")
    print("=" * 80)
    
    return {
        "lexicon": lexicon_accuracy,
        "transformer": transformer_accuracy,
        "lexicon_misclassified": lexicon_misclassified,
        "transformer_misclassified": transformer_misclassified
    }

if __name__ == "__main__":
    try:
        results = test_sentiment_modes()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
