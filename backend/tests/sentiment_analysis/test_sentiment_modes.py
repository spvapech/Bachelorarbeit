"""
Test script to compare lexicon-based and transformer-based sentiment analysis.
"""

from models.sentiment_analyzer import SentimentAnalyzer


def test_sentiment_modes():
    """Test both sentiment analysis modes."""
    
    # Test texts in German
    test_texts = [
        "Die Arbeit hier ist fantastisch und das Team ist sehr unterstützend!",
        "Leider ist die Bezahlung schlecht und die Arbeitszeiten sind unfair.",
        "Es ist okay, nichts Besonderes.",
        "Brillante Unternehmenskultur mit exzellenten Entwicklungsmöglichkeiten.",
        "Katastrophales Management und keine Work-Life-Balance.",
        "Die Kollegen sind nett, aber die Projekte sind langweilig.",
        "Innovative Firma mit spannenden Herausforderungen!",
        "Viel zu viel Stress und keine Wertschätzung der Mitarbeiter.",
    ]
    
    print("=" * 80)
    print("SENTIMENT ANALYSIS COMPARISON")
    print("=" * 80)
    
    # Test Lexicon-based approach
    print("\n📚 LEXICON-BASED APPROACH (Rule-based)")
    print("-" * 80)
    analyzer_lexicon = SentimentAnalyzer(mode="lexicon")
    
    lexicon_results = []
    for text in test_texts:
        result = analyzer_lexicon.analyze_sentiment(text)
        lexicon_results.append(result)
        print(f"\nText: {text}")
        print(f"  → Sentiment: {result['sentiment']}")
        print(f"  → Polarity: {result['polarity']:.2f}")
        print(f"  → Confidence: {result['confidence']:.2f}")
    
    # Test Transformer-based approach
    print("\n\n🤖 TRANSFORMER-BASED APPROACH (Machine Learning)")
    print("-" * 80)
    
    try:
        analyzer_transformer = SentimentAnalyzer(mode="transformer")
        
        transformer_results = []
        for text in test_texts:
            result = analyzer_transformer.analyze_sentiment(text)
            transformer_results.append(result)
            print(f"\nText: {text}")
            print(f"  → Sentiment: {result['sentiment']}")
            print(f"  → Polarity: {result['polarity']:.2f}")
            print(f"  → Confidence: {result['confidence']:.2f}")
        
        # Compare results
        print("\n\n📊 COMPARISON")
        print("-" * 80)
        agreements = 0
        for i, text in enumerate(test_texts):
            lex_sent = lexicon_results[i]['sentiment']
            trans_sent = transformer_results[i]['sentiment']
            match = "✓" if lex_sent == trans_sent else "✗"
            agreements += (1 if lex_sent == trans_sent else 0)
            
            print(f"\n{match} Text: {text[:50]}...")
            print(f"   Lexicon: {lex_sent} (conf: {lexicon_results[i]['confidence']:.2f})")
            print(f"   Transformer: {trans_sent} (conf: {transformer_results[i]['confidence']:.2f})")
        
        accuracy = (agreements / len(test_texts)) * 100
        print(f"\n\nAgreement: {agreements}/{len(test_texts)} ({accuracy:.1f}%)")
        
    except ImportError as e:
        print("\n⚠️  Transformer mode not available.")
        print("To use ML-based sentiment analysis, install dependencies:")
        print("  pip install transformers torch")
        print(f"\nError: {e}")
    
    # Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    summary = analyzer_lexicon.get_sentiment_summary(lexicon_results)
    print(f"\nLexicon-based results:")
    print(f"  Positive: {summary['positive_count']} ({summary['positive_percentage']:.1f}%)")
    print(f"  Neutral:  {summary['neutral_count']} ({summary['neutral_percentage']:.1f}%)")
    print(f"  Negative: {summary['negative_count']} ({summary['negative_percentage']:.1f}%)")
    print(f"  Avg Polarity: {summary['avg_polarity']:.2f}")
    
    print("\n\n💡 RECOMMENDATIONS")
    print("-" * 80)
    print("✓ Lexicon-based: Fast, no dependencies, good for known vocabulary")
    print("✓ Transformer-based: More accurate, learns from context, handles unknown words")
    print("\nUse transformer mode for production if accuracy is critical!")


if __name__ == "__main__":
    test_sentiment_modes()
