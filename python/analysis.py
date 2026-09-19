"""
PipelineIQ — Core Business Analysis
Project 4: CRM System Analysis
Gelmish Technology Ltd

Computes all KPIs and analytical outputs that feed
the dashboard and the Recommendations phase.

Outputs saved to data/processed/:
  - kpi_summary.csv
  - rep_performance.csv
  - pipeline_by_stage.csv
  - revenue_trend.csv
  - churn_risk_summary.csv
  - loss_analysis.csv
  - deal_velocity.csv
  - product_performance.csv
  - region_performance.csv
  - activity_effectiveness.csv
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

PROC_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')

def load():
    reps       = pd.read_csv(os.path.join(PROC_DIR, 'sales_reps_clean.csv'))
    companies  = pd.read_csv(os.path.join(PROC_DIR, 'companies_clean.csv'))
    contacts   = pd.read_csv(os.path.join(PROC_DIR, 'contacts_clean.csv'))
    deals      = pd.read_csv(os.path.join(PROC_DIR, 'deals_clean.csv'))
    activities = pd.read_csv(os.path.join(PROC_DIR, 'activities_clean.csv'))

    deals['created_date'] = pd.to_datetime(deals['created_date'])
    deals['close_date']   = pd.to_datetime(deals['close_date'],
                                           errors='coerce')
    activities['activity_date'] = pd.to_datetime(
        activities['activity_date'])

    deals['is_won']  = deals['stage'] == 'Closed Won'
    deals['is_lost'] = deals['stage'] == 'Closed Lost'
    deals['is_open'] = ~deals['stage'].isin(['Closed Won','Closed Lost'])

    return reps, companies, contacts, deals, activities


# ── 1. KPI Summary ────────────────────────────────────────────────
def calc_kpis(deals, companies, activities):
    won  = deals[deals['is_won']]
    lost = deals[deals['is_lost']]
    open_deals = deals[deals['is_open']]

    total_revenue      = won['deal_value'].sum()
    total_pipeline     = open_deals['weighted_value'].sum()
    win_rate           = len(won) / (len(won) + len(lost)) * 100 \
                         if (len(won) + len(lost)) > 0 else 0
    avg_deal_size      = won['deal_value'].mean()
    avg_velocity       = deals['deal_velocity_days'].dropna().mean()
    churn_high         = companies[
                             companies['churn_risk_band'].isin(
                                 ['High','Critical'])].shape[0]
    avg_ltv            = companies['customer_ltv'].mean()
    total_activities   = len(activities)
    positive_rate      = activities['is_positive'].mean() * 100 \
                         if 'is_positive' in activities.columns \
                         else (activities['outcome'] == 'Positive').mean() * 100

    kpis = {
        'total_revenue_won':        round(total_revenue, 2),
        'total_pipeline_weighted':  round(total_pipeline, 2),
        'total_deals':              len(deals),
        'deals_won':                len(won),
        'deals_lost':               len(lost),
        'deals_open':               len(open_deals),
        'win_rate_pct':             round(win_rate, 2),
        'avg_deal_size':            round(avg_deal_size, 2),
        'avg_deal_velocity_days':   round(avg_velocity, 1),
        'companies_high_churn':     churn_high,
        'avg_customer_ltv':         round(avg_ltv, 2),
        'total_activities':         total_activities,
        'activity_positive_rate':   round(positive_rate, 2),
    }

    df = pd.DataFrame([kpis])
    df.to_csv(os.path.join(PROC_DIR, 'kpi_summary.csv'), index=False)
    print("  kpi_summary.csv              ✓")

    for k, v in kpis.items():
        print(f"    {k:<35} : {v:>15,}" if isinstance(v, (int, float))
              else f"    {k:<35} : {v}")
    return kpis


# ── 2. Rep Performance ────────────────────────────────────────────
def calc_rep_performance(deals, reps):
    merged = deals.merge(
        reps[['rep_id','rep_name','annual_quota','title','region']],
        on='rep_id', how='left')

    won_rev = merged[merged['is_won']].groupby('rep_id')['deal_value'].sum()

    rep_perf = merged.groupby(
        ['rep_id','rep_name','annual_quota','title','region']
    ).agg(
        total_deals     = ('deal_id',             'count'),
        won_deals       = ('is_won',              'sum'),
        lost_deals      = ('is_lost',             'sum'),
        open_deals      = ('is_open',             'sum'),
        total_value     = ('deal_value',          'sum'),
        avg_deal_size   = ('deal_value',          'mean'),
        avg_velocity    = ('deal_velocity_days',  'mean'),
        weighted_pipe   = ('weighted_value',      'sum'),
    ).reset_index()

    rep_perf['revenue_won'] = rep_perf['rep_id'].map(won_rev).fillna(0)
    rep_perf['win_rate_pct'] = (
        rep_perf['won_deals'] /
        rep_perf['total_deals'] * 100
    ).round(1)
    rep_perf['quota_attainment_pct'] = (
        rep_perf['revenue_won'] /
        rep_perf['annual_quota'] * 100
    ).round(1)
    rep_perf['avg_deal_size']  = rep_perf['avg_deal_size'].round(2)
    rep_perf['avg_velocity']   = rep_perf['avg_velocity'].round(1)
    rep_perf['weighted_pipe']  = rep_perf['weighted_pipe'].round(2)

    rep_perf.to_csv(
        os.path.join(PROC_DIR, 'rep_performance.csv'), index=False)
    print("  rep_performance.csv          ✓")
    return rep_perf


# ── 3. Pipeline by Stage ──────────────────────────────────────────
def calc_pipeline_stages(deals):
    stage_order = ['Prospecting','Qualification','Proposal',
                   'Negotiation','Closed Won','Closed Lost']

    pipe = deals.groupby('stage').agg(
        deal_count      = ('deal_id',        'count'),
        total_value     = ('deal_value',     'sum'),
        avg_value       = ('deal_value',     'mean'),
        weighted_value  = ('weighted_value', 'sum'),
        avg_velocity    = ('deal_velocity_days', 'mean')
    ).reindex(stage_order).round(2).reset_index()

    pipe['conversion_pct'] = (
        pipe['deal_count'] / pipe['deal_count'].sum() * 100
    ).round(1)

    pipe.to_csv(
        os.path.join(PROC_DIR, 'pipeline_by_stage.csv'), index=False)
    print("  pipeline_by_stage.csv        ✓")
    return pipe


# ── 4. Monthly Revenue Trend ──────────────────────────────────────
def calc_revenue_trend(deals):
    won = deals[deals['is_won']].copy()
    won['month'] = won['close_date'].dt.to_period('M')

    monthly = won.groupby('month').agg(
        deals_won   = ('deal_id',    'count'),
        revenue     = ('deal_value', 'sum'),
        avg_deal    = ('deal_value', 'mean')
    ).reset_index()
    monthly['month']   = monthly['month'].astype(str)
    monthly['revenue'] = monthly['revenue'].round(2)
    monthly['avg_deal']= monthly['avg_deal'].round(2)

    # MoM growth
    monthly['mom_growth_pct'] = (
        monthly['revenue'].pct_change() * 100
    ).round(1)

    # 3-month rolling average
    monthly['rolling_3m_avg'] = (
        monthly['revenue'].rolling(3).mean()
    ).round(2)

    monthly.to_csv(
        os.path.join(PROC_DIR, 'revenue_trend.csv'), index=False)
    print("  revenue_trend.csv            ✓")
    return monthly


# ── 5. Churn Risk Summary ─────────────────────────────────────────
def calc_churn_risk(companies, deals):
    churn = companies.groupby('churn_risk_band').agg(
        company_count = ('company_id',   'count'),
        avg_ltv       = ('customer_ltv', 'mean'),
        avg_churn_score = ('churn_score','mean'),
        total_ltv     = ('customer_ltv', 'sum')
    ).round(2).reset_index()

    # attach deal revenue per company
    won_by_company = deals[deals['is_won']].groupby(
        'company_id')['deal_value'].sum().reset_index()
    won_by_company.columns = ['company_id', 'revenue_won']

    comp_with_rev = companies.merge(
        won_by_company, on='company_id', how='left')
    comp_with_rev['revenue_won'] = comp_with_rev['revenue_won'].fillna(0)

    at_risk = comp_with_rev[
        comp_with_rev['churn_risk_band'].isin(['High','Critical'])
    ][['company_id','company_name','industry','region',
       'churn_score','customer_ltv','revenue_won',
       'churn_risk_band']].sort_values(
           'churn_score', ascending=False).head(20)

    churn.to_csv(
        os.path.join(PROC_DIR, 'churn_risk_summary.csv'), index=False)
    at_risk.to_csv(
        os.path.join(PROC_DIR, 'churn_at_risk_top20.csv'), index=False)
    print("  churn_risk_summary.csv       ✓")
    print("  churn_at_risk_top20.csv      ✓")
    return churn, at_risk


# ── 6. Loss Analysis ──────────────────────────────────────────────
def calc_loss_analysis(deals):
    lost = deals[deals['is_lost']].copy()

    loss = lost.groupby('loss_reason').agg(
        deal_count  = ('deal_id',    'count'),
        total_value = ('deal_value', 'sum'),
        avg_value   = ('deal_value', 'mean')
    ).round(2).reset_index()
    loss['pct_of_losses'] = (
        loss['deal_count'] / loss['deal_count'].sum() * 100
    ).round(1)
    loss = loss.sort_values('total_value', ascending=False)

    loss.to_csv(
        os.path.join(PROC_DIR, 'loss_analysis.csv'), index=False)
    print("  loss_analysis.csv            ✓")
    return loss


# ── 7. Deal Velocity by Product ───────────────────────────────────
def calc_deal_velocity(deals):
    velocity = deals[deals['deal_velocity_days'].notna()].groupby(
        'product'
    ).agg(
        avg_velocity   = ('deal_velocity_days', 'mean'),
        median_velocity= ('deal_velocity_days', 'median'),
        min_velocity   = ('deal_velocity_days', 'min'),
        max_velocity   = ('deal_velocity_days', 'max'),
        deal_count     = ('deal_id',            'count')
    ).round(1).reset_index()

    velocity.to_csv(
        os.path.join(PROC_DIR, 'deal_velocity.csv'), index=False)
    print("  deal_velocity.csv            ✓")
    return velocity


# ── 8. Product Performance ────────────────────────────────────────
def calc_product_performance(deals):
    prod = deals.groupby('product').agg(
        total_deals  = ('deal_id',        'count'),
        won_deals    = ('is_won',         'sum'),
        lost_deals   = ('is_lost',        'sum'),
        total_value  = ('deal_value',     'sum'),
        avg_value    = ('deal_value',     'mean'),
        weighted     = ('weighted_value', 'sum')
    ).round(2).reset_index()

    prod['win_rate_pct'] = (
        prod['won_deals'] / prod['total_deals'] * 100
    ).round(1)

    won_rev = deals[deals['is_won']].groupby(
        'product')['deal_value'].sum()
    prod['revenue_won'] = prod['product'].map(won_rev).fillna(0).round(2)

    prod.to_csv(
        os.path.join(PROC_DIR, 'product_performance.csv'), index=False)
    print("  product_performance.csv      ✓")
    return prod


# ── 9. Region Performance ─────────────────────────────────────────
def calc_region_performance(deals, companies):
    merged = deals.merge(
        companies[['company_id','region','industry']],
        on='company_id', how='left')

    region = merged.groupby('region').agg(
        total_deals = ('deal_id',        'count'),
        won_deals   = ('is_won',         'sum'),
        total_value = ('deal_value',     'sum'),
        weighted    = ('weighted_value', 'sum'),
        avg_deal    = ('deal_value',     'mean')
    ).round(2).reset_index()

    region['win_rate_pct'] = (
        region['won_deals'] / region['total_deals'] * 100
    ).round(1)

    won_rev = merged[merged['is_won']].groupby(
        'region')['deal_value'].sum()
    region['revenue_won'] = (
        region['region'].map(won_rev).fillna(0).round(2))

    region.to_csv(
        os.path.join(PROC_DIR, 'region_performance.csv'), index=False)
    print("  region_performance.csv       ✓")
    return region


# ── 10. Activity Effectiveness ────────────────────────────────────
def calc_activity_effectiveness(activities, deals):
    merged = activities.merge(
        deals[['deal_id','is_won','stage']], on='deal_id', how='left')

    eff = merged.groupby('activity_type').agg(
        total_activities = ('activity_id', 'count'),
        positive_outcomes= ('outcome',
                            lambda x: (x == 'Positive').sum()),
        linked_won_deals = ('is_won', 'sum'),
        avg_duration     = ('duration_mins', 'mean')
    ).round(2).reset_index()

    eff['positive_rate_pct'] = (
        eff['positive_outcomes'] /
        eff['total_activities'] * 100
    ).round(1)

    eff.to_csv(
        os.path.join(PROC_DIR, 'activity_effectiveness.csv'), index=False)
    print("  activity_effectiveness.csv   ✓")
    return eff


# ── Main ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\nPipelineIQ — Running Analysis...\n")
    reps, companies, contacts, deals, activities = load()

    print("\n── KPI Summary ──────────────────────────────────────────")
    calc_kpis(deals, companies, activities)

    print("\n── Rep Performance ──────────────────────────────────────")
    calc_rep_performance(deals, reps)

    print("\n── Pipeline by Stage ────────────────────────────────────")
    calc_pipeline_stages(deals)

    print("\n── Revenue Trend ────────────────────────────────────────")
    calc_revenue_trend(deals)

    print("\n── Churn Risk ───────────────────────────────────────────")
    calc_churn_risk(companies, deals)

    print("\n── Loss Analysis ────────────────────────────────────────")
    calc_loss_analysis(deals)

    print("\n── Deal Velocity ────────────────────────────────────────")
    calc_deal_velocity(deals)

    print("\n── Product Performance ──────────────────────────────────")
    calc_product_performance(deals)

    print("\n── Region Performance ───────────────────────────────────")
    calc_region_performance(deals, companies)

    print("\n── Activity Effectiveness ───────────────────────────────")
    calc_activity_effectiveness(activities, deals)

    print("\n✓ All analysis files written to data/processed/\n")