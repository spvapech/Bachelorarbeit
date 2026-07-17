"""
Vergleichstest: num_topics 8 vs 13

Dieses Skript trainiert zwei LDA-Modelle (8 und 13 Topics) auf
einem kleinen Beispieldatensatz und berechnet die Coherence (c_v).
"""
from models.lda_topic_model import LDATopicAnalyzer
from gensim.models import CoherenceModel


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


def train_and_evaluate(k):
    analyzer = LDATopicAnalyzer(num_topics=k)
    result = analyzer.train_model(sample_texts)

    # Berechne Coherence (c_v) basierend auf tokenisierten Dokumenten
    cm = CoherenceModel(
        model=analyzer.lda_model,
        texts=analyzer.documents,
        dictionary=analyzer.dictionary,
        coherence='c_v'
    )
    coherence = cm.get_coherence()

    print('\n' + '=' * 60)
    print(f'Model mit {k} Topics')
    print('=' * 60)
    print(f"Num Documents: {result['num_documents']}")
    print(f"Vocab size: {result['vocabulary_size']}")
    print(f"Coherence (c_v): {coherence:.4f}")

    # Zeige Top-Wörter jeder Topic
    for topic in result['topics']:
        words = [f"{w['word']} ({w['weight']:.3f})" for w in topic['words'][:7]]
        print(f"Topic {topic['topic_id']}: {', '.join(words)}")

    return coherence


def main():
    c8 = train_and_evaluate(8)
    c13 = train_and_evaluate(13)

    print('\nSummary:')
    print(f'  Coherence @8 : {c8:.4f}')
    print(f'  Coherence @13: {c13:.4f}')

    if c13 > c8:
        print('\nEmpfehlung: num_topics=13 liefert höhere Coherence auf diesem kleinen Korpus.')
    elif c13 < c8:
        print('\nEmpfehlung: num_topics=8 liefert höhere Coherence auf diesem kleinen Korpus.')
    else:
        print('\nEmpfehlung: Keine klare Verbesserung durch Wechsel auf 13 Topics.')


if __name__ == '__main__':
    main()
