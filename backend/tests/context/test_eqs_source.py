"""
Tests des EQS-Adapters: Normalisierung der Meldungen, Aufbereitung des
Volltexts und Kategorienfilter — durchgängig offline gegen fixierte
Beispielantworten der Schnittstelle.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.context_sources import eqs_source


# Gekürzte, aber strukturgetreue Ad-hoc-Meldung (Aufbau: Kopfblock,
# Meldungstext, Fußblock) nach dem Muster echter EQS-Antworten.
ADHOC_HTML = """
<html><body><table><tr><td>
<p>Bayer Aktiengesellschaft / Schlagwort(e): Prognose&auml;nderung<br/>
Bayer Aktiengesellschaft: Bayer senkt Ausblick f&uuml;r das Gesch&auml;ftsjahr <br/><br/>
24.07.2023 / 19:32 CET/CEST<br/>
Ver&ouml;ffentlichung einer Insiderinformation nach Artikel 17 der Verordnung
(EU) Nr. 596/2014, &uuml;bermittelt durch EQS News - ein Service der EQS Group AG.<br/>
F&uuml;r den Inhalt der Mitteilung ist der Emittent / Herausgeber verantwortlich.<br/>
Leverkusen, 24. Juli 2023 &ndash; Der Bayer-Konzern hat den Ausblick f&uuml;r das
Gesch&auml;ftsjahr 2023 gesenkt. Grund sind vor allem die zur&uuml;ckgegangenen
Ums&auml;tze mit glyphosatbasierten Produkten.<br/>
Ende der Mitteilung<br/>
Sprache: Deutsch<br/>Unternehmen: Bayer Aktiengesellschaft</p>
</td></tr></table></body></html>
"""


# ── Volltextaufbereitung ─────────────────────────────────────────────────────

def test_summary_entfernt_kopf_und_fussblock():
    summary = eqs_source._summary(ADHOC_HTML, "Bayer Aktiengesellschaft: Bayer senkt "
                                              "Ausblick für das Geschäftsjahr")
    assert summary is not None
    # Meldungsinhalt bleibt erhalten
    assert "glyphosatbasierten Produkten" in summary
    assert "Leverkusen, 24. Juli 2023" in summary
    # Formalbausteine sind entfernt
    assert "Insiderinformation" not in summary
    assert "Herausgeber verantwortlich" not in summary
    assert "Schlagwort" not in summary
    assert "Ende der Mitteilung" not in summary
    assert "Sprache: Deutsch" not in summary


def test_summary_ohne_inhalt_liefert_none():
    """Enthält eine Meldung nur Formalbausteine, entsteht keine Zusammenfassung."""
    nur_boilerplate = ("<p>Muster AG / Schlagwort(e): Sonstiges<br/>"
                       "Für den Inhalt der Mitteilung ist der Emittent / Herausgeber "
                       "verantwortlich.<br/>Ende der Mitteilung</p>")
    assert eqs_source._summary(nur_boilerplate, "Muster AG") is None


def test_summary_kuerzt_an_satzgrenze():
    lang = "<p>" + ("Ein vollständiger Satz zum Geschäftsverlauf. " * 60) + "</p>"
    summary = eqs_source._summary(lang, "", limit=300)
    assert summary is not None
    assert len(summary) <= 300
    assert summary.endswith(".")


def test_plaintext_entfernt_markup_und_entities():
    assert eqs_source._plaintext("<p>Umsatz&nbsp;&uuml;ber <b>Plan</b></p>") == "Umsatz über Plan"


def test_plaintext_leer():
    assert eqs_source._plaintext(None) == ""
    assert eqs_source._plaintext("") == ""


# ── Datums- und Antwortnormalisierung ────────────────────────────────────────

def test_published_iso_bevorzugt_utc_feld():
    record = {"dateUtc": "2023-07-24 17:32:24", "date": "2023-07-24 19:32:24"}
    assert eqs_source._published_iso(record).startswith("2023-07-24T17:32:24")


def test_published_iso_faellt_auf_lokalzeit_zurueck():
    assert eqs_source._published_iso({"date": "2023-07-24 19:32:24"}).startswith("2023-07-24T19:32:24")


def test_published_iso_ohne_datum():
    assert eqs_source._published_iso({"headline": "ohne Datum"}) is None


def test_records_akzeptiert_liste_und_einzelobjekt():
    assert eqs_source._records({"records": [{"id": "a"}, {"id": "b"}]}) == [{"id": "a"}, {"id": "b"}]
    assert eqs_source._records({"records": {"id": "a"}}) == [{"id": "a"}]
    assert eqs_source._records({"records": None}) == []
    assert eqs_source._records("kein dict") == []


# ── Kategorienfilter und Normalisierung der Meldungen ────────────────────────

def _antwort(records):
    return {"status": 200, "records": records}


def test_fetch_adhoc_filtert_formalmeldungen(monkeypatch):
    """
    Stimmrechtsmitteilungen, Directors' Dealings und Finanztermine sind
    Formalmeldungen ohne Erklärungswert und dürfen nicht übernommen werden.
    """
    seite = [
        {"id": "1_en", "categoryCode": "adhoc", "category": "Ad-hoc",
         "headline": "Muster AG: Prognose gesenkt", "dateUtc": "2023-05-02 08:00:00",
         "isin": "DE0001234567"},
        {"id": "2_en", "categoryCode": "PVR", "category": "Voting rights",
         "headline": "Stimmrechtsmitteilung", "dateUtc": "2023-05-03 08:00:00",
         "isin": "DE0001234567"},
        {"id": "3_en", "categoryCode": "dd", "category": "Directors' Dealings",
         "headline": "Eigengeschäft", "dateUtc": "2023-05-04 08:00:00",
         "isin": "DE0001234567"},
        {"id": "4_en", "categoryCode": "corporate", "category": "Corporate",
         "headline": "Muster AG: Neuer Standort", "dateUtc": "2023-05-05 08:00:00",
         "isin": "DE0001234567"},
        {"id": "5_en", "categoryCode": "AFR", "category": "Advance financial reports",
         "headline": "Finanztermin", "dateUtc": "2023-05-06 08:00:00",
         "isin": "DE0001234567"},
    ]
    monkeypatch.setattr(eqs_source, "_api_get", lambda path, params: _antwort(
        seite if path == "news" and params.get("page") is None else []
    ))

    items, errors = eqs_source.fetch_adhoc("Muster AG", isin="DE0001234567",
                                           with_detail=False)
    assert errors == []
    assert [i["titel"] for i in items] == ["Muster AG: Prognose gesenkt",
                                           "Muster AG: Neuer Standort"]
    # Ad-hoc und Corporate News werden auf getrennte source_types abgebildet
    assert [i["source_type"] for i in items] == ["adhoc", "news"]
    assert all(i["provider"] == "eqs" for i in items)


def test_fetch_adhoc_dedupliziert_sprachfassungen(monkeypatch):
    """Dieselbe Meldung erscheint je Sprache einmal — übernommen wird eine."""
    seite = [
        {"id": "abc_de", "categoryCode": "adhoc", "category": "Ad-hoc",
         "headline": "Muster AG: Prognose gesenkt", "dateUtc": "2023-05-02 08:00:00"},
        {"id": "abc_en", "categoryCode": "adhoc", "category": "Ad-hoc",
         "headline": "Muster AG: Outlook lowered", "dateUtc": "2023-05-02 08:00:00"},
    ]
    monkeypatch.setattr(eqs_source, "_api_get", lambda path, params: _antwort(
        seite if params.get("page") is None else []
    ))
    items, _ = eqs_source.fetch_adhoc("Muster AG", isin="DE0001234567", with_detail=False)
    assert len(items) == 1


def test_fetch_adhoc_ohne_isin_meldet_fehler(monkeypatch):
    """Ohne auflösbare ISIN liefert der Adapter eine Meldung statt einer Ausnahme."""
    monkeypatch.setattr(eqs_source, "resolve_isin", lambda name: None)
    items, errors = eqs_source.fetch_adhoc("Nicht Börsennotiert GmbH")
    assert items == []
    assert len(errors) == 1 and "keine ISIN" in errors[0]


def test_fetch_adhoc_bricht_bei_quellenfehler_nicht_ab(monkeypatch):
    """Ein Transportfehler führt zu einer Fehlermeldung, nicht zum Abbruch."""
    def kaputt(path, params):
        raise OSError("Zeitüberschreitung")
    monkeypatch.setattr(eqs_source, "_api_get", kaputt)

    items, errors = eqs_source.fetch_adhoc("Muster AG", isin="DE0001234567")
    assert items == []
    assert len(errors) == 1 and "Zeitüberschreitung" in errors[0]


def test_fetch_adhoc_paginiert_bis_zur_letzten_seite(monkeypatch):
    """
    Die erste Seite wird ohne `page` angefragt (Eigenheit der Schnittstelle),
    Folgeseiten mit `page=2`, `page=3`, … bis eine Teilseite zurückkommt.
    """
    angefragt = []

    def seiten(path, params):
        angefragt.append(params.get("page"))
        page = params.get("page") or 1
        if page > 2:
            return _antwort([])
        anzahl = eqs_source._PER_PAGE if page == 1 else 3
        return _antwort([
            {"id": f"{page}-{n}_en", "categoryCode": "adhoc", "category": "Ad-hoc",
             "headline": f"Meldung {page}-{n}", "dateUtc": "2023-05-02 08:00:00"}
            for n in range(anzahl)
        ])

    monkeypatch.setattr(eqs_source, "_api_get", seiten)
    items, errors = eqs_source.fetch_adhoc("Muster AG", isin="DE0001234567",
                                           with_detail=False)
    assert errors == []
    assert angefragt[0] is None          # erste Seite ohne page-Parameter
    assert angefragt[1] == 2
    assert len(items) == eqs_source._PER_PAGE + 3


def test_fetch_adhoc_sortiert_chronologisch(monkeypatch):
    seite = [
        {"id": "b_en", "categoryCode": "adhoc", "category": "Ad-hoc",
         "headline": "Später", "dateUtc": "2023-09-01 08:00:00"},
        {"id": "a_en", "categoryCode": "adhoc", "category": "Ad-hoc",
         "headline": "Früher", "dateUtc": "2023-03-01 08:00:00"},
    ]
    monkeypatch.setattr(eqs_source, "_api_get", lambda path, params: _antwort(
        seite if params.get("page") is None else []
    ))
    items, _ = eqs_source.fetch_adhoc("Muster AG", isin="DE0001234567", with_detail=False)
    assert [i["titel"] for i in items] == ["Früher", "Später"]


# ── ISIN-Auflösung ───────────────────────────────────────────────────────────

def test_resolve_isin_waehlt_namensgleichen_emittenten(monkeypatch):
    treffer = (
        [{"companyName": "Siemens Aktiengesellschaft", "isin": "DE0007236101"}] * 5
        + [{"companyName": "Siemens Healthineers AG", "isin": "DE000SHL1006"}] * 9
    )
    monkeypatch.setattr(eqs_source, "_api_get", lambda path, params: _antwort(treffer))
    # Trotz geringerer Trefferzahl gewinnt der exakte Namenstreffer
    assert eqs_source.resolve_isin("Siemens AG")["isin"] == "DE0007236101"


def test_resolve_isin_sucht_ohne_rechtsform(monkeypatch):
    """
    Die Volltextsuche wertet den Suchbegriff als zusammenhängende Zeichenkette:
    'Deutsche Lufthansa AG' liefert keinen Treffer, 'Deutsche Lufthansa' schon.
    """
    gesucht = []

    def suche(path, params):
        gesucht.append(params.get("search"))
        if params.get("search") == "Deutsche Lufthansa":
            return _antwort([{"companyName": "Deutsche Lufthansa AG",
                              "isin": "DE0008232125"}] * 12)
        return _antwort([])

    monkeypatch.setattr(eqs_source, "_api_get", suche)
    treffer = eqs_source.resolve_isin("Deutsche Lufthansa AG")
    assert treffer["isin"] == "DE0008232125"
    assert gesucht[0] == "Deutsche Lufthansa"  # Rechtsform zuerst entfernt


def test_resolve_isin_faellt_auf_vollen_namen_zurueck(monkeypatch):
    """Bleibt die Suche ohne Rechtsform leer, wird der volle Name versucht."""
    gesucht = []

    def suche(path, params):
        gesucht.append(params.get("search"))
        if params.get("search") == "Muster Group":
            return _antwort([{"companyName": "Muster Group", "isin": "DE0001234567"}] * 3)
        return _antwort([])

    monkeypatch.setattr(eqs_source, "_api_get", suche)
    assert eqs_source.resolve_isin("Muster Group")["isin"] == "DE0001234567"
    assert gesucht == ["Muster", "Muster Group"]


def test_resolve_isin_verwirft_fremde_emittenten(monkeypatch):
    """
    Für nicht börsennotierte Unternehmen liefert die Volltextsuche fremde
    Emittenten. Ohne Namensbezug wird kein Treffer akzeptiert — sonst würden
    einer Anomalie fremde Ereignisse zugeordnet.
    """
    monkeypatch.setattr(eqs_source, "_api_get", lambda path, params: _antwort(
        [{"companyName": "FCR Immobilien AG", "isin": "DE000A1YC913"}] * 40
    ))
    assert eqs_source.resolve_isin("Rewe") is None


def test_resolve_isin_ignoriert_platzhalter_isins(monkeypatch):
    monkeypatch.setattr(eqs_source, "_api_get", lambda path, params: _antwort(
        [{"companyName": "Muster AG", "isin": "noisin339926"}]
    ))
    assert eqs_source.resolve_isin("Muster AG") is None
