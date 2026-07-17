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

CREATE POLICY "public_read_analyst_recommendations"
    ON analyst_recommendations FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "service_role_all_analyst_recommendations"
    ON analyst_recommendations FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
