-- ================================================================
-- PipelineIQ — Analytical Views
-- Project 4: CRM System Analysis
-- Gelmish Technology Ltd
-- ================================================================
-- These views sit on top of the normalised schema and serve
-- as the analytical layer between raw tables and BI reporting.
-- All views are safe to re-run (CREATE OR REPLACE).
-- ================================================================


-- ── View 1: Full Deal Detail ──────────────────────────────────────
-- Denormalised deal view joining all lookup tables.
-- Primary source for ad-hoc deal queries and exports.
CREATE OR REPLACE VIEW vw_deal_detail AS
SELECT
    d.deal_id,
    d.deal_name,
    c.company_name,
    i.industry_name,
    rg.region_name,
    c.company_size,
    r.rep_name,
    r.title                          AS rep_title,
    p.product_name,
    p.tier                           AS product_tier,
    ds.stage_name,
    ds.display_order                 AS stage_order,
    lr.reason_text                   AS loss_reason,
    d.deal_value,
    d.weighted_value,
    d.probability,
    d.deal_size_band,
    d.created_date,
    d.close_date,
    d.expected_close_date,
    d.deal_velocity_days,
    d.is_won,
    d.is_lost,
    d.is_open,
    d.year_month,
    CASE
        WHEN d.is_won  THEN 'Won'
        WHEN d.is_lost THEN 'Lost'
        ELSE 'Open'
    END                              AS deal_status
FROM deals d
JOIN companies   c  ON d.company_id      = c.company_id
JOIN industries  i  ON c.industry_id     = i.industry_id
JOIN regions     rg ON c.region_id       = rg.region_id
JOIN sales_reps  r  ON d.rep_id          = r.rep_id
JOIN products    p  ON d.product_id      = p.product_id
JOIN deal_stages ds ON d.stage_id        = ds.stage_id
LEFT JOIN loss_reasons lr ON d.loss_reason_id = lr.loss_reason_id;


-- ── View 2: Executive KPI Summary ────────────────────────────────
-- Single-row summary of all top-level business KPIs.
-- Refreshes on every query — always current.
CREATE OR REPLACE VIEW vw_executive_kpis AS
SELECT
    COUNT(*)                                      AS total_deals,
    SUM(is_won::INT)                              AS deals_won,
    SUM(is_lost::INT)                             AS deals_lost,
    SUM(is_open::INT)                             AS deals_open,

    ROUND(SUM(is_won::INT) * 100.0 /
        NULLIF(SUM(is_won::INT) +
               SUM(is_lost::INT), 0), 1)          AS win_rate_pct,

    ROUND(SUM(CASE WHEN is_won
              THEN deal_value ELSE 0 END), 2)     AS total_revenue_won,

    ROUND(SUM(CASE WHEN is_open
              THEN weighted_value ELSE 0 END), 2) AS weighted_pipeline,

    ROUND(AVG(deal_value), 2)                     AS avg_deal_size,

    ROUND(AVG(CASE WHEN deal_velocity_days > 0
              THEN deal_velocity_days END), 1)    AS avg_velocity_days,

    ROUND(SUM(CASE WHEN is_won
              THEN deal_value ELSE 0 END) /
        NULLIF(SUM(is_won::INT), 0), 2)           AS avg_won_deal_size,

    NOW()                                         AS calculated_at
FROM deals;


-- ── View 3: Quarterly Revenue Summary ────────────────────────────
-- Revenue performance by quarter for board reporting.
CREATE OR REPLACE VIEW vw_quarterly_revenue AS
SELECT
    EXTRACT(YEAR    FROM close_date)::INT         AS year,
    EXTRACT(QUARTER FROM close_date)::INT         AS quarter,
    CONCAT(EXTRACT(YEAR FROM close_date)::INT,
           '-Q',
           EXTRACT(QUARTER FROM close_date)::INT) AS year_quarter,
    COUNT(*)                                      AS deals_won,
    ROUND(SUM(deal_value), 2)                     AS revenue,
    ROUND(AVG(deal_value), 2)                     AS avg_deal_size,
    ROUND(AVG(deal_velocity_days), 1)             AS avg_velocity,
    SUM(SUM(deal_value)) OVER (
        ORDER BY
            EXTRACT(YEAR FROM close_date),
            EXTRACT(QUARTER FROM close_date)
    )                                             AS cumulative_revenue
FROM deals
WHERE is_won = TRUE
  AND close_date IS NOT NULL
GROUP BY
    EXTRACT(YEAR FROM close_date),
    EXTRACT(QUARTER FROM close_date)
ORDER BY year, quarter;


-- ── View 4: Industry Performance ─────────────────────────────────
-- Deal performance broken down by industry vertical.
CREATE OR REPLACE VIEW vw_industry_performance AS
SELECT
    i.industry_name,
    COUNT(d.deal_id)                              AS total_deals,
    SUM(d.is_won::INT)                            AS won_deals,
    SUM(d.is_lost::INT)                           AS lost_deals,
    ROUND(SUM(d.is_won::INT) * 100.0 /
        NULLIF(COUNT(d.deal_id), 0), 1)           AS win_rate_pct,
    ROUND(SUM(CASE WHEN d.is_won
              THEN d.deal_value ELSE 0 END), 2)   AS revenue_won,
    ROUND(AVG(d.deal_value), 2)                   AS avg_deal_size,
    ROUND(AVG(d.deal_velocity_days), 1)           AS avg_velocity_days,
    COUNT(DISTINCT d.company_id)                  AS unique_accounts
FROM deals d
JOIN companies  c ON d.company_id  = c.company_id
JOIN industries i ON c.industry_id = i.industry_id
GROUP BY i.industry_name
ORDER BY revenue_won DESC;


-- ── View 5: Rep Activity Summary ─────────────────────────────────
-- Links rep activity volume to deal outcomes.
-- Used to assess activity quality vs quantity.
CREATE OR REPLACE VIEW vw_rep_activity_summary AS
SELECT
    r.rep_id,
    r.rep_name,
    rg.region_name,
    COUNT(DISTINCT a.activity_id)                 AS total_activities,
    COUNT(DISTINCT a.deal_id)                     AS deals_touched,
    ROUND(AVG(a.duration_mins), 1)                AS avg_duration_mins,
    SUM(a.is_positive::INT)                       AS positive_outcomes,
    ROUND(SUM(a.is_positive::INT) * 100.0 /
        NULLIF(COUNT(a.activity_id), 0), 1)       AS positive_rate_pct,
    COUNT(DISTINCT CASE WHEN d.is_won
          THEN d.deal_id END)                     AS won_deals_touched,
    ROUND(COUNT(DISTINCT CASE WHEN d.is_won
          THEN d.deal_id END) * 100.0 /
        NULLIF(COUNT(DISTINCT a.deal_id), 0), 1) AS activity_win_rate
FROM sales_reps  r
JOIN regions     rg ON r.region_id  = rg.region_id
LEFT JOIN activities a ON r.rep_id  = a.rep_id
LEFT JOIN deals      d ON a.deal_id = d.deal_id
GROUP BY r.rep_id, r.rep_name, rg.region_name
ORDER BY total_activities DESC;


-- ── View 6: At-Risk Account Monitor ──────────────────────────────
-- Live list of high and critical churn risk active accounts.
-- Designed to feed a daily CSM alert workflow.
CREATE OR REPLACE VIEW vw_at_risk_accounts AS
SELECT
    c.company_id,
    c.company_name,
    i.industry_name,
    rg.region_name,
    c.churn_score,
    c.churn_risk_band,
    c.customer_ltv,
    c.ltv_band,
    COALESCE(
        SUM(CASE WHEN d.is_won
            THEN d.deal_value END), 0)            AS total_revenue_won,
    COUNT(DISTINCT d.deal_id)                     AS total_deals,
    MAX(d.close_date)                             AS last_close_date,
    CURRENT_DATE - MAX(d.close_date)              AS days_since_last_deal,
    CASE
        WHEN c.churn_score >= 0.8 THEN 'IMMEDIATE'
        WHEN c.churn_score >= 0.6 THEN 'THIS WEEK'
        ELSE 'THIS MONTH'
    END                                           AS intervention_urgency
FROM companies c
JOIN industries i  ON c.industry_id = i.industry_id
JOIN regions    rg ON c.region_id   = rg.region_id
LEFT JOIN deals d  ON c.company_id  = d.company_id
WHERE c.churn_risk_band IN ('High', 'Critical')
  AND c.is_active = TRUE
GROUP BY
    c.company_id, c.company_name, i.industry_name,
    rg.region_name, c.churn_score, c.churn_risk_band,
    c.customer_ltv, c.ltv_band
ORDER BY c.churn_score DESC;


-- ================================================================
-- USAGE EXAMPLES
-- ================================================================

-- Top 10 at-risk accounts by LTV:
-- SELECT company_name, churn_score, customer_ltv,
--        intervention_urgency
-- FROM   vw_at_risk_accounts
-- ORDER  BY customer_ltv DESC
-- LIMIT  10;

-- Quarterly revenue trend:
-- SELECT year_quarter, revenue, cumulative_revenue
-- FROM   vw_quarterly_revenue;

-- Rep performance with activity data:
-- SELECT r.rep_name, r.win_rate_pct,
--        a.total_activities, a.positive_rate_pct
-- FROM   vw_rep_performance  r
-- JOIN   vw_rep_activity_summary a
--        ON r.rep_id = a.rep_id
-- ORDER  BY r.revenue_won DESC;

-- Call churn alert stored procedure:
-- SELECT * FROM fn_churn_risk_alert(0.6);

-- Pipeline health check:
-- SELECT * FROM fn_pipeline_health();