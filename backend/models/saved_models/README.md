# LDA Saved Models

Dieser Ordner enthält gespeicherte LDA Topic Models.

## Struktur

Jedes Modell besteht aus mehreren Dateien:
- `lda_model_YYYYMMDD_HHMMSS.model` - Hauptmodell
- `lda_model_YYYYMMDD_HHMMSS.dict` - Wörterbuch
- `lda_model_YYYYMMDD_HHMMSS.meta` - Metadaten
- `lda_model_YYYYMMDD_HHMMSS.bigram` - Bigram-Modell
- `lda_model_YYYYMMDD_HHMMSS.trigram` - Trigram-Modell
- `lda_model_YYYYMMDD_HHMMSS.model.id2word` - ID-zu-Wort-Mapping
- `lda_model_YYYYMMDD_HHMMSS.model.state` - Modellzustand
- `lda_model_YYYYMMDD_HHMMSS.model.expElogbeta.npy` - NumPy-Array

## Verwendung

### Modell speichern
```python
from models.lda_topic_model import LDATopicAnalyzer

analyzer = LDATopicAnalyzer(num_topics=8)
analyzer.train_model(texts)
model_path = analyzer.save_model()  # Speichert automatisch hier
```

### Modell laden
```python
analyzer = LDATopicAnalyzer()
analyzer.load_model("models/saved_models/lda_model_20260105_123456")
```

### Via API
```bash
# Liste aller Modelle
GET /api/topics/models/list

# Modell laden
POST /api/topics/models/load?model_name=lda_model_20260105_123456
```

## Hinweise

- Modelle werden automatisch mit Zeitstempel benannt
- Alte Modelle bleiben erhalten (keine automatische Löschung)
- Modelle sind groß (~100-500 KB pro Modell)
- .gitignore ist konfiguriert, um Modelle nicht zu committen
