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

