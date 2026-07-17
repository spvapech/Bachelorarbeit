"""
Example script demonstrating LDA Topic Modeling usage.
This script shows how to use the topic modeling functionality programmatically.
"""

from models.lda_topic_model import LDATopicAnalyzer
from services.topic_model_service import TopicModelDatabase


def example_1_basic_training():
    """Example 1: Basic model training with sample texts."""
    print("=" * 60)
    print("Example 1: Basic Model Training")
    print("=" * 60)
    
    # Sample texts (in real use, these come from the database)
    sample_texts = [
        "Die Arbeitsatmosphäre ist sehr gut und das Team arbeitet hervorragend zusammen.",
        "Die Kommunikation zwischen den Abteilungen könnte verbessert werden.",
        "Gehalt und Sozialleistungen sind fair und wettbewerbsfähig.",
        "Work-Life-Balance ist ausgezeichnet, flexible Arbeitszeiten sind möglich.",
        "Vorgesetzte sind kompetent und unterstützen die Mitarbeiter gut.",
        "Karrieremöglichkeiten sind begrenzt, mehr Weiterbildung wäre wünschenswert.",
        "Die technische Ausstattung ist modern und auf dem neuesten Stand.",
        "Zusammenarbeit im Team funktioniert reibungslos und effizient.",
        "Bewerbungsprozess war professionell und transparent.",
        "Feedback nach dem Vorstellungsgespräch kam schnell und war hilfreich."
    ]
    
    # Initialize and train model
    analyzer = LDATopicAnalyzer(num_topics=3)
    result = analyzer.train_model(sample_texts)
    
    print(f"\n✓ Model trained on {result['num_documents']} documents")
    print(f"✓ Vocabulary size: {result['vocabulary_size']} words")
    print(f"✓ Number of topics: {result['num_topics']}")
    
    # Display topics
    print("\nDiscovered Topics:")
    for topic in result['topics']:
        print(f"\nTopic {topic['topic_id']}:")
        words = [f"{w['word']} ({w['weight']:.3f})" for w in topic['words'][:5]]
        print(f"  Top words: {', '.join(words)}")
    
    return analyzer


def example_2_predict_topics(analyzer):
    """Example 2: Predict topics for new text."""
    print("\n" + "=" * 60)
    print("Example 2: Topic Prediction")
    print("=" * 60)
    
    test_texts = [
        "Das Team ist sehr kollegial und die Atmosphäre ist angenehm.",
        "Ich wünsche mir mehr Möglichkeiten zur Weiterbildung und Karriereentwicklung.",
        "Die Bezahlung entspricht den Erwartungen und ist marktgerecht."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nText {i}: {text[:50]}...")
        topics = analyzer.predict_topics(text, threshold=0.15)
        
        if topics:
            print("  Predicted topics:")
            for topic in topics:
                print(f"    - Topic {topic['topic_id']}: {topic['probability']:.2%}")
        else:
            print("  No topics with sufficient probability found")


def example_3_database_integration():
    """Example 3: Using database integration."""
    print("\n" + "=" * 60)
    print("Example 3: Database Integration")
    print("=" * 60)
    
    try:
        db = TopicModelDatabase()
        
        # Get statistics
        stats = db.get_statistics()
        print(f"\nDatabase Statistics:")
        print(f"  Candidates: {stats['candidates_total']}")
        print(f"  Employees: {stats['employee_total']}")
        print(f"  Total: {stats['total_records']}")
        
        # Fetch data for training
        print(f"\nFetching data from database...")
        data = db.get_all_texts(source="both", limit=50)
        
        print(f"  ✓ Retrieved {data['metadata']['total_count']} documents")
        print(f"    - Candidates: {data['metadata']['candidates_count']}")
        print(f"    - Employees: {data['metadata']['employee_count']}")
        
        if data['texts']:
            # Train model on real data
            analyzer = LDATopicAnalyzer(num_topics=5)
            result = analyzer.train_model(data['texts'])
            
            print(f"\n✓ Model trained successfully")
            print(f"  Topics discovered: {result['num_topics']}")
            print(f"  Vocabulary: {result['vocabulary_size']} unique words")
            
            # Save model
            model_path = analyzer.save_model()
            print(f"\n✓ Model saved to: {model_path}")
            
            return analyzer
        else:
            print("\n⚠ No text data found in database")
            return None
            
    except Exception as e:
        print(f"\n✗ Database error: {str(e)}")
        print("  Make sure:")
        print("  1. Supabase credentials are configured in .env")
        print("  2. Database tables exist and contain data")
        return None


def example_4_save_and_load():
    """Example 4: Save and load models."""
    print("\n" + "=" * 60)
    print("Example 4: Save and Load Models")
    print("=" * 60)
    
    # Train a simple model
    sample_texts = [
        "Gute Arbeitsatmosphäre und kollegiales Team",
        "Faire Bezahlung und gute Sozialleistungen",
        "Flexible Arbeitszeiten und Home-Office möglich",
        "Karrieremöglichkeiten sind vorhanden",
        "Moderne Ausstattung und Tools"
    ]
    
    analyzer1 = LDATopicAnalyzer(num_topics=2)
    analyzer1.train_model(sample_texts)
    
    # Save model
    model_path = analyzer1.save_model()
    print(f"\n✓ Model saved to: {model_path}")
    
    # Load model
    analyzer2 = LDATopicAnalyzer()
    metadata = analyzer2.load_model(model_path)
    
    print(f"\n✓ Model loaded successfully")
    print(f"  Topics: {metadata['num_topics']}")
    print(f"  Documents trained on: {metadata['num_documents']}")
    print(f"  Trained at: {metadata['trained_at']}")
    
    # Test loaded model
    test_text = "Das Team ist super und die Arbeitsbedingungen sind gut"
    topics = analyzer2.predict_topics(test_text)
    print(f"\n✓ Loaded model can predict:")
    print(f"  Text: {test_text}")
    print(f"  Topics: {topics}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("LDA TOPIC MODELING - EXAMPLES")
    print("=" * 60)
    
    # Example 1: Basic training
    analyzer = example_1_basic_training()
    
    # Example 2: Predictions
    example_2_predict_topics(analyzer)
    
    # Example 3: Database integration (may fail if no DB access)
    print("\n\nAttempting database integration...")
    db_analyzer = example_3_database_integration()
    
    # Example 4: Save and load
    example_4_save_and_load()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the FastAPI server: uvicorn main:app --reload")
    print("2. Visit http://localhost:8000/docs for API documentation")
    print("3. Try the API endpoints to train and use models")


if __name__ == "__main__":
    main()
