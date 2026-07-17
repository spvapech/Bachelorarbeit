"""
Skript zum Trainieren der LDA-Modelle für Bewerber und Mitarbeiter
"""
import asyncio
from services.topic_model_service import TopicModelDatabase
from models.lda_topic_model import LDATopicAnalyzer

async def train_models():
    print("=" * 60)
    print("Starte Training der LDA-Modelle")
    print("=" * 60)
    
    # Initialisiere Database Service
    topic_db = TopicModelDatabase()
    
    # 1. Trainiere Modell für BEIDE (Kombiniert)
    print("\n[1/3] Trainiere kombiniertes Modell (Bewerber + Mitarbeiter)...")
    print("-" * 60)
    
    data = topic_db.get_all_texts(
        source="both",
        limit=None,
        include_metadata=True
    )
    
    print(f"✓ Geladene Daten:")
    print(f"  - Bewerber: {data['metadata']['candidates_count']}")
    print(f"  - Mitarbeiter: {data['metadata']['employee_count']}")
    print(f"  - Gesamt: {data['metadata']['total_count']}")
    
    if data["texts"]:
        analyzer = LDATopicAnalyzer(num_topics=15)
        result = analyzer.train_model(
            data["texts"],
            metadata=data.get("detailed_metadata")
        )
        
        # Speichere Modell
        model_path = analyzer.save_model()
        print(f"✓ Kombiniertes Modell gespeichert: {model_path}")
        if 'perplexity' in result:
            print(f"✓ Perplexity: {result['perplexity']:.2f}")
        if 'coherence_score' in result:
            print(f"✓ Coherence: {result['coherence_score']:.4f}")
    else:
        print("✗ Keine Daten gefunden!")
    
    print("\n" + "=" * 60)
    print("Training abgeschlossen!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(train_models())
