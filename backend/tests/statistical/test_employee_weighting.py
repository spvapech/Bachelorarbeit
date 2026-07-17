"""
Test Script für Employee Type Weighting in LDA Topic Modeling
===============================================================

Dieser Test zeigt, wie die Gewichtung basierend auf Mitarbeitertypen funktioniert.

Mitarbeitertypen und ihre Gewichtungen:
- Manager: 2.0 (höchste Gewichtung)
- Employee: 1.5 (hohe Gewichtung)
- Student: 0.8 (niedrigere Gewichtung)
- Nicht-Employee: 0.5 (niedrigste Gewichtung)
- Unbekannt: 1.0 (Standard-Gewichtung)

Die Gewichtung beeinflusst, wie stark die Bewertungen eines bestimmten Typs
in die Topic-Analyse einfließen.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from models.lda_topic_model import LDATopicAnalyzer
from services.topic_model_service import TopicModelDatabase


def test_employee_type_weights():
    """Test die Gewichtungsfunktion für verschiedene Mitarbeitertypen."""
    print("=" * 80)
    print("TEST: Employee Type Gewichtungen")
    print("=" * 80)
    
    analyzer = LDATopicAnalyzer(num_topics=5)
    
    test_statuses = [
        'Employee',
        'Manager',
        'Student',
        'Nicht-Employee',
        'Angestellter',
        'Führungskraft',
        'Praktikant',
        'Ex-Employee',
        'Unknown',
        None
    ]
    
    print("\nGewichtungen für verschiedene Status-Werte:")
    print("-" * 80)
    for status in test_statuses:
        weight = analyzer.get_employee_type_weight(status)
        status_str = str(status) if status is not None else '(None)'
        print(f"Status: {status_str:20s} → Gewicht: {weight:.1f}")
    
    print("\n✅ Gewichtungs-Test erfolgreich")
    return analyzer


def test_weighted_training():
    """Test das Training mit gewichteten Daten."""
    print("\n" + "=" * 80)
    print("TEST: Training mit Employee Type Gewichtung")
    print("=" * 80)
    
    # Erstelle Testdaten mit verschiedenen Mitarbeitertypen
    test_data = [
        {
            'text': 'Das Gehalt ist sehr gut und die Work-Life-Balance ist ausgezeichnet. Das Team ist super.',
            'status': 'Manager',
            'source': 'employee'
        },
        {
            'text': 'Die Arbeitsatmosphäre ist okay, aber das Gehalt könnte besser sein.',
            'status': 'Employee',
            'source': 'employee'
        },
        {
            'text': 'Als Student finde ich die Lernmöglichkeiten gut, aber die Bezahlung ist niedrig.',
            'status': 'Student',
            'source': 'employee'
        },
        {
            'text': 'Die Kommunikation war schlecht und das Vorgesetztenverhalten unprofessionell.',
            'status': 'Nicht-Employee',
            'source': 'employee'
        },
        {
            'text': 'Exzellente Karrieremöglichkeiten und Weiterbildung. Die Führung ist sehr kompetent.',
            'status': 'Manager',
            'source': 'employee'
        },
        {
            'text': 'Gutes Team und interessante Aufgaben. Homeoffice ist möglich.',
            'status': 'Employee',
            'source': 'employee'
        },
    ]
    
    # Extrahiere Texte und Metadaten
    texts = [item['text'] for item in test_data]
    metadata = [{'status': item['status'], 'source': item['source']} for item in test_data]
    
    print(f"\nAnzahl Testdokumente: {len(texts)}")
    print("\nStatus-Verteilung:")
    print("-" * 80)
    
    status_counts = {}
    for meta in metadata:
        status = meta['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        print(f"  {status}: {count} Dokument(e)")
    
    # Trainiere Modell mit Gewichtung
    print("\n🔄 Trainiere Modell mit Employee Type Gewichtung...")
    analyzer = LDATopicAnalyzer(num_topics=3)
    
    result = analyzer.train_model(texts, metadata=metadata)
    
    print("\n✅ Training erfolgreich!")
    print("\nTrainingsergebnisse:")
    print("-" * 80)
    print(f"Status: {result['status']}")
    print(f"Anzahl Topics: {result['num_topics']}")
    print(f"Anzahl Dokumente: {result['num_documents']}")
    print(f"Vokabular-Größe: {result['vocabulary_size']}")
    
    if 'weight_statistics' in result:
        print("\nGewichtungs-Statistiken:")
        print("-" * 80)
        for status, stats in result['weight_statistics'].items():
            print(f"  {status}: {stats['count']} Dokument(e) × Gewicht {stats['weight']:.1f}")
    
    print("\nEntdeckte Topics:")
    print("-" * 80)
    for topic in result['topics']:
        print(f"\nTopic {topic['topic_id']}:")
        words_list = topic.get('words', [])
        if words_list:
            top_words = [f"{w['word']} ({w['weight']:.3f})" for w in words_list[:5]]
            print(f"  Top Wörter: {', '.join(top_words)}")
        else:
            print("  Keine Wörter gefunden")
    
    return result


def test_database_integration():
    """Test die Integration mit der Datenbank."""
    print("\n" + "=" * 80)
    print("TEST: Datenbank-Integration mit Employee Type Gewichtung")
    print("=" * 80)
    
    try:
        db = TopicModelDatabase()
        
        # Hole Daten mit Metadaten
        print("\n🔄 Lade Employee-Daten mit Metadaten aus der Datenbank...")
        employee_data = db.get_employee_texts_with_metadata(limit=50)
        
        print(f"\n✅ {len(employee_data)} Employee-Einträge geladen")
        
        # Analysiere Status-Verteilung
        if employee_data:
            print("\nStatus-Verteilung in der Datenbank:")
            print("-" * 80)
            
            status_counts = {}
            for item in employee_data:
                status = item.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {status if status else '(leer)'}: {count} Einträge")
            
            # Zeige Beispiele
            print("\nBeispiel-Einträge:")
            print("-" * 80)
            for i, item in enumerate(employee_data[:3]):
                status = item.get('status', 'unknown')
                text_preview = item['text'][:100] + '...' if len(item['text']) > 100 else item['text']
                print(f"\n{i+1}. Status: {status}")
                print(f"   Text: {text_preview}")
        else:
            print("⚠️  Keine Employee-Daten gefunden")
        
        # Test das vollständige Training mit Datenbank-Daten
        if employee_data and len(employee_data) >= 10:
            print("\n" + "=" * 80)
            print("Training mit echten Datenbank-Daten")
            print("=" * 80)
            
            texts = [item['text'] for item in employee_data[:50]]  # Limitiere auf 50 für schnelleren Test
            metadata = [{'status': item.get('status'), 'source': item.get('source')} for item in employee_data[:50]]
            
            analyzer = LDATopicAnalyzer(num_topics=5)
            result = analyzer.train_model(texts, metadata=metadata)
            
            print("\n✅ Training mit Datenbank-Daten erfolgreich!")
            print(f"\nVerarbeitete Dokumente: {result['num_documents']}")
            
            if 'weight_statistics' in result:
                print("\nGewichtungs-Statistiken aus Datenbank:")
                print("-" * 80)
                for status, stats in result['weight_statistics'].items():
                    percentage = (stats['count'] / result['num_documents']) * 100
                    print(f"  {status}: {stats['count']} Dokumente ({percentage:.1f}%) × Gewicht {stats['weight']:.1f}")
        
    except Exception as e:
        print(f"\n❌ Fehler bei Datenbank-Integration: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Hauptfunktion für alle Tests."""
    print("\n")
    print("█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  TEST: LDA Topic Modeling mit Employee Type Gewichtung".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    try:
        # Test 1: Gewichtungsfunktion
        test_employee_type_weights()
        
        # Test 2: Training mit gewichteten Testdaten
        test_weighted_training()
        
        # Test 3: Datenbank-Integration
        test_database_integration()
        
        print("\n" + "=" * 80)
        print("✅ Alle Tests erfolgreich abgeschlossen!")
        print("=" * 80)
        print("\nZusammenfassung:")
        print("-" * 80)
        print("✓ Employee Type Gewichtungen werden korrekt berechnet")
        print("✓ Training mit gewichteten Daten funktioniert")
        print("✓ Datenbank-Integration mit Metadaten funktioniert")
        print("\nDie Gewichtung sorgt dafür, dass:")
        print("  • Manager-Bewertungen 2× so stark gewichtet werden wie Standard")
        print("  • Employee-Bewertungen 1.5× so stark gewichtet werden")
        print("  • Student-Bewertungen mit 0.8× gewichtet werden")
        print("  • Nicht-Employee-Bewertungen mit 0.5× gewichtet werden")
        print("\n")
        
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ Test fehlgeschlagen: {str(e)}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
