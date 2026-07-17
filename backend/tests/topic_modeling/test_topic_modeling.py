"""
Quick test script to verify LDA Topic Modeling installation and functionality.
"""

import sys


def test_imports():
    """Test if all required packages are installed."""
    print("Testing imports...")
    
    try:
        import gensim
        print(f"✓ Gensim version: {gensim.__version__}")
    except ImportError as e:
        print(f"✗ Gensim import failed: {e}")
        return False
    
    try:
        from models.lda_topic_model import LDATopicAnalyzer
        print("✓ LDATopicAnalyzer imported successfully")
    except ImportError as e:
        print(f"✗ LDATopicAnalyzer import failed: {e}")
        return False
    
    try:
        from services.topic_model_service import TopicModelDatabase
        print("✓ TopicModelDatabase imported successfully")
    except ImportError as e:
        print(f"✗ TopicModelDatabase import failed: {e}")
        return False
    
    return True


def test_basic_functionality():
    """Test basic LDA functionality."""
    print("\nTesting basic functionality...")
    
    try:
        from models.lda_topic_model import LDATopicAnalyzer
        
        # Create sample texts
        texts = [
            "Die Arbeitsatmosphäre ist sehr gut und das Team ist hervorragend",
            "Die Bezahlung ist fair und die Sozialleistungen sind ausgezeichnet",
            "Work-Life-Balance ist gut, flexible Arbeitszeiten sind möglich",
            "Die Kommunikation im Team funktioniert einwandfrei",
            "Karrieremöglichkeiten sind vorhanden und Weiterbildung wird gefördert"
        ]
        
        # Initialize analyzer
        analyzer = LDATopicAnalyzer(num_topics=2)
        print("✓ LDATopicAnalyzer initialized")
        
        # Train model
        result = analyzer.train_model(texts)
        print(f"✓ Model trained on {result['num_documents']} documents")
        print(f"✓ Vocabulary size: {result['vocabulary_size']}")
        print(f"✓ Number of topics: {result['num_topics']}")
        
        # Get topics
        topics = analyzer.get_topics(num_words=5)
        print(f"✓ Retrieved {len(topics)} topics")
        
        # Test prediction
        test_text = "Das Team arbeitet gut zusammen und die Atmosphäre ist angenehm"
        predictions = analyzer.predict_topics(test_text)
        print(f"✓ Prediction successful, found {len(predictions)} relevant topics")
        
        return True
        
    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_connection():
    """Test database connectivity (optional)."""
    print("\nTesting database connection...")
    
    try:
        from services.topic_model_service import TopicModelDatabase
        
        db = TopicModelDatabase()
        stats = db.get_statistics()
        
        print(f"✓ Database connected")
        print(f"  - Candidates: {stats['candidates_total']}")
        print(f"  - Employees: {stats['employee_total']}")
        print(f"  - Total: {stats['total_records']}")
        
        return True
        
    except Exception as e:
        print(f"⚠ Database connection failed: {e}")
        print("  This is OK if database is not configured yet")
        return None  # None means optional test failed


def main():
    """Run all tests."""
    print("=" * 60)
    print("LDA TOPIC MODELING - INSTALLATION TEST")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: Basic functionality
    if results[0][1]:  # Only if imports succeeded
        results.append(("Basic Functionality", test_basic_functionality()))
    else:
        print("\n⚠ Skipping functionality test due to import errors")
        results.append(("Basic Functionality", False))
    
    # Test 3: Database (optional)
    if results[0][1]:  # Only if imports succeeded
        db_result = test_database_connection()
        results.append(("Database Connection", db_result))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        if result is True:
            status = "✓ PASSED"
        elif result is False:
            status = "✗ FAILED"
        else:
            status = "⚠ SKIPPED (optional)"
        print(f"{test_name:.<40} {status}")
    
    # Overall result
    critical_tests = [r for r in results if r[0] != "Database Connection"]
    all_passed = all(result for _, result in critical_tests)
    
    print("=" * 60)
    if all_passed:
        print("✓ All critical tests passed!")
        print("\nNext steps:")
        print("1. Start the backend: uvicorn main:app --reload")
        print("2. Visit: http://localhost:8000/docs")
        print("3. Try: POST /api/topics/train")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("- Make sure gensim is installed: pip install gensim")
        print("- Check that all files are in the correct directories")
        print("- Run from the backend directory")
        return 1


if __name__ == "__main__":
    sys.exit(main())
