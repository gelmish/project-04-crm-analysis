-- ================================================================
-- PipelineIQ — Stored Procedures
-- Project 4: CRM System Analysis
-- Gelmish Technology Ltd
-- ================================================================
-- All functions use LANGUAGE plpgsql
-- Safe to re-run — all use CREATE OR REPLACE
-- Run AFTER schema.sql and seed.sql
-- ================================================================


-- ── Function 1: Pipeline Health Check ────────────────────────────
-- Returns a key-value summary of all top-level pipeline metrics.
-- Use this as the first query in any executive briefing.
--
-- Usage: SELECT * FROM fn_pipeline_health();
-- ─────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION fn_pipeline_health()
RETURNS TABLE (
    metric TEXT,
    value  TEXT
) LANGUAGE plpgsql AS $$
DECLARE
    v_total_deals    INT;
    v_won_deals      INT;
    v_lost_deals     INT;
    v_open_deals     INT;
    v_win_rate       NUMERIC;
    v_total_revenue  NUMERIC;
    v_pipeline_value NUMERIC;
    v_avg_velocity   NUMERIC;
    v_avg_deal_size  NUMERIC;
BEGIN
    SELECT
        COUNT(*),
        SUM(is_won::INT),
        SUM(is_lost::INT),
        SUM(is_open::INT),
        SUM(CASE WHEN is_won  THEN deal_value    ELSE 0 END),
        SUM(CASE WHEN is_open THEN weighted_value ELSE 0 END),
        AVG(CASE WHEN deal_velocity_days > 0
                 THEN deal_velocity_days END),
        AVG(deal_value)
    INTO
        v_total_deals, v_won_deals, v_lost_deals,
        v_open_deals,  v_total_revenue, v_pipeline_value,
        v_avg_velocity, v_avg_deal_size
    FROM deals;

    v_win_rate := ROUND(
        v_won_deals * 100.0 /
        NULLIF(v_won_deals + v_lost_deals, 0), 1);

    RETURN QUERY VALUES
        ('Total Deals',
            v_total_deals::TEXT),
        ('Closed Won',
            v_won_deals::TEXT),
        ('Closed Lost',
            v_lost_deals::TEXT),
        ('Open Deals',
            v_open_deals::TEXT),
        ('Win Rate (%)',
            v_win_rate::TEXT),
        ('Total Revenue Won',
            TO_CHAR(v_total_revenue,  'FM$999,999,999.00')),
        ('Weighted Open Pipeline',
            TO_CHAR(v_pipeline_value, 'FM$999,999,999.00')),
        ('Avg Deal Size',
            TO_CHAR(v_avg_deal_size,  'FM$999,999,999.00')),
        ('Avg Deal Velocity (days)',
            ROUND(v_avg_velocity, 1)::TEXT);
END;
$$;


-- ── Function 2: Rep Performance by Quarter ────────────────────────
-- Returns a ranked rep leaderboard for any given quarter.
-- Includes revenue, quota attainment, win rate and velocity.
--
-- Usage: SELECT * FROM fn_rep_performance_by_quarter(2024, 1);
--        SELECT * FROM fn_rep_performance_by_quarter(2023, 4);
-- ─────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION fn_rep_performance_by_quarter(
    p_year    INT,
    p_quarter INT
)
RETURNS TABLE (
    rep_name            TEXT,
    region_name         TEXT,
    title               TEXT,
    deals_won           BIGINT,
    revenue_won         NUMERIC,
    annual_quota        NUMERIC,
    quota_attainment_pct NUMERIC,
    avg_deal_size       NUMERIC,
    avg_velocity_days   NUMERIC,
    win_rate_pct        NUMERIC
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.rep_name::TEXT,
        rg.region_name::TEXT,
        r.title::TEXT,
        SUM(d.is_won::INT),
        ROUND(SUM(
            CASE WHEN d.is_won THEN d.deal_value ELSE 0 END), 2),
        r.annual_quota,
        ROUND(SUM(
            CASE WHEN d.is_won THEN d.deal_value ELSE 0 END)
            * 100.0 / NULLIF(r.annual_quota, 0), 1),
        ROUND(AVG(d.deal_value), 2),
        ROUND(AVG(d.deal_velocity_days), 1),
        ROUND(SUM(d.is_won::INT) * 100.0 /
            NULLIF(COUNT(d.deal_id), 0), 1)
    FROM sales_reps r
    JOIN regions rg ON r.region_id = rg.region_id
    JOIN deals   d  ON r.rep_id    = d.rep_id
    WHERE EXTRACT(YEAR    FROM d.close_date) = p_year
      AND EXTRACT(QUARTER FROM d.close_date) = p_quarter
    GROUP BY
        r.rep_name, rg.region_name,
        r.title, r.annual_quota
    ORDER BY revenue_won DESC;
END;
$$;


-- ── Function 3: Churn Risk Alert ──────────────────────────────────
-- Returns all active accounts above a given churn score threshold.
-- Default threshold is 0.6 (High risk and above).
-- Designed to feed a daily CSM alert or email workflow.
--
-- Usage: SELECT * FROM fn_churn_risk_alert();
--        SELECT * FROM fn_churn_risk_alert(0.8);
-- ─────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION fn_churn_risk_alert(
    p_threshold NUMERIC DEFAULT 0.6
)
RETURNS TABLE (
    company_name         TEXT,
    industry_name        TEXT,
    region_name          TEXT,
    churn_score          NUMERIC,
    churn_risk_band      TEXT,
    customer_ltv         NUMERIC,
    ltv_band             TEXT,
    revenue_won          NUMERIC,
    intervention_urgency TEXT
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.company_name::TEXT,
        i.industry_name::TEXT,
        rg.region_name::TEXT,
        c.churn_score,
        c.churn_risk_band::TEXT,
        c.customer_ltv,
        c.ltv_band::TEXT,
        COALESCE(ROUND(SUM(
            CASE WHEN d.is_won
                 THEN d.deal_value END), 2), 0),
        CASE
            WHEN c.churn_score >= 0.8 THEN 'IMMEDIATE'
            WHEN c.churn_score >= 0.6 THEN 'THIS WEEK'
            ELSE 'THIS MONTH'
        END::TEXT
    FROM companies c
    JOIN industries i  ON c.industry_id = i.industry_id
    JOIN regions    rg ON c.region_id   = rg.region_id
    LEFT JOIN deals d  ON c.company_id  = d.company_id
    WHERE c.churn_score  >= p_threshold
      AND c.is_active     = TRUE
    GROUP BY
        c.company_name, i.industry_name, rg.region_name,
        c.churn_score, c.churn_risk_band,
        c.customer_ltv, c.ltv_band
    ORDER BY c.churn_score DESC;
END;
$$;


-- ── Function 4: Deal Velocity Analysis ───────────────────────────
-- Returns velocity statistics broken down by product and stage.
-- Identifies where deals are stalling in the pipeline.
--
-- Usage: SELECT * FROM fn_deal_velocity_analysis();
-- ─────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION fn_deal_velocity_analysis()
RETURNS TABLE (
    product_name     TEXT,
    stage_name       TEXT,
    deal_count       BIGINT,
    avg_velocity     NUMERIC,
    median_velocity  NUMERIC,
    min_velocity     INT,
    max_velocity     INT,
    stall_risk       TEXT
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.product_name::TEXT,
        ds.stage_name::TEXT,
        COUNT(d.deal_id),
        ROUND(AVG(d.deal_velocity_days), 1),
        ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY d.deal_velocity_days)::NUMERIC, 1),
        MIN(d.deal_velocity_days),
        MAX(d.deal_velocity_days),
        CASE
            WHEN AVG(d.deal_velocity_days) > 90
                THEN 'HIGH STALL RISK'
            WHEN AVG(d.deal_velocity_days) > 60
                THEN 'MODERATE'
            ELSE 'HEALTHY'
        END::TEXT
    FROM deals d
    JOIN products    p  ON d.product_id = p.product_id
    JOIN deal_stages ds ON d.stage_id   = ds.stage_id
    WHERE d.deal_velocity_days IS NOT NULL
    GROUP BY p.product_name, ds.stage_name
    ORDER BY p.product_name, AVG(d.deal_velocity_days) DESC;
END;
$$;


-- ── Function 5: Revenue Forecast ─────────────────────────────────
-- Projects next quarter revenue based on weighted open pipeline
-- and the historical win rate for each rep.
--
-- Usage: SELECT * FROM fn_revenue_forecast();
-- ─────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION fn_revenue_forecast()
RETURNS TABLE (
    rep_name              TEXT,
    region_name           TEXT,
    open_deals            BIGINT,
    weighted_pipeline     NUMERIC,
    historical_win_rate   NUMERIC,
    forecast_revenue      NUMERIC,
    annual_quota          NUMERIC,
    quota_gap             NUMERIC
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH win_rates AS (
        SELECT
            rep_id,
            ROUND(SUM(is_won::INT) * 100.0 /
                NULLIF(SUM(is_won::INT) +
                       SUM(is_lost::INT), 0), 1) AS win_rate
        FROM deals
        GROUP BY rep_id
    ),
    open_pipe AS (
        SELECT
            rep_id,
            COUNT(*)         AS open_deals,
            SUM(weighted_value) AS weighted_pipeline
        FROM deals
        WHERE is_open = TRUE
        GROUP BY rep_id
    ),
    won_revenue AS (
        SELECT
            rep_id,
            SUM(deal_value) AS revenue_won
        FROM deals
        WHERE is_won = TRUE
        GROUP BY rep_id
    )
    SELECT
        r.rep_name::TEXT,
        rg.region_name::TEXT,
        COALESCE(op.open_deals, 0),
        ROUND(COALESCE(op.weighted_pipeline, 0), 2),
        COALESCE(wr.win_rate, 0),
        ROUND(COALESCE(op.weighted_pipeline, 0) *
              COALESCE(wr.win_rate, 0) / 100.0, 2),
        r.annual_quota,
        ROUND(r.annual_quota -
              COALESCE(wrev.revenue_won, 0), 2)
    FROM sales_reps r
    JOIN regions    rg   ON r.region_id = rg.region_id
    LEFT JOIN win_rates  wr   ON r.rep_id = wr.rep_id
    LEFT JOIN open_pipe  op   ON r.rep_id = op.rep_id
    LEFT JOIN won_revenue wrev ON r.rep_id = wrev.rep_id
    ORDER BY forecast_revenue DESC;
END;
$$;


-- ================================================================
-- USAGE REFERENCE
-- ================================================================

-- Pipeline health (executive summary):
-- SELECT * FROM fn_pipeline_health();

-- Q1 2024 rep leaderboard:
-- SELECT * FROM fn_rep_performance_by_quarter(2024, 1);

-- All accounts with churn score >= 0.8 (immediate action):
-- SELECT * FROM fn_churn_risk_alert(0.8);

-- Velocity analysis — find stalling stages:
-- SELECT * FROM fn_deal_velocity_analysis()
-- WHERE stall_risk = 'HIGH STALL RISK';

-- Revenue forecast vs quota gap:
-- SELECT rep_name, forecast_revenue,
--        annual_quota, quota_gap
-- FROM   fn_revenue_forecast()
-- ORDER  BY quota_gap DESC;