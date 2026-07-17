-- Migration: Create Candidates Table
-- Description: Creates the candidates table with all required columns for candidate feedback and ratings

CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    
    -- Basic Information
    titel TEXT,
    status TEXT,
    datum TIMESTAMPTZ,
    update_datum TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Ratings
    durchschnittsbewertung NUMERIC(3, 2),
    gerundete_durchschnittsbewertung NUMERIC(3, 2),
    
    -- Descriptions
    stellenbeschreibung TEXT,
    verbesserungsvorschlaege TEXT,
    
    -- Star Ratings (Sternebewertung columns)
    sternebewertung_erklaerung_der_weiteren_schritte NUMERIC(3, 2),
    sternebewertung_zufriedenstellende_reaktion NUMERIC(3, 2),
    sternebewertung_vollstaendigkeit_der_infos NUMERIC(3, 2),
    sternebewertung_zufriedenstellende_antworten NUMERIC(3, 2),
    sternebewertung_angenehme_atmosphaere NUMERIC(3, 2),
    sternebewertung_professionalitaet_des_gespraechs NUMERIC(3, 2),
    sternebewertung_wertschaetzende_behandlung NUMERIC(3, 2),
    sternebewertung_erwartbarkeit_des_prozesses NUMERIC(3, 2),
    sternebewertung_zeitgerechte_zu_oder_absage NUMERIC(3, 2),
    sternebewertung_schnelle_antwort NUMERIC(3, 2),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create index on status for faster queries
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);

-- Create index on datum for date-based queries
CREATE INDEX IF NOT EXISTS idx_candidates_datum ON candidates(datum);

-- Add comment to table
COMMENT ON TABLE candidates IS 'Stores candidate feedback and ratings from interviews';

-- Migration: Create Employee Table
-- Description: Creates the employee table with all required columns for employee feedback and ratings

CREATE TABLE IF NOT EXISTS employee (
    id SERIAL PRIMARY KEY,
    
    -- Basic Information
    titel TEXT,
    status TEXT,
    datum TIMESTAMPTZ,
    update_datum TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Ratings
    durchschnittsbewertung NUMERIC(3, 2),
    gerundete_durchschnittsbewertung NUMERIC(3, 2),
    
    -- Descriptions
    jobbeschreibung TEXT,
    gut_am_arbeitgeber_finde_ich TEXT,
    schlecht_am_arbeitgeber_finde_ich TEXT,
    verbesserungsvorschlaege TEXT,
    
    -- Star Ratings (Sternebewertung columns)
    sternebewertung_arbeitsatmosphaere NUMERIC(3, 2),
    sternebewertung_image NUMERIC(3, 2),
    sternebewertung_work_life_balance NUMERIC(3, 2),
    sternebewertung_karriere_weiterbildung NUMERIC(3, 2),
    sternebewertung_gehalt_sozialleistungen NUMERIC(3, 2),
    sternebewertung_kollegenzusammenhalt NUMERIC(3, 2),
    sternebewertung_umwelt_sozialbewusstsein NUMERIC(3, 2),
    sternebewertung_vorgesetztenverhalten NUMERIC(3, 2),
    sternebewertung_kommunikation NUMERIC(3, 2),
    sternebewertung_interessante_aufgaben NUMERIC(3, 2),
    sternebewertung_umgang_mit_aelteren_kollegen NUMERIC(3, 2),
    sternebewertung_arbeitsbedingungen NUMERIC(3, 2),
    sternebewertung_gleichberechtigung NUMERIC(3, 2),
    
    -- Topic Text Columns (comments per topic)
    arbeitsatmosphaere TEXT,
    image TEXT,
    work_life_balance TEXT,
    karriere_weiterbildung TEXT,
    gehalt_sozialleistungen TEXT,
    kollegenzusammenhalt TEXT,
    umwelt_sozialbewusstsein TEXT,
    vorgesetztenverhalten TEXT,
    kommunikation TEXT,
    interessante_aufgaben TEXT,
    umgang_mit_aelteren_kollegen TEXT,
    arbeitsbedingungen TEXT,
    gleichberechtigung TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create index on status for faster queries
CREATE INDEX IF NOT EXISTS idx_employee_status ON employee(status);

-- Create index on datum for date-based queries
CREATE INDEX IF NOT EXISTS idx_employee_datum ON employee(datum);

-- Add comment to table
COMMENT ON TABLE employee IS 'Stores employee feedback and ratings about their workplace experience';

-- Migration: Create Companies Table
-- Description: Creates the companies table to store company information

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create index on name for faster lookups
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);

-- Add comment to table
COMMENT ON TABLE companies IS 'Stores company information that candidates and employees belong to';

-- Migration: Add Company References
-- Description: Adds company_id foreign key columns to candidates and employee tables

-- Add company_id column to candidates table
ALTER TABLE candidates
ADD COLUMN IF NOT EXISTS company_id INTEGER;

-- Add foreign key constraint to candidates table
ALTER TABLE candidates
ADD CONSTRAINT fk_candidates_company
FOREIGN KEY (company_id) REFERENCES companies(id)
ON DELETE SET NULL;

-- Create index on company_id for faster queries
CREATE INDEX IF NOT EXISTS idx_candidates_company_id ON candidates(company_id);

-- Add company_id column to employee table
ALTER TABLE employee
ADD COLUMN IF NOT EXISTS company_id INTEGER;

-- Add foreign key constraint to employee table
ALTER TABLE employee
ADD CONSTRAINT fk_employee_company
FOREIGN KEY (company_id) REFERENCES companies(id)
ON DELETE SET NULL;

-- Create index on company_id for faster queries
CREATE INDEX IF NOT EXISTS idx_employee_company_id ON employee(company_id);


-- Migration 006: Anomalie- und Kontext-Tabellen (2. Design-Zyklus)
-- Description: Ticker-Zuordnung, Anomalien, externe Kontextquellen,
--   Aktienkurse, Kennzahlen und Erklaerungen (RLS nur in Supabase-Migration 006)

ALTER TABLE companies ADD COLUMN IF NOT EXISTS ticker TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS isin TEXT;

CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    source TEXT NOT NULL DEFAULT 'employee',
    dimension TEXT NOT NULL,
    period TEXT NOT NULL,
    window_start DATE NOT NULL,
    window_end DATE NOT NULL,
    direction TEXT NOT NULL,
    magnitude NUMERIC(4,2),
    score NUMERIC(8,3),
    method TEXT NOT NULL,
    params JSONB NOT NULL DEFAULT '{}'::jsonb,
    detected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, source, dimension, period, method)
);

CREATE INDEX IF NOT EXISTS idx_anomalies_company ON anomalies(company_id);

CREATE TABLE IF NOT EXISTS context_items (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    provider TEXT NOT NULL,
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

CREATE TABLE IF NOT EXISTS explanations (
    id SERIAL PRIMARY KEY,
    anomaly_id INTEGER REFERENCES anomalies(id) ON DELETE CASCADE,
    context_item_id INTEGER REFERENCES context_items(id) ON DELETE SET NULL,
    rank INTEGER,
    correspondence_score NUMERIC(5,3),
    matched_topics JSONB,
    direction_consistent BOOLEAN,
    review_evidence JSONB,
    erklaerungstext TEXT,
    quelle JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_explanations_anomaly ON explanations(anomaly_id);

-- Migration 007: Analystenempfehlungen (Yahoo Finance)

CREATE TABLE IF NOT EXISTS analyst_recommendations (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    month TEXT NOT NULL,
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
