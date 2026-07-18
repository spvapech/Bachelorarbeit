-- Kombinierte Migration 006 + 007 für den Supabase SQL-Editor
-- (idempotent: kann gefahrlos mehrfach ausgeführt werden)
-- Projekt: Supabase Dashboard -> SQL Editor -> einfügen -> Run

-- Migration: Anomalie- und Kontext-Tabellen (2. Design-Zyklus)
-- Description: Erweitert das Schema um die Komponenten Anomalieerkennung,
--   Kontextsammlung (externe Quellen) und Erklärungsgenerierung:
--   - companies erhält ticker/isin zur Verknüpfung mit Finanzmarktdaten
--   - anomalies: erkannte extreme Veränderungen je Bewertungszeitreihe
--   - context_items: externe Ereignisse (News, Ad-hoc, Kursbewegungen)
--   - stock_prices: Aktienkursverlauf je Unternehmen
--   - financial_kpis: zentrale Unternehmenskennzahlen
--   - explanations: Erklärungsansätze je Anomalie mit Quellenbeleg

-- ── companies: Ticker-Zuordnung ──────────────────────────────────────────────
ALTER TABLE companies ADD COLUMN IF NOT EXISTS ticker TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS isin TEXT;

-- ── anomalies ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    source TEXT NOT NULL DEFAULT 'employee',        -- 'employee' | 'candidates'
    dimension TEXT NOT NULL,                        -- 'durchschnittsbewertung' | Dimensionsschluessel
    period TEXT NOT NULL,                           -- Anomalie-Monat 'YYYY-MM'
    window_start DATE NOT NULL,                     -- Ereignisfenster fuer Kontextsammlung
    window_end DATE NOT NULL,
    direction TEXT NOT NULL,                        -- 'rise' | 'fall'
    magnitude NUMERIC(4,2),                         -- Delta in Bewertungspunkten
    score NUMERIC(8,3),                             -- methodenspezifisch (|z| bzw. Mean-Shift)
    method TEXT NOT NULL,                           -- 'pelt' | 'zscore'
    params JSONB NOT NULL DEFAULT '{}'::jsonb,      -- verwendete Parameter (Reproduzierbarkeit)
    detected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, source, dimension, period, method)
);

CREATE INDEX IF NOT EXISTS idx_anomalies_company ON anomalies(company_id);

-- ── context_items ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS context_items (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,                      -- 'news' | 'adhoc' | 'stock_move'
    provider TEXT NOT NULL,                         -- 'yfinance' | 'eqs_rss' | 'manual'
    titel TEXT NOT NULL,
    zusammenfassung TEXT,
    url TEXT,
    published_at TIMESTAMPTZ,
    raw JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_context_items_url
    ON context_items(company_id, url) WHERE url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_context_items_company_date
    ON context_items(company_id, published_at);

-- ── stock_prices ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    close NUMERIC(14,4),
    volume BIGINT,
    currency TEXT,
    UNIQUE (company_id, date)
);

CREATE INDEX IF NOT EXISTS idx_stock_prices_company_date ON stock_prices(company_id, date);

-- ── financial_kpis ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS financial_kpis (
    id SERIAL PRIMARY KEY,
    company_id INTEGER UNIQUE REFERENCES companies(id) ON DELETE CASCADE,
    ticker TEXT,
    market_cap NUMERIC,
    trailing_pe NUMERIC,
    revenue NUMERIC,
    employees INTEGER,
    dividend_yield NUMERIC,
    profit_margin NUMERIC,
    currency TEXT,
    raw JSONB,
    fetched_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ── explanations ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS explanations (
    id SERIAL PRIMARY KEY,
    anomaly_id INTEGER REFERENCES anomalies(id) ON DELETE CASCADE,
    context_item_id INTEGER REFERENCES context_items(id) ON DELETE SET NULL,
    rank INTEGER,
    correspondence_score NUMERIC(5,3),
    matched_topics JSONB,                           -- ["Kommunikation", ...]
    direction_consistent BOOLEAN,
    review_evidence JSONB,                          -- Topic-/Sentiment-Statistik im Fenster
    erklaerungstext TEXT,                           -- generierter Erklaerungssatz
    quelle JSONB,                                   -- Quellenbeleg {source_type, provider, titel, url, published_at}
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_explanations_anomaly ON explanations(anomaly_id);

-- ── Row-Level Security (Stil wie 005_enable_rls.sql) ─────────────────────────
ALTER TABLE anomalies ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "public_read_anomalies" ON anomalies;
CREATE POLICY "public_read_anomalies"
    ON anomalies FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "service_role_all_anomalies" ON anomalies;
CREATE POLICY "service_role_all_anomalies"
    ON anomalies FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

ALTER TABLE context_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "public_read_context_items" ON context_items;
CREATE POLICY "public_read_context_items"
    ON context_items FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "service_role_all_context_items" ON context_items;
CREATE POLICY "service_role_all_context_items"
    ON context_items FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

ALTER TABLE stock_prices ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "public_read_stock_prices" ON stock_prices;
CREATE POLICY "public_read_stock_prices"
    ON stock_prices FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "service_role_all_stock_prices" ON stock_prices;
CREATE POLICY "service_role_all_stock_prices"
    ON stock_prices FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

ALTER TABLE financial_kpis ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "public_read_financial_kpis" ON financial_kpis;
CREATE POLICY "public_read_financial_kpis"
    ON financial_kpis FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "service_role_all_financial_kpis" ON financial_kpis;
CREATE POLICY "service_role_all_financial_kpis"
    ON financial_kpis FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

ALTER TABLE explanations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "public_read_explanations" ON explanations;
CREATE POLICY "public_read_explanations"
    ON explanations FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "service_role_all_explanations" ON explanations;
CREATE POLICY "service_role_all_explanations"
    ON explanations FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


-- Migration: Analystenempfehlungen (Yahoo Finance)
-- Description: Monatliche Verteilung der Analystenempfehlungen
--   (Strong Buy / Buy / Hold / Sell / Strong Sell) je Unternehmen.
--   yfinance liefert relative Perioden (0m..-3m); beim Abruf werden sie in
--   Kalendermonate aufgeloest, wodurch ueber die Zeit Historie entsteht.

CREATE TABLE IF NOT EXISTS analyst_recommendations (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    month TEXT NOT NULL,                            -- 'YYYY-MM'
    strong_buy INTEGER DEFAULT 0,
    buy INTEGER DEFAULT 0,
    hold INTEGER DEFAULT 0,
    sell INTEGER DEFAULT 0,
    strong_sell INTEGER DEFAULT 0,
    fetched_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, month)
);

CREATE INDEX IF NOT EXISTS idx_analyst_recommendations_company
    ON analyst_recommendations(company_id, month);

-- ── Row-Level Security (Stil wie 005/006) ────────────────────────────────────
ALTER TABLE analyst_recommendations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "public_read_analyst_recommendations" ON analyst_recommendations;
CREATE POLICY "public_read_analyst_recommendations"
    ON analyst_recommendations FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "service_role_all_analyst_recommendations" ON analyst_recommendations;
CREATE POLICY "service_role_all_analyst_recommendations"
    ON analyst_recommendations FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
