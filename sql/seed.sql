-- ================================================================
-- PipelineIQ — Seed Data
-- Project 4: CRM System Analysis
-- Gelmish Technology Ltd
-- ================================================================
-- Populates all lookup tables with reference data
-- Run AFTER schema.sql
-- Run BEFORE loading CSV data
-- ================================================================


-- ── Regions ───────────────────────────────────────────────────────
INSERT INTO regions (region_name) VALUES
    ('North America'),
    ('Europe'),
    ('APAC'),
    ('Latin America'),
    ('Middle East & Africa')
ON CONFLICT (region_name) DO NOTHING;


-- ── Industries ────────────────────────────────────────────────────
INSERT INTO industries (industry_name) VALUES
    ('FinTech'),
    ('HealthTech'),
    ('EdTech'),
    ('RetailTech'),
    ('HRTech'),
    ('LegalTech'),
    ('PropTech'),
    ('CyberSecurity')
ON CONFLICT (industry_name) DO NOTHING;


-- ── Deal Stages ───────────────────────────────────────────────────
INSERT INTO deal_stages (stage_name, display_order, probability) VALUES
    ('Prospecting',   1, 10.00),
    ('Qualification', 2, 25.00),
    ('Proposal',      3, 50.00),
    ('Negotiation',   4, 75.00),
    ('Closed Won',    5, 100.00),
    ('Closed Lost',   6,   0.00)
ON CONFLICT (stage_name) DO NOTHING;


-- ── Products ──────────────────────────────────────────────────────
INSERT INTO products (product_name, tier, min_price, max_price) VALUES
    ('PipelineIQ Starter',    'Starter',    5000.00,  15000.00),
    ('PipelineIQ Pro',        'Pro',       15000.00,  50000.00),
    ('PipelineIQ Enterprise', 'Enterprise',50000.00, 250000.00)
ON CONFLICT (product_name) DO NOTHING;


-- ── Loss Reasons ─────────────────────────────────────────────────
INSERT INTO loss_reasons (reason_text) VALUES
    ('Price too high'),
    ('Chose competitor'),
    ('No budget'),
    ('Project cancelled'),
    ('Poor fit'),
    ('No decision made')
ON CONFLICT (reason_text) DO NOTHING;


-- ── Activity Types ────────────────────────────────────────────────
INSERT INTO activity_types (type_name) VALUES
    ('Email'),
    ('Call'),
    ('Demo'),
    ('Meeting'),
    ('Proposal Sent'),
    ('Follow-up')
ON CONFLICT (type_name) DO NOTHING;


-- ── Activity Outcomes ─────────────────────────────────────────────
INSERT INTO activity_outcomes (outcome_name) VALUES
    ('Positive'),
    ('Neutral'),
    ('Negative'),
    ('No Response')
ON CONFLICT (outcome_name) DO NOTHING;


-- ================================================================
-- VERIFICATION QUERIES
-- Run these after seeding to confirm all lookups loaded correctly
-- ================================================================

-- SELECT 'regions'        AS tbl, COUNT(*) FROM regions
-- UNION ALL
-- SELECT 'industries',           COUNT(*) FROM industries
-- UNION ALL
-- SELECT 'deal_stages',          COUNT(*) FROM deal_stages
-- UNION ALL
-- SELECT 'products',             COUNT(*) FROM products
-- UNION ALL
-- SELECT 'loss_reasons',         COUNT(*) FROM loss_reasons
-- UNION ALL
-- SELECT 'activity_types',       COUNT(*) FROM activity_types
-- UNION ALL
-- SELECT 'activity_outcomes',    COUNT(*) FROM activity_outcomes;

-- Expected output:
-- regions            5
-- industries         8
-- deal_stages        6
-- products           3
-- loss_reasons       6
-- activity_types     6
-- activity_outcomes  4