"""
Test script for improved LDA topic modeling with work-focused topics.
"""

from models.lda_topic_model import LDATopicAnalyzer
from services.topic_model_service import TopicModelDatabase

def test_preprocessing():
    """Test the improved preprocessing with stopwords and normalization."""
    print("=" * 60)
    print("TEST 1: Verbessertes Preprocessing mit Bewertungskriterien")
    print("=" * 60)
    
    analyzer = LDATopicAnalyzer(num_topics=5)
    
    # Zeige extrahierte Rating-Kriterien
    rating_keywords = LDATopicAnalyzer.get_rating_criteria_keywords()
    print(f"\nAutomatisch extrahierte Bewertungskriterien ({len(rating_keywords)} Begriffe):")
    print("Beispiele:", sorted(list(rating_keywords))[:15])
    
    # Test text with common stopwords and abbreviations
    test_text = """
    Die MA haben sehr gut gearbeitet. Der AG bietet gute Konditionen.
    Die WLB ist okay und HO ist möglich. Die GF ist nett und die 
    Mitarbeiter sind zufrieden. Die work life balance ist super.
    Die Karriere und Weiterbildung sind wichtig. Das Gehalt und die
    Sozialleistungen sind fair. Die Arbeitsatmosphäre ist angenehm.
    """
    
    print("\nOriginal Text:")
    print(test_text)
    
    tokens = analyzer.preprocess_text(test_text)
    print(f"\nPreprocessed Tokens ({len(tokens)} tokens):")
    print(tokens)
    print("\n✅ Beobachtungen:")
    print("  - Stopwords und Füllwörter wurden entfernt")
    print("  - Abkürzungen wurden normalisiert (MA→mitarbeiter, WLB→work_life_balance)")
    print("  - Bewertungskriterien wurden beibehalten (karriereentwicklung, verguetung, etc.)")
    print("  - Zusammengesetzte Begriffe wurden normalisiert (work_life_balance)")



def test_bigrams_trigrams():
    """Test bigram and trigram detection."""
    print("\n" + "=" * 60)
    print("TEST 2: Bigram/Trigram Erkennung")
    print("=" * 60)
    
    analyzer = LDATopicAnalyzer(num_topics=3)
    
    # Texts with common work phrases
    texts = [
        "Die work life balance ist sehr gut. Home Office Möglichkeiten sind vorhanden.",
        "Das team work funktioniert super. Die flexible arbeitszeit wird geschätzt.",
        "Work life balance und home office sind wichtig. Team work ist essentiell.",
        "Die flexible arbeitszeit ermöglicht gute work life balance. Home office jeden Tag.",
        "Team work und home office kombiniert. Flexible arbeitszeit ist super.",
    ]
    
    print("\nTrainiere auf Beispieltexten...")
    analyzer.prepare_documents(texts)
    
    print(f"\nGefundene Begriffe im Wörterbuch: {len(analyzer.dictionary)}")
    print("\nBeispiel-Begriffe (mit Bigrams/Trigrams):")
    
    # Show some terms from dictionary
    terms = list(analyzer.dictionary.token2id.keys())[:30]
    for term in terms:
        if '_' in term:  # Highlight bigrams/trigrams
            print(f"  ✓ {term} (Phrase)")
        else:
            print(f"    {term}")


def test_topic_quality():
    """Test topic quality with real data from database."""
    print("\n" + "=" * 60)
    print("TEST 3: Topic-Qualität mit echten Daten")
    print("=" * 60)
    
    try:
        # Get real data
        db = TopicModelDatabase()
        data = db.get_all_texts(source="both", limit=50)
        
        if not data['texts']:
            print("\n⚠️ Keine Daten in der Datenbank gefunden!")
            print("Füge zuerst Daten über den Upload-Endpunkt hinzu.")
            return
        
        print(f"\nGefundene Dokumente: {data['metadata']['total_count']}")
        print(f"  - Kandidaten: {data['metadata']['candidates_count']}")
        print(f"  - Mitarbeiter: {data['metadata']['employee_count']}")
        
        # Train model with optimized parameters
        analyzer = LDATopicAnalyzer(num_topics=6, passes=20, iterations=400)
        
        print("\nTrainiere verbessertes LDA-Modell...")
        result = analyzer.train_model(data['texts'])
        
        print(f"\nModell erfolgreich trainiert!")
        print(f"  - Anzahl Topics: {result['num_topics']}")
        print(f"  - Vokabular-Größe: {result['vocabulary_size']}")
        print(f"  - Anzahl Dokumente: {result['num_documents']}")
        
        print("\n" + "-" * 60)
        print("Entdeckte Topics (Top 10 Wörter pro Topic):")
        print("-" * 60)
        
        topics = analyzer.get_topics(num_words=10)
        for topic in topics:
            print(f"\n📊 Topic {topic['topic_id']}:")
            for word_info in topic['words']:
                word = word_info['word']
                weight = word_info['weight']
                
                # Highlight bigrams/trigrams and work-related terms
                if '_' in word:
                    print(f"   ✓ {word:25} ({weight:.4f}) [PHRASE]")
                else:
                    print(f"     {word:25} ({weight:.4f})")
        
        # Test prediction
        print("\n" + "-" * 60)
        print("Test: Topic Prediction für Beispieltext")
        print("-" * 60)
        
        test_text = """
        Die work life balance ist ausgezeichnet. Das team ist sehr 
        kompetent und hilfsbereit. Home office ist flexibel möglich.
        Die weiterbildungsmöglichkeiten sind gut, aber das gehalt 
        könnte besser sein. Die führung ist transparent und fair.
        """
        
        print(f"\nTest-Text:")
        print(test_text)
        
        predictions = analyzer.predict_topics(test_text, threshold=0.1)
        
        print(f"\nErkannte Topics:")
        for pred in predictions:
            topic_id = pred['topic_id']
            prob = pred['probability']
            print(f"  - Topic {topic_id}: {prob:.1%}")
        
        # Save the model
        print("\n" + "-" * 60)
        print("Speichere verbessertes Modell...")
        model_path = analyzer.save_model()
        print(f"✓ Modell gespeichert: {model_path}")
        print("  (inkl. Bigram/Trigram-Modelle)")
        
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()


def compare_with_old_model():
    """Compare topic quality with old model if available."""
    print("\n" + "=" * 60)
    print("TEST 4: Vergleich mit altem Modell")
    print("=" * 60)
    
    import os
    import glob
    
    model_dir = "models"
    if not os.path.exists(model_dir):
        print("\n⚠️ Kein Modell-Ordner gefunden.")
        return
    
    # Find old models
    old_models = glob.glob(os.path.join(model_dir, "lda_model_*.model"))
    
    if not old_models:
        print("\n⚠️ Keine alten Modelle gefunden.")
        return
    
    print(f"\nGefundene Modelle: {len(old_models)}")
    for model in old_models:
        model_name = os.path.basename(model).replace('.model', '')
        print(f"  - {model_name}")
    
    # Load the most recent old model
    latest_model = sorted(old_models)[-1]
    model_path = latest_model.replace('.model', '')
    
    print(f"\nLade altes Modell: {os.path.basename(model_path)}")
    
    try:
        old_analyzer = LDATopicAnalyzer()
        metadata = old_analyzer.load_model(model_path)
        
        print(f"\nAltes Modell:")
        print(f"  - Topics: {metadata.get('num_topics', 'N/A')}")
        print(f"  - Vokabular: {metadata.get('vocabulary_size', 'N/A')}")
        print(f"  - Dokumente: {metadata.get('num_documents', 'N/A')}")
        print(f"  - Trainiert: {metadata.get('trained_at', 'N/A')}")
        print(f"  - Bigrams: {'✓' if metadata.get('has_bigrams') else '✗'}")
        print(f"  - Trigrams: {'✓' if metadata.get('has_trigrams') else '✗'}")
        
        if not metadata.get('has_bigrams'):
            print("\n💡 Altes Modell hat keine Bigrams/Trigrams!")
            print("   → Trainiere ein neues Modell für bessere Ergebnisse.")
        
        # Show topics from old model
        print("\nTopics vom alten Modell:")
        topics = old_analyzer.get_topics(num_words=8)
        for topic in topics:
            words = [w['word'] for w in topic['words'][:5]]
            print(f"  Topic {topic['topic_id']}: {', '.join(words)}")
            
    except Exception as e:
        print(f"\n❌ Fehler beim Laden: {e}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🎯 TEST: Verbesserte LDA Topics für Arbeitsthemen")
    print("=" * 60)
    
    # Run tests
    test_preprocessing()
    test_bigrams_trigrams()
    test_topic_quality()
    compare_with_old_model()
    
    print("\n" + "=" * 60)
    print("✅ Tests abgeschlossen!")
    print("=" * 60)
    print("\nNächste Schritte:")
    print("1. Überprüfe die Topic-Qualität in der Ausgabe")
    print("2. Justiere Parameter falls nötig (num_topics, passes, etc.)")
    print("3. Füge weitere domain-spezifische Stopwords hinzu falls nötig")
    print("4. Trainiere das Modell über die API für Produktionseinsatz:")
    print("   POST /api/topics/train")
    print()


if __name__ == "__main__":
    main()
