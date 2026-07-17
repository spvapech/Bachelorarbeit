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

