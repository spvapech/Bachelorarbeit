-- Function: get_employee_ratings_avg
-- Returns average of all sternebewertung_* columns for a given company.
CREATE OR REPLACE FUNCTION get_employee_ratings_avg(p_company_id INTEGER)
RETURNS TABLE (
    avg_arbeitsatmosphaere        NUMERIC,
    avg_image                     NUMERIC,
    avg_work_life_balance         NUMERIC,
    avg_karriere_weiterbildung    NUMERIC,
    avg_gehalt_sozialleistungen   NUMERIC,
    avg_kollegenzusammenhalt      NUMERIC,
    avg_umwelt_sozialbewusstsein  NUMERIC,
    avg_vorgesetztenverhalten     NUMERIC,
    avg_kommunikation             NUMERIC,
    avg_interessante_aufgaben     NUMERIC,
    avg_umgang_aelteren_kollegen  NUMERIC,
    avg_arbeitsbedingungen        NUMERIC,
    avg_gleichberechtigung        NUMERIC
)
LANGUAGE sql STABLE AS $$
    SELECT
        ROUND(AVG(sternebewertung_arbeitsatmosphaere),       4),
        ROUND(AVG(sternebewertung_image),                    4),
        ROUND(AVG(sternebewertung_work_life_balance),        4),
        ROUND(AVG(sternebewertung_karriere_weiterbildung),   4),
        ROUND(AVG(sternebewertung_gehalt_sozialleistungen),  4),
        ROUND(AVG(sternebewertung_kollegenzusammenhalt),     4),
        ROUND(AVG(sternebewertung_umwelt_sozialbewusstsein), 4),
        ROUND(AVG(sternebewertung_vorgesetztenverhalten),    4),
        ROUND(AVG(sternebewertung_kommunikation),            4),
        ROUND(AVG(sternebewertung_interessante_aufgaben),    4),
        ROUND(AVG(sternebewertung_umgang_mit_aelteren_kollegen), 4),
        ROUND(AVG(sternebewertung_arbeitsbedingungen),       4),
        ROUND(AVG(sternebewertung_gleichberechtigung),       4)
    FROM employee
    WHERE company_id = p_company_id;
$$;

-- Function: get_employee_ratings_avg_range
-- Returns average of all sternebewertung_* columns for a company within a date range.
CREATE OR REPLACE FUNCTION get_employee_ratings_avg_range(
    p_company_id INTEGER,
    p_from       TIMESTAMPTZ,
    p_to         TIMESTAMPTZ
)
RETURNS TABLE (
    avg_arbeitsatmosphaere        NUMERIC,
    avg_image                     NUMERIC,
    avg_work_life_balance         NUMERIC,
    avg_karriere_weiterbildung    NUMERIC,
    avg_gehalt_sozialleistungen   NUMERIC,
    avg_kollegenzusammenhalt      NUMERIC,
    avg_umwelt_sozialbewusstsein  NUMERIC,
    avg_vorgesetztenverhalten     NUMERIC,
    avg_kommunikation             NUMERIC,
    avg_interessante_aufgaben     NUMERIC,
    avg_umgang_aelteren_kollegen  NUMERIC,
    avg_arbeitsbedingungen        NUMERIC,
    avg_gleichberechtigung        NUMERIC
)
LANGUAGE sql STABLE AS $$
    SELECT
        ROUND(AVG(sternebewertung_arbeitsatmosphaere),       4),
        ROUND(AVG(sternebewertung_image),                    4),
        ROUND(AVG(sternebewertung_work_life_balance),        4),
        ROUND(AVG(sternebewertung_karriere_weiterbildung),   4),
        ROUND(AVG(sternebewertung_gehalt_sozialleistungen),  4),
        ROUND(AVG(sternebewertung_kollegenzusammenhalt),     4),
        ROUND(AVG(sternebewertung_umwelt_sozialbewusstsein), 4),
        ROUND(AVG(sternebewertung_vorgesetztenverhalten),    4),
        ROUND(AVG(sternebewertung_kommunikation),            4),
        ROUND(AVG(sternebewertung_interessante_aufgaben),    4),
        ROUND(AVG(sternebewertung_umgang_mit_aelteren_kollegen), 4),
        ROUND(AVG(sternebewertung_arbeitsbedingungen),       4),
        ROUND(AVG(sternebewertung_gleichberechtigung),       4)
    FROM employee
    WHERE company_id = p_company_id
      AND datum >= p_from
      AND datum <  p_to;
$$;

GRANT EXECUTE ON FUNCTION get_employee_ratings_avg(INTEGER)                             TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_employee_ratings_avg_range(INTEGER, TIMESTAMPTZ, TIMESTAMPTZ) TO anon, authenticated, service_role;
