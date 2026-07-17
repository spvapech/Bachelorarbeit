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

