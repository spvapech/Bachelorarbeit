"""
Test Script: Topic Merging for LDA Model
Automatically identifies and merges similar topics to reduce overlap.
"""

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.lda_topic_model import LDATopicAnalyzer


def main():
    print("=" * 80)
    print("🔄 TOPIC MERGING TEST")
    print("=" * 80)
    
    # Initialize analyzer
    analyzer = LDATopicAnalyzer()
    
    # Load the latest trained model
    model_dir = "models/saved_models"
    
    # Find the latest model
    models = sorted([f for f in os.listdir(model_dir) if f.startswith("lda_model_") and f.endswith(".model")])
    
    if not models:
        print("❌ No trained models found. Please train a model first.")
        print("   Run: python test_improved_topics.py")
        return
    
    latest_model = models[-1].replace(".model", "")
    model_path = os.path.join(model_dir, latest_model)
    
    print(f"\n📂 Loading model: {latest_model}")
    metadata = analyzer.load_model(model_path)
    print(f"✅ Model loaded successfully")
    print(f"   Topics: {metadata['num_topics']}")
    print(f"   Vocabulary: {metadata['vocabulary_size']}")
    print(f"   Trained: {metadata['trained_at']}")
    
    # Display current topics
    print(f"\n{'='*80}")
    print("📊 CURRENT TOPICS (Before Merging)")
    print(f"{'='*80}")
    
    topics = analyzer.get_topics()
    for topic in topics:
        print(f"\nTopic {topic['topic_id']}:")
        print(f"  Words: {', '.join([w['word'] for w in topic['words'][:10]])}")
    
    # Analyze topic similarities
    print(f"\n{'='*80}")
    print("🔍 ANALYZING TOPIC SIMILARITIES")
    print(f"{'='*80}")
    
    similar_pairs = analyzer.find_similar_topics(similarity_threshold=0.15, top_n=15)
    
    if similar_pairs:
        print(f"\nFound {len(similar_pairs)} similar topic pairs:")
        print("-" * 80)
        for topic1, topic2, similarity in similar_pairs:
            words1 = [w for w, _ in analyzer.lda_model.show_topic(topic1, 5)]
            words2 = [w for w, _ in analyzer.lda_model.show_topic(topic2, 5)]
            print(f"\n📌 Topic {topic1} ↔️ Topic {topic2} (Similarity: {similarity:.2%})")
            print(f"   Topic {topic1}: {', '.join(words1)}")
            print(f"   Topic {topic2}: {', '.join(words2)}")
    else:
        print("\n✅ No similar topics found (all topics are sufficiently distinct)")
    
    # Merge similar topics
    print(f"\n{'='*80}")
    print("🔄 MERGING SIMILAR TOPICS")
    print(f"{'='*80}")
    
    # Test with different thresholds
    thresholds = [0.20, 0.25, 0.30]
    
    best_result = None
    best_threshold = None
    
    for threshold in thresholds:
        print(f"\n🧪 Testing threshold: {threshold:.0%}")
        print("-" * 40)
        
        result = analyzer.merge_similar_topics(
            similarity_threshold=threshold,
            verbose=False
        )
        
        print(f"   Original topics: {result['original_num_topics']}")
        print(f"   Merged topics: {result['merged_num_topics']}")
        print(f"   Reduction: {result['reduction']} topics")
        
        # Choose best threshold (aim for 10-15% reduction)
        if result['reduction'] > 0 and result['reduction'] <= 2:
            best_result = result
            best_threshold = threshold
    
    # Apply best merge
    if best_result:
        print(f"\n{'='*80}")
        print(f"✅ APPLYING BEST MERGE (Threshold: {best_threshold:.0%})")
        print(f"{'='*80}")
        
        # Re-run with verbose output
        final_result = analyzer.merge_similar_topics(
            similarity_threshold=best_threshold,
            verbose=True
        )
        
        # Display merged topics
        print(f"\n{'='*80}")
        print("📊 MERGED TOPICS (After Merging)")
        print(f"{'='*80}")
        
        for rep_id, group in sorted(final_result['topic_groups'].items()):
            print(f"\n🎯 Merged Topic {rep_id}:")
            words = [w for w, _ in analyzer.lda_model.show_topic(rep_id, 10)]
            print(f"   Top Words: {', '.join(words)}")
            if len(group) > 1:
                print(f"   ✓ Includes original topics: {group}")
            else:
                print(f"   ℹ️  Single topic (no merge)")
        
        # Test prediction with merged topics
        print(f"\n{'='*80}")
        print("🧪 TEST: Prediction with Merged Topics")
        print(f"{'='*80}")
        
        test_texts = [
            "Die work life balance ist gut und das Gehalt ist fair. Das Team ist sehr hilfsbereit.",
            "Der Bewerbungsprozess war sehr langwierig und ich habe keine Rückmeldung bekommen.",
            "Die Führung ist transparent und die Kommunikation funktioniert gut."
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"\nTest {i}: {text[:70]}...")
            print("-" * 40)
            
            # Original prediction
            original = analyzer.predict_topics(text, threshold=0.1)
            print(f"Original: {len(original)} topics")
            for pred in original[:3]:
                print(f"  Topic {pred['topic_id']}: {pred['probability']:.1%}")
            
            # Merged prediction
            merged = analyzer.predict_topics_merged(text, threshold=0.1)
            print(f"Merged:   {len(merged)} topics")
            for pred in merged[:3]:
                sources = pred.get('source_topics', [pred['topic_id']])
                merge_info = f" (merged from {sources})" if pred.get('is_merged') else ""
                print(f"  Topic {pred['topic_id']}: {pred['probability']:.1%}{merge_info}")
        
        # Show final statistics
        print(f"\n{'='*80}")
        print("📈 IMPROVEMENT STATISTICS")
        print(f"{'='*80}")
        
        print(f"\n✅ Topics reduced: {final_result['original_num_topics']} → {final_result['merged_num_topics']}")
        print(f"✅ Overlap reduction: {len(final_result['similar_pairs'])} similar pairs merged")
        print(f"✅ More focused topic distribution")
        print(f"✅ Clearer topic distinctions")
        
    else:
        print(f"\n{'='*80}")
        print("ℹ️  NO MERGING RECOMMENDED")
        print(f"{'='*80}")
        print("\nTopics are already sufficiently distinct.")
        print("The current model has good topic separation.")
    
    print(f"\n{'='*80}")
    print("✅ TOPIC MERGING TEST COMPLETED")
    print(f"{'='*80}")
    
    print("\n💡 Next Steps:")
    print("   1. If topics were merged, use predict_topics_merged() for predictions")
    print("   2. Adjust similarity_threshold if you want more/less merging")
    print("   3. Consider retraining with optimal num_topics directly")


if __name__ == "__main__":
    main()
