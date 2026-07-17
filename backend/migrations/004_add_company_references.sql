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

