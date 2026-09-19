-- ================================================================
-- PipelineIQ — PostgreSQL Database Schema
-- Project 4: CRM System Analysis
-- Gelmish Technology Ltd
-- ================================================================
-- Fully normalised to 3NF
-- Enforced PK/FK relationships
-- Indexes on all FK and frequently queried columns
-- ================================================================

-- ── Drop existing tables (safe re-run) ───────────────────────────
DROP TABLE IF EXISTS activities        CASCADE;
DROP TABLE IF EXISTS deals             CASCADE;
DROP TABLE IF EXISTS contacts          CASCADE;
DROP TABLE IF EXISTS companies         CASCADE;
DROP TABLE IF EXISTS sales_reps        CASCADE;
DROP TABLE IF EXISTS deal_stages       CASCADE;
DROP TABLE IF EXISTS products          CASCADE;
DROP TABLE IF EXISTS regions           CASCADE;
DROP TABLE IF EXISTS industries        CASCADE;
DROP TABLE IF EXISTS loss_reasons      CASCADE;
DROP TABLE IF EXISTS activity_types    CASCADE;
DROP TABLE IF EXISTS activity_outcomes CASCADE;


-- ================================================================
-- LOOKUP TABLES (3NF normalisation)
-- ================================================================

CREATE TABLE regions (
    region_id   SERIAL       PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE industries (
    industry_id   SERIAL       PRIMARY KEY,
    industry_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE deal_stages (
    stage_id      SERIAL      PRIMARY KEY,
    stage_name    VARCHAR(50) NOT NULL UNIQUE,
    display_order INT         NOT NULL,
    probability   NUMERIC(5,2) NOT NULL
        CHECK (probability BETWEEN 0 AND 100)
);

CREATE TABLE products (
    product_id    SERIAL       PRIMARY KEY,
    product_name  VARCHAR(100) NOT NULL UNIQUE,
    tier          VARCHAR(50)  NOT NULL,
    min_price     NUMERIC(12,2) NOT NULL,
    max_price     NUMERIC(12,2) NOT NULL,
    CONSTRAINT chk_price_range CHECK (max_price >= min_price)
);

CREATE TABLE loss_reasons (
    loss_reason_id SERIAL       PRIMARY KEY,
    reason_text    VARCHAR(200) NOT NULL UNIQUE
);

CREATE TABLE activity_types (
    activity_type_id SERIAL      PRIMARY KEY,
    type_name        VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE activity_outcomes (
    outcome_id   SERIAL      PRIMARY KEY,
    outcome_name VARCHAR(50) NOT NULL UNIQUE
);


-- ================================================================
-- CORE TABLES
-- ================================================================

-- ── Sales Reps ───────────────────────────────────────────────────
CREATE TABLE sales_reps (
    rep_id           VARCHAR(10)  PRIMARY KEY,
    rep_name         VARCHAR(100) NOT NULL,
    title            VARCHAR(100) NOT NULL,
    region_id        INT          NOT NULL
        REFERENCES regions(region_id) ON DELETE RESTRICT,
    hire_date        DATE         NOT NULL,
    annual_quota     NUMERIC(12,2) NOT NULL
        CHECK (annual_quota > 0),
    active           BOOLEAN      NOT NULL DEFAULT TRUE,
    years_of_service NUMERIC(5,1),
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);


-- ── Companies ────────────────────────────────────────────────────
CREATE TABLE companies (
    company_id      VARCHAR(10)   PRIMARY KEY,
    company_name    VARCHAR(200)  NOT NULL UNIQUE,
    industry_id     INT           NOT NULL
        REFERENCES industries(industry_id) ON DELETE RESTRICT,
    company_size    VARCHAR(20)   NOT NULL
        CHECK (company_size IN (
            '1-10','11-50','51-200',
            '201-500','501-1000','1000+')),
    region_id       INT           NOT NULL
        REFERENCES regions(region_id) ON DELETE RESTRICT,
    annual_revenue  NUMERIC(15,2),
    churn_score     NUMERIC(5,3)
        CHECK (churn_score BETWEEN 0 AND 1),
    customer_ltv    NUMERIC(12,2)
        CHECK (customer_ltv >= 0),
    churn_risk_band VARCHAR(20)
        CHECK (churn_risk_band IN (
            'Low','Medium','High','Critical')),
    ltv_band        VARCHAR(20)
        CHECK (ltv_band IN (
            'Bronze','Silver','Gold','Platinum')),
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,
    created_date    DATE          NOT NULL,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);


-- ── Contacts ─────────────────────────────────────────────────────
CREATE TABLE contacts (
    contact_id   VARCHAR(10)  PRIMARY KEY,
    first_name   VARCHAR(100) NOT NULL,
    last_name    VARCHAR(100) NOT NULL,
    full_name    VARCHAR(200) GENERATED ALWAYS AS
                     (first_name || ' ' || last_name) STORED,
    email        VARCHAR(200) UNIQUE,
    job_title    VARCHAR(100),
    company_id   VARCHAR(10)  NOT NULL
        REFERENCES companies(company_id) ON DELETE CASCADE,
    region_id    INT          NOT NULL
        REFERENCES regions(region_id) ON DELETE RESTRICT,
    phone        VARCHAR(30),
    is_primary   BOOLEAN      NOT NULL DEFAULT FALSE,
    created_date DATE         NOT NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);


-- ── Deals ─────────────────────────────────────────────────────────
CREATE TABLE deals (
    deal_id              VARCHAR(10)   PRIMARY KEY,
    company_id           VARCHAR(10)   NOT NULL
        REFERENCES companies(company_id) ON DELETE RESTRICT,
    rep_id               VARCHAR(10)   NOT NULL
        REFERENCES sales_reps(rep_id) ON DELETE RESTRICT,
    product_id           INT           NOT NULL
        REFERENCES products(product_id) ON DELETE RESTRICT,
    stage_id             INT           NOT NULL
        REFERENCES deal_stages(stage_id) ON DELETE RESTRICT,
    loss_reason_id       INT
        REFERENCES loss_reasons(loss_reason_id) ON DELETE SET NULL,
    deal_name            VARCHAR(300)  NOT NULL,
    deal_value           NUMERIC(12,2) NOT NULL
        CHECK (deal_value > 0),
    weighted_value       NUMERIC(12,2) NOT NULL
        CHECK (weighted_value >= 0),
    probability          NUMERIC(5,2)  NOT NULL
        CHECK (probability BETWEEN 0 AND 100),
    deal_size_band       VARCHAR(20)
        CHECK (deal_size_band IN (
            'Small','Mid-Market','Enterprise','Strategic')),
    created_date         DATE          NOT NULL,
    close_date           DATE,
    expected_close_date  DATE,
    deal_velocity_days   INT
        CHECK (deal_velocity_days >= 0),
    is_won               BOOLEAN       NOT NULL DEFAULT FALSE,
    is_lost              BOOLEAN       NOT NULL DEFAULT FALSE,
    is_open              BOOLEAN       NOT NULL DEFAULT TRUE,
    year_month           VARCHAR(7),
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_stage_consistency CHECK (
        NOT (is_won AND is_lost)
    ),
    CONSTRAINT chk_close_date CHECK (
        close_date IS NULL OR close_date >= created_date
    )
);


-- ── Activities ───────────────────────────────────────────────────
CREATE TABLE activities (
    activity_id      VARCHAR(10)  PRIMARY KEY,
    deal_id          VARCHAR(10)  NOT NULL
        REFERENCES deals(deal_id) ON DELETE CASCADE,
    rep_id           VARCHAR(10)  NOT NULL
        REFERENCES sales_reps(rep_id) ON DELETE RESTRICT,
    activity_type_id INT          NOT NULL
        REFERENCES activity_types(activity_type_id) ON DELETE RESTRICT,
    outcome_id       INT          NOT NULL
        REFERENCES activity_outcomes(outcome_id) ON DELETE RESTRICT,
    activity_date    DATE         NOT NULL,
    duration_mins    INT
        CHECK (duration_mins > 0 AND duration_mins <= 480),
    activity_month   VARCHAR(7),
    is_positive      BOOLEAN      NOT NULL DEFAULT FALSE,
    notes            TEXT,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);


-- ================================================================
-- INDEXES
-- ================================================================

-- companies
CREATE INDEX idx_companies_industry
    ON companies(industry_id);
CREATE INDEX idx_companies_region
    ON companies(region_id);
CREATE INDEX idx_companies_churn_band
    ON companies(churn_risk_band);
CREATE INDEX idx_companies_active
    ON companies(is_active);

-- contacts
CREATE INDEX idx_contacts_company
    ON contacts(company_id);
CREATE INDEX idx_contacts_region
    ON contacts(region_id);

-- deals
CREATE INDEX idx_deals_company
    ON deals(company_id);
CREATE INDEX idx_deals_rep
    ON deals(rep_id);
CREATE INDEX idx_deals_product
    ON deals(product_id);
CREATE INDEX idx_deals_stage
    ON deals(stage_id);
CREATE INDEX idx_deals_created
    ON deals(created_date);
CREATE INDEX idx_deals_close
    ON deals(close_date);
CREATE INDEX idx_deals_is_won
    ON deals(is_won);
CREATE INDEX idx_deals_year_month
    ON deals(year_month);

-- activities
CREATE INDEX idx_activities_deal
    ON activities(deal_id);
CREATE INDEX idx_activities_rep
    ON activities(rep_id);
CREATE INDEX idx_activities_date
    ON activities(activity_date);
CREATE INDEX idx_activities_type
    ON activities(activity_type_id);


-- ================================================================
-- VIEWS
-- ================================================================

-- ── View 1: Pipeline Summary ──────────────────────────────────────
CREATE OR REPLACE VIEW vw_pipeline_summary AS
SELECT
    ds.stage_name,
    ds.display_order,
    COUNT(d.deal_id)          AS deal_count,
    SUM(d.deal_value)         AS total_value,
    AVG(d.deal_value)         AS avg_value,
    SUM(d.weighted_value)     AS weighted_pipeline,
    AVG(d.deal_velocity_days) AS avg_velocity_days,
    ROUND(COUNT(d.deal_id) * 100.0 /
        SUM(COUNT(d.deal_id)) OVER (), 1) AS pct_of_pipeline
FROM deals d
JOIN deal_stages ds ON d.stage_id = ds.stage_id
GROUP BY ds.stage_name, ds.display_order
ORDER BY ds.display_order;


-- ── View 2: Rep Performance ───────────────────────────────────────
CREATE OR REPLACE VIEW vw_rep_performance AS