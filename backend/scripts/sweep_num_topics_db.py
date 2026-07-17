"""
Sweep Script: evaluate num_topics on real DB data

Lädt Texte über `TopicModelDatabase.get_all_texts` und führt einen Sweep
für k in 5..20 durch. Gibt Coherence (c_v) für jedes k aus und wählt das
beste k basierend auf maximaler Coherence.
"""
from models.lda_topic_model import LDATopicAnalyzer
from services.topic_model_service import TopicModelDatabase
from gensim.models import CoherenceModel
import sys


def load_data(limit=None):
    db = TopicModelDatabase()
    data = db.get_all_texts(source='both', limit=limit, include_metadata=True)
    texts = data.get('texts', [])
    metadata = data.get('detailed_metadata')
    return texts, metadata, data.get('metadata', {})


def sweep(texts, metadata=None, start=5, end=20):
    results = {}
    for k in range(start, end + 1):
        print(f"\nTraining k={k} ...")
        analyzer = LDATopicAnalyzer(num_topics=k)
        analyzer.train_model(texts, metadata=metadata)

        cm = CoherenceModel(model=analyzer.lda_model, texts=analyzer.documents, dictionary=analyzer.dictionary, coherence='c_v')
        coherence = cm.get_coherence()
        results[k] = coherence
        print(f"k={k} => Coherence (c_v) = {coherence:.4f}")
    return results


def main(limit=None):
    try:
        texts, metadata, stats = load_data(limit=limit)
    except Exception as e:
        print("Fehler beim Laden der Daten aus der Datenbank:", str(e))
        print("Stelle sicher, dass Supabase-Zugangsdaten (.env) korrekt sind.")
        sys.exit(1)

    print(f"Geladene Dokumente: {len(texts)} (candidates={stats.get('candidates_count')}, employee={stats.get('employee_count')})")

    if not texts:
        print("Keine Dokumente zum Trainieren gefunden. Abbruch.")
        sys.exit(1)

    results = sweep(texts, metadata)

    best_k = max(results, key=results.get)
    print('\nSweep abgeschlossen.')
    print(f"Bestes k: {best_k} mit Coherence {results[best_k]:.4f}")


if __name__ == '__main__':
    # Optional: Limit records for faster testing via CLI arg
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass
    main(limit=limit)
