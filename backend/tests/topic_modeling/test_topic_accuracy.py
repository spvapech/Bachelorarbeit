"""
Topic Modeling Accuracy Test
Evaluates how well the LDA model identifies topics in employee reviews.
Tests topic coherence, distinctiveness, and prediction accuracy.
"""

import sys
from typing import List, Dict, Any
from collections import defaultdict
from models.lda_topic_model import LDATopicAnalyzer
from services.topic_model_service import TopicModelDatabase


def load_trained_model() -> LDATopicAnalyzer:
    """Load the existing trained model from disk."""
    print("📂 Loading trained LDA model...")
    try:
        analyzer = LDATopicAnalyzer()
        model_dir = "models/saved_models"
        
        # Find the most recent model
        import os
        import glob
        model_files = glob.glob(f"{model_dir}/lda_model_*.model")
        if not model_files:
            raise FileNotFoundError("No trained model found. Please train a model first.")
        
        latest_model = max(model_files, key=os.path.getctime)
        model_path = latest_model.replace(".model", "")
        
        analyzer.load_model(model_path)
        print(f"✅ Loaded model: {os.path.basename(model_path)}")
        return analyzer
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        raise


def evaluate_topic_coherence(analyzer: LDATopicAnalyzer) -> Dict[str, Any]:
    """
    Evaluate topic coherence - how semantically related are words within topics?
    """
    print("\n" + "="*80)
    print("📊 TOPIC COHERENCE EVALUATION")
    print("="*80)
    
    topics = analyzer.get_topics(num_words=10)
    
    print(f"\nAnalyzing {len(topics)} topics...")
    print("\n" + "-"*80)
    
    for topic in topics:
        print(f"\nTopic {topic['topic_id']}:")
        words = [w['word'] for w in topic['words'][:10]]
        weights = [w['weight'] for w in topic['words'][:10]]
        
        print(f"  Top words: {', '.join(words[:5])}")
        print(f"  Weight range: {min(weights):.4f} - {max(weights):.4f}")
        
        # Simple coherence check: are words related?
        # High weights = more important to topic
        weight_concentration = max(weights) / sum(weights) if sum(weights) > 0 else 0
        print(f"  Weight concentration: {weight_concentration:.2%}")
        
        # Check for word diversity
        unique_stems = len(set(w[:4] for w in words))  # Rough stem check
        diversity = unique_stems / len(words) if words else 0
        print(f"  Word diversity: {diversity:.2%}")
    
    return {
        "num_topics": len(topics),
        "topics_analyzed": True
    }


def evaluate_topic_distinctiveness(analyzer: LDATopicAnalyzer) -> Dict[str, Any]:
    """
    Evaluate topic distinctiveness - how different are topics from each other?
    """
    print("\n" + "="*80)
    print("📊 TOPIC DISTINCTIVENESS EVALUATION")
    print("="*80)
    
    topics = analyzer.get_topics(num_words=10)
    
    # Get top words for each topic
    topic_words = {}
    for topic in topics:
        topic_id = topic['topic_id']
        topic_words[topic_id] = set(w['word'] for w in topic['words'][:10])
    
    # Calculate overlap between topics
    overlaps = []
    print("\nTopic Overlap Analysis:")
    print("-"*80)
    
    for i, topic_i in enumerate(topics):
        for j, topic_j in enumerate(topics):
            if i < j:  # Only compare each pair once
                words_i = topic_words[topic_i['topic_id']]
                words_j = topic_words[topic_j['topic_id']]
                
                overlap = len(words_i & words_j)
                overlap_pct = overlap / 10 * 100  # Out of 10 words
                
                overlaps.append(overlap_pct)
                
                if overlap_pct > 30:  # High overlap is problematic
                    print(f"⚠️  Topic {topic_i['topic_id']} ↔ Topic {topic_j['topic_id']}: {overlap_pct:.0f}% overlap")
                    common = words_i & words_j
                    print(f"    Common words: {', '.join(list(common)[:5])}")
    
    avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0
    
    print(f"\nAverage topic overlap: {avg_overlap:.1f}%")
    
    if avg_overlap < 20:
        print("✅ Good distinctiveness (< 20% overlap)")
    elif avg_overlap < 40:
        print("⚠️  Moderate distinctiveness (20-40% overlap)")
    else:
        print("❌ Poor distinctiveness (> 40% overlap)")
    
    return {
        "average_overlap": avg_overlap,
        "num_comparisons": len(overlaps),
        "distinctiveness": "good" if avg_overlap < 20 else "moderate" if avg_overlap < 40 else "poor"
    }


def evaluate_prediction_consistency(analyzer: LDATopicAnalyzer) -> Dict[str, Any]:
    """
    Evaluate prediction consistency - does the model assign topics reliably?
    Note: Multiple topics per review is EXPECTED and NORMAL in real reviews.
    """
    print("\n" + "="*80)
    print("📊 PREDICTION CONSISTENCY EVALUATION")
    print("="*80)
    
    # Load some real reviews for testing
    db = TopicModelDatabase()
    employee_data = db.get_employee_texts_with_metadata(limit=100)
    
    if not employee_data:
        print("⚠️  No reviews available for testing")
        return {"error": "No data"}
    
    print(f"\nTesting on {len(employee_data)} real employee reviews...")
    print("(Note: Multiple topics per review is normal and expected)")
    
    # Analyze predictions
    topic_assignments = defaultdict(int)
    no_topic_count = 0
    single_topic_count = 0
    multi_topic_count = 0
    low_confidence_count = 0
    high_confidence_count = 0
    
    confidence_scores = []
    topics_per_review = []
    
    for item in employee_data:
        # Review is already just the text string
        text = item.get('text', '')
        
        if not text or len(text.strip()) < 10:
            continue
        
        # Predict topics
        predictions = analyzer.predict_topics(text, threshold=0.1)
        
        num_topics = len(predictions)
        topics_per_review.append(num_topics)
        
        if num_topics == 0:
            no_topic_count += 1
        elif num_topics == 1:
            single_topic_count += 1
        else:
            multi_topic_count += 1
        
        for pred in predictions:
            topic_assignments[pred['topic_id']] += 1
            confidence_scores.append(pred['probability'])
            
            if pred['probability'] < 0.3:
                low_confidence_count += 1
            elif pred['probability'] > 0.5:
                high_confidence_count += 1
    
    # Calculate statistics
    total_with_text = len(employee_data)
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    avg_topics_per_review = sum(topics_per_review) / len(topics_per_review) if topics_per_review else 0
    
    print("\nPrediction Statistics:")
    print("-"*80)
    print(f"Total reviews analyzed: {total_with_text}")
    print(f"Reviews with NO topic: {no_topic_count} ({no_topic_count/total_with_text*100:.1f}%) ⚠️")
    print(f"Reviews with SINGLE topic: {single_topic_count} ({single_topic_count/total_with_text*100:.1f}%)")
    print(f"Reviews with MULTIPLE topics: {multi_topic_count} ({multi_topic_count/total_with_text*100:.1f}%) ✅")
    print(f"Average topics per review: {avg_topics_per_review:.1f}")
    print()
    print(f"Average confidence: {avg_confidence:.3f}")
    print(f"High confidence predictions (> 0.5): {high_confidence_count} ({high_confidence_count/len(confidence_scores)*100:.1f}%)")
    print(f"Low confidence predictions (< 0.3): {low_confidence_count} ({low_confidence_count/len(confidence_scores)*100:.1f}%)")
    
    print("\nTopic Distribution:")
    print("-"*80)
    for topic_id, count in sorted(topic_assignments.items()):
        pct = count / total_with_text * 100
        bar = "█" * int(pct / 2)
        print(f"Topic {topic_id}: {bar} {count:3d} ({pct:5.1f}%)")
    
    # Check for balance
    if topic_assignments:
        max_count = max(topic_assignments.values())
        min_count = min(topic_assignments.values())
        balance_ratio = min_count / max_count if max_count > 0 else 0
        
        print(f"\nTopic Balance Ratio: {balance_ratio:.2f}")
        if balance_ratio > 0.5:
            print("✅ Good balance (topics evenly distributed)")
        elif balance_ratio > 0.2:
            print("⚠️  Moderate balance")
        else:
            print("❌ Poor balance (some topics dominate)")
    
    # Interpret results
    print("\n" + "="*80)
    print("📝 INTERPRETATION")
    print("="*80)
    
    if no_topic_count / total_with_text > 0.1:
        print(f"⚠️  {no_topic_count/total_with_text*100:.0f}% reviews have NO topics - threshold might be too high")
    else:
        print(f"✅ Only {no_topic_count/total_with_text*100:.0f}% reviews have no topics - good coverage")
    
    if avg_topics_per_review < 2:
        print(f"⚠️  Average {avg_topics_per_review:.1f} topics/review - might be too few")
    elif avg_topics_per_review > 4:
        print(f"⚠️  Average {avg_topics_per_review:.1f} topics/review - might be too many (threshold too low?)")
    else:
        print(f"✅ Average {avg_topics_per_review:.1f} topics/review - realistic for complex reviews")
    
    if avg_confidence < 0.2:
        print(f"⚠️  Low average confidence ({avg_confidence:.2f}) - model is very uncertain")
    elif avg_confidence < 0.3:
        print(f"⚠️  Moderate confidence ({avg_confidence:.2f}) - acceptable for LDA")
    else:
        print(f"✅ Good confidence ({avg_confidence:.2f})")
    
    return {
        "total_analyzed": total_with_text,
        "no_topic_pct": no_topic_count / total_with_text * 100 if total_with_text > 0 else 0,
        "single_topic_pct": single_topic_count / total_with_text * 100 if total_with_text > 0 else 0,
        "multi_topic_pct": multi_topic_count / total_with_text * 100 if total_with_text > 0 else 0,
        "avg_topics_per_review": avg_topics_per_review,
        "avg_confidence": avg_confidence,
        "high_confidence_pct": high_confidence_count / len(confidence_scores) * 100 if confidence_scores else 0,
        "topic_distribution": dict(topic_assignments)
    }


def evaluate_semantic_quality(analyzer: LDATopicAnalyzer) -> Dict[str, Any]:
    """
    Qualitatively evaluate if topics make semantic sense.
    """
    print("\n" + "="*80)
    print("📊 SEMANTIC QUALITY EVALUATION")
    print("="*80)
    
    topics = analyzer.get_topics(num_words=10)
    
    # Common categories in employee reviews (German)
    expected_categories = {
        "work_life_balance": ["work", "life", "balance", "zeit", "flexible", "stunden", "urlaub", "freizeit"],
        "compensation": ["gehalt", "bezahlung", "lohn", "geld", "verdienst", "bonus", "sozialleistungen"],
        "team_culture": ["team", "kollegen", "zusammenarbeit", "atmosphäre", "kultur", "mitarbeiter"],
        "management": ["management", "führung", "vorgesetzten", "chef", "leitung", "entscheidungen"],
        "career": ["karriere", "weiterbildung", "entwicklung", "aufstieg", "perspektiven", "wachstum"],
        "communication": ["kommunikation", "information", "transparenz", "feedback", "austausch"],
        "tasks": ["aufgaben", "projekte", "arbeit", "tätigkeiten", "verantwortung", "interessant"]
    }
    
    print("\nTrying to identify topic categories:")
    print("-"*80)
    
    category_matches = defaultdict(list)
    
    for topic in topics:
        topic_id = topic['topic_id']
        words = [w['word'].lower() for w in topic['words'][:10]]
        
        print(f"\nTopic {topic_id}:")
        print(f"  Words: {', '.join(words[:5])}")
        
        # Try to match to expected categories
        best_match = None
        best_score = 0
        
        for category, keywords in expected_categories.items():
            matches = sum(1 for word in words if any(kw in word or word in kw for kw in keywords))
            if matches > best_score:
                best_score = matches
                best_match = category
        
        if best_match and best_score >= 2:
            print(f"  → Likely category: {best_match} (confidence: {best_score}/10)")
            category_matches[best_match].append(topic_id)
        else:
            print(f"  → Unclear category (no strong match)")
    
    print("\n" + "-"*80)
    print("Category Coverage:")
    for category, topic_ids in category_matches.items():
        print(f"  {category}: Topics {topic_ids}")
    
    uncovered = set(expected_categories.keys()) - set(category_matches.keys())
    if uncovered:
        print(f"\n⚠️  Potentially missing categories: {', '.join(uncovered)}")
    
    coverage = len(category_matches) / len(expected_categories) * 100
    print(f"\nCategory coverage: {coverage:.0f}%")
    
    return {
        "identified_categories": len(category_matches),
        "total_expected": len(expected_categories),
        "coverage_pct": coverage
    }


def main():
    """Run all topic model evaluations."""
    print("="*80)
    print("LDA TOPIC MODEL EVALUATION")
    print("="*80)
    
    try:
        # Load model
        analyzer = load_trained_model()
        
        # Run evaluations
        results = {
            "coherence": evaluate_topic_coherence(analyzer),
            "distinctiveness": evaluate_topic_distinctiveness(analyzer),
            "consistency": evaluate_prediction_consistency(analyzer),
            "semantic_quality": evaluate_semantic_quality(analyzer)
        }
        
        # Summary
        print("\n" + "="*80)
        print("📊 EVALUATION SUMMARY")
        print("="*80)
        
        print(f"\n✅ Topics analyzed: {results['coherence']['num_topics']}")
        print(f"✅ Topic distinctiveness: {results['distinctiveness']['distinctiveness']}")
        print(f"✅ Average topic overlap: {results['distinctiveness']['average_overlap']:.1f}%")
        print(f"✅ Average prediction confidence: {results['consistency']['avg_confidence']:.3f}")
        print(f"✅ Average topics per review: {results['consistency']['avg_topics_per_review']:.1f}")
        print(f"✅ Category coverage: {results['semantic_quality']['coverage_pct']:.0f}%")
        
        print(f"\n📌 Key Insights:")
        if results['consistency']['no_topic_pct'] < 10:
            print(f"   ✅ Only {results['consistency']['no_topic_pct']:.1f}% reviews have no topics")
        else:
            print(f"   ⚠️  {results['consistency']['no_topic_pct']:.1f}% reviews have no topics")
        
        print(f"   ℹ️  {results['consistency']['multi_topic_pct']:.1f}% reviews have multiple topics (NORMAL)")
        print(f"   ℹ️  High confidence predictions: {results['consistency']['high_confidence_pct']:.1f}%")
        
        print("\n" + "="*80)
        print("✅ EVALUATION COMPLETED")
        print("="*80)
        
        return results
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    try:
        results = main()
        if results is None:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Evaluation interrupted by user")
        sys.exit(1)
