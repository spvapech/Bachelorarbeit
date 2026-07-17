# Quickstart

> Vollständige Anleitung: [INSTALLATION.md](INSTALLATION.md)

---

## Voraussetzungen installieren

```bash
# uv (Python-Paketmanager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node.js 20+ prüfen
node --version   # muss v20+ sein → sonst: https://nodejs.org/
```

---

## 1 — Repository klonen

```bash
git clone https://github.com/IIS-Bachelorprojekt/gruppe-P1-3.git gruppe-P1-3
cd gruppe-P1-3
```

---

## 2 — Abhängigkeiten installieren

```bash
# Backend
cd backend && uv sync && cd ..

# Frontend
cd frontend && npm install && cd ..
```

---

## 3 — Umgebungsvariablen setzen

```bash
touch backend/.env
```

Öffne `backend/.env` und füge ein:

```env
SUPABASE_URL=https://dein-projekt.supabase.co
SUPABASE_KEY=dein-supabase-anon-key
```

> Zugangsdaten: [supabase.com](https://supabase.com) → Projekt → **Settings → API**

---

## 4 — Projekt starten

**Terminal 1 — Backend:**

```bash
cd backend
uv run uvicorn main:app --reload
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

| Dienst   | URL                          |
| -------- | ---------------------------- |
| Frontend | http://localhost:5173        |
| Backend  | http://localhost:8000        |
| API-Docs | http://localhost:8000/docs   |

---

## 5 — LDA-Modell trainieren (einmalig)

Das Backend muss laufen. Dann in einem neuen Terminal:

```bash
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "both", "num_topics": 5}'
```

---

## Schnellreferenz

```bash
cd backend && uv run uvicorn main:app --reload   # Backend starten
cd frontend && npm run dev                        # Frontend starten
cd backend && uv run pytest tests/               # Tests ausführen
```

## Häufige Fehler

| Fehler | Lösung |
| ------ | ------ |
| `uv: command not found` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` dann Terminal neu starten |
| Port 8000 belegt | `lsof -ti:8000 \| xargs kill -9` |
| `SUPABASE_URL ... required` | `backend/.env` fehlt oder ist leer → Schritt 3 wiederholen |
| `ModuleNotFoundError` | `cd backend && uv sync` |
| Frontend-Pakete fehlen | `cd frontend && rm -rf node_modules && npm install` |
