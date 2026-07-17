"""
Endpoint-Tests der Anomalie- und Erklärungs-Routen
(FastAPI TestClient + In-Memory-Store).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_autodetect_returns_and_persists():
    res = client.get("/api/anomalies/company/3",
                     params={"dimension": "durchschnittsbewertung"})
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 1
    falls_2023 = [a for a in data["anomalies"]
                  if a["direction"] == "fall" and a["period"].startswith("2023")]
    assert falls_2023, "Demo 3 muss einen Einbruch 2023 zeigen"
    anomaly = falls_2023[0]
    assert anomaly["dimension_label"] == "Gesamtbewertung"
    assert anomaly["window_start"] < anomaly["window_end"]
    assert anomaly["method"] == "pelt"
    assert anomaly["params"]["penalty"] == 0.5

    # Zweiter Aufruf: identisch (persistiert, kein erneuter Lauf)
    res2 = client.get("/api/anomalies/company/3",
                      params={"dimension": "durchschnittsbewertung"})
    assert res2.json()["count"] == data["count"]


def test_detect_with_custom_params_replaces():
    res = client.post("/api/anomalies/company/3/detect", json={
        "method": "zscore", "z_threshold": 1.5,
        "dimensions": ["durchschnittsbewertung"],
    })
    assert res.status_code == 200
    data = res.json()
    assert data["params_used"]["method"] == "zscore"
    assert data["detected"] >= 1
    listed = client.get("/api/anomalies/company/3",
                        params={"dimension": "durchschnittsbewertung",
                                "method": "zscore"}).json()
    assert listed["count"] == data["detected"]


def test_series_endpoint():
    res = client.get("/api/anomalies/company/3/series",
                     params={"dimension": "kommunikation"})
    assert res.status_code == 200
    data = res.json()
    assert data["dimension_label"] == "Kommunikation"
    assert len(data["series"]) > 12
    assert {"period", "value", "count"} <= set(data["series"][0].keys())


def test_series_unknown_dimension_400():
    res = client.get("/api/anomalies/company/3/series",
                     params={"dimension": "gibt_es_nicht"})
    assert res.status_code == 400


def test_explanations_flow():
    client.get("/api/anomalies/company/3")  # sicherstellen, dass Anomalien existieren
    gen = client.post("/api/explanations/company/3/generate",
                      json={"with_sentiment": False})
    assert gen.status_code == 200
    assert gen.json()["explanations_created"] > 0

    listed = client.get("/api/explanations/company/3")
    assert listed.status_code == 200
    data = listed.json()
    assert data["coverage"]["total_anomalies"] > 0
    first_with = next(item for item in data["items"] if item["explanations"])
    exp = first_with["explanations"][0]
    assert {"erklaerungstext", "quelle", "correspondence_score", "rank"} <= set(exp.keys())

    cov = client.get("/api/explanations/company/3/coverage")
    assert cov.status_code == 200
    assert cov.json()["coverage"] is not None


def test_context_endpoints():
    overview = client.get("/api/context/company/3")
    assert overview.status_code == 200
    assert overview.json()["ticker"] == "DEMO3.DE"

    stock = client.get("/api/context/company/3/stock")
    assert stock.status_code == 200
    assert len(stock.json()["monthly"]) > 24

    kpis = client.get("/api/context/company/3/kpis")
    assert kpis.status_code == 200
    assert kpis.json()["market_cap"] == 1_800_000_000

    news = client.get("/api/context/company/3/news",
                      params={"start": "2023-01-01", "end": "2023-03-31"})
    assert news.status_code == 200
    assert news.json()["count"] >= 2

    suggestions = client.get("/api/context/ticker-suggestions", params={"q": "sap"})
    assert suggestions.status_code == 200
    assert any(s["ticker"] == "SAP.DE" for s in suggestions.json()["suggestions"])
