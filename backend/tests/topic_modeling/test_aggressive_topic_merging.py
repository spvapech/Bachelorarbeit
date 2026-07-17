"""
Test Script: Force Topic Merging with Lower Threshold
Merges similar topics even with moderate overlap (15-20%).
"""

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.lda_topic_model import LDATopicAnalyzer


def main():
    print("=" * 80)
    print("🔄 AGGRESSIVE TOPIC MERGING TEST")
    print("=" * 80)
    
    # Initialize analyzer
    analyzer = LDATopicAnalyzer()
    
    # Load the latest trained model
    model_dir = "models/saved_models"
    
    # Find the latest model
    models = sorted([f for f in os.listdir(model_dir) if f.startswith("lda_model_") and f.endswith(".model")])
    
    if not models:
        print("❌ No trained models found.")
        return
    
    latest_model = models[-1].replace(".model", "")
    model_path = os.path.join(model_dir, latest_model)
    
    print(f"\n📂 Loading model: {latest_model}")
    metadata = analyzer.load_model(model_path)
    print(f"✅ Model loaded: {metadata['num_topics']} topics")
    
    # Display current topics
    print(f"\n{'='*80}")
    print("📊 CURRENT TOPICS")
    print(f"{'='*80}")
    
    topics = analyzer.get_topics()
    for topic in topics:
        print(f"\nTopic {topic['topic_id']}:")
        words = ', '.join([w['word'] for w in topic['words'][:8]])
        print(f"  {words}")
    
    # Analyze all topic similarities
    print(f"\n{'='*80}")
    print("🔍 DETAILED SIMILARITY ANALYSIS")
    print(f"{'='*80}")
    
    print("\nAll topic pair similarities:")
    print("-" * 80)
    
    all_similarities = []
    for i in range(analyzer.num_topics):
        for j in range(i + 1, analyzer.num_topics):
            sim = analyzer.calculate_topic_similarity(i, j, top_n=15)
            all_similarities.append((i, j, sim))
            
            words_i = [w for w, _ in analyzer.lda_model.show_topic(i, 5)]
            words_j = [w for w, _ in analyzer.lda_model.show_topic(j, 5)]
            
            indicator = "⚠️ HIGH" if sim >= 0.20 else "✅ OK" if sim >= 0.10 else "  "
            
            print(f"{indicator} Topic {i} ↔️ Topic {j}: {sim:.1%}")
            if sim >= 0.10:
                print(f"      {i}: {', '.join(words_i)}")
                print(f"      {j}: {', '.join(words_j)}")
    
    # Find average overlap
    avg_overlap = sum(s[2] for s in all_similarities) / len(all_similarities)
    print(f"\n📊 Average overlap: {avg_overlap:.1%}")
    
    # Apply aggressive merging with 15% threshold
    print(f"\n{'='*80}")
    print("🔄 APPLYING AGGRESSIVE MERGE (Threshold: 15%)")
    print(f"{'='*80}")
    
    result = analyzer.merge_similar_topics(
        similarity_threshold=0.15,
        verbose=True
    )
    
    # Display merged topics with analysis
    print(f"\n{'='*80}")
    print("📊 MERGED TOPICS ANALYSIS")
    print(f"{'='*80}")
    
    for rep_id, group in sorted(result['topic_groups'].items()):
        print(f"\n🎯 Merged Topic {rep_id}:")
        words = [w for w, _ in analyzer.lda_model.show_topic(rep_id, 12)]
        print(f"   Top Words: {', '.join(words)}")
        
        if len(group) > 1:
            print(f"   ✓ Combined from topics: {group}")
            print(f"   📝 Interpretation: ", end="")
            
            # Analyze what this merged topic represents
            word_set = set(words[:8])
            
            if any(w in word_set for w in ['mitarbeiter', 'unternehmen', 'stelle', 'arbeitnehmer']):
                print("Employee & Company Relations")
            elif any(w in word_set for w in ['bewerbung', 'gespraech', 'rueckmeldung']):
                print("Application Process & Communication")
            elif any(w in word_set for w in ['homeoffice', 'balance', 'work', 'life']):
                print("Work-Life-Balance & Benefits")
            elif any(w in word_set for w in ['gehalt', 'verguetung', 'bezahlung']):
                print("Compensation & Pay")
            elif any(w in word_set for w in ['team', 'kollegen', 'zusammenhalt']):
                print("Team & Collaboration")
            elif any(w in word_set for w in ['fuehrung', 'management', 'vorgesetzter']):
                print("Leadership & Management")
            else:
                print("Mixed/General Work Topics")
        else:
            print(f"   ℹ️  Unique topic (no similar topics found)")
    
    # Test predictions
    print(f"\n{'='*80}")
    print("🧪 PREDICTION COMPARISON")
    print(f"{'='*80}")
    
    test_texts = [
        "Das Unternehmen bietet gute Mitarbeiterangebote. Die Stelle ist interessant und die Kollegen sind nett.",
        "Der Bewerbungsprozess war gut organisiert. Ich bekam schnell Rückmeldung nach dem Gespräch.",
        "Das Gehalt ist fair und die Work-Life-Balance stimmt. Homeoffice ist möglich."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📄 Test {i}:")
        print(f"   Text: {text[:65]}...")
        print("-" * 40)
        
        # Original
        original = analyzer.predict_topics(text, threshold=0.05)
        print(f"   Original ({len(original)} topics):")
        for pred in original[:2]:
            words = [w for w, _ in analyzer.lda_model.show_topic(pred['topic_id'], 3)]
            print(f"      Topic {pred['topic_id']} ({pred['probability']:.0%}): {', '.join(words)}")
        
        # Merged
        merged = analyzer.predict_topics_merged(text, threshold=0.05)
        print(f"   Merged ({len(merged)} topics):")
        for pred in merged[:2]:
            words = [w for w, _ in analyzer.lda_model.show_topic(pred['topic_id'], 3)]
            merge_info = f" ← topics {pred.get('source_topics', [pred['topic_id']])}" if pred.get('is_merged') else ""
            print(f"      Topic {pred['topic_id']} ({pred['probability']:.0%}): {', '.join(words)}{merge_info}")
    
    # Final statistics
    print(f"\n{'='*80}")
    print("📈 IMPROVEMENT SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n✅ Original model: {result['original_num_topics']} topics")
    print(f"✅ After merging: {result['merged_num_topics']} topics")
    print(f"✅ Reduction: {result['reduction']} topics merged")
    print(f"✅ Similar pairs handled: {len(result['similar_pairs'])}")
    
    if result['reduction'] > 0:
        print(f"\n🎉 Benefits of merging:")
        print(f"   • Reduced overlap between similar topics")
        print(f"   • More focused topic categories")
        print(f"   • Clearer semantic distinctions")
        print(f"   • Better user experience with consolidated topics")
        
        reduction_pct = (result['reduction'] / result['original_num_topics']) * 100
        print(f"\n📊 Complexity reduction: {reduction_pct:.0f}%")
        
        if reduction_pct >= 15:
            print("   ✅ Significant improvement achieved!")
        elif reduction_pct >= 5:
            print("   ✅ Moderate improvement achieved")
        else:
            print("   ℹ️  Minor improvement - topics were already well-separated")
    else:
        print(f"\nℹ️  Topics are already optimally separated")
        print(f"   Current overlap is minimal ({avg_overlap:.1%} average)")
    
    print(f"\n{'='*80}")
    print("✅ AGGRESSIVE MERGING TEST COMPLETED")
    print(f"{'='*80}")
    
    print("\n💡 Usage in Production:")
    print("   # Use merged predictions:")
    print("   results = analyzer.predict_topics_merged(text, threshold=0.1)")
    print("\n   # Access merged topic info:")
    print("   for r in results:")
    print("       print(f\"Topic {r['topic_id']}: {r['probability']:.0%}\")")
    print("       if r.get('is_merged'):")
    print("           print(f\"  (combined from topics: {r['source_topics']})\")")


if __name__ == "__main__":
    main()
