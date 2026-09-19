"""
PipelineIQ — Exploratory Data Analysis
Project 4: CRM System Analysis
Gelmish Technology Ltd
"""

import pandas as pd
import numpy as np
import os

PROC_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
REPORT   = os.path.join(PROC_DIR, 'eda_report.txt')

lines = []

def h(title):
    sep = '=' * 60
    lines.append(f"\n{sep}")
    lines.append(f"  {title}")
    lines.append(f"{sep}")
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)

def p(text=''):
    lines.append(str(text))
    print(text)

def load():
    reps       = pd.read_csv(os.path.join(PROC_DIR, 'sales_reps_clean.csv'))
    companies  = pd.read_csv(os.path.join(PROC_DIR, 'companies_clean.csv'))
    contacts   = pd.read_csv(os.path.join(PROC_DIR, 'contacts_clean.csv'))
    deals      = pd.read_csv(os.path.join(PROC_DIR, 'deals_clean.csv'))
    activities = pd.read_csv(os.path.join(PROC_DIR, 'activities_clean.csv'))

    deals['created_date']       = pd.to_datetime(deals['created_date'])
    deals['close_date']         = pd.to_datetime(deals['close_date'], errors='coerce')
    activities['activity_date'] = pd.to_datetime(activities['activity_date'])
    companies['created_date']   = pd.to_datetime(companies['created_date'])

    deals['is_won']  = deals['stage'] == 'Closed Won'
    deals['is_lost'] = deals['stage'] == 'Closed Lost'
    deals['is_open'] = ~deals['stage'].isin(['Closed Won','Closed Lost'])

    return reps, companies, contacts, deals, activities


def eda_overview(reps, companies, contacts, deals, activities):
    h("1. DATASET OVERVIEW")
    p(f"  Sales Reps   : {len(reps):>6,} rows | {reps.shape[1]} columns")
    p(f"  Companies    : {len(companies):>6,} rows | {companies.shape[1]} columns")
    p(f"  Contacts     : {len(contacts):>6,} rows | {contacts.shape[1]} columns")
    p(f"  Deals        : {len(deals):>6,} rows | {deals.shape[1]} columns")
    p(f"  Activities   : {len(activities):>6,} rows | {activities.shape[1]} columns")
    p()
    p(f"  Date range   : {deals['created_date'].min().date()} "
      f"to {deals['created_date'].max().date()}")
    p(f"  Total deal value : ${deals['deal_value'].sum():>15,.2f}")
    p(f"  Won deal value   : "
      f"${deals[deals['is_won']]['deal_value'].sum():>15,.2f}")


def eda_pipeline(deals):
    h("2. PIPELINE HEALTH")
    stage_summary = deals.groupby('stage').agg(
        deal_count  = ('deal_id',        'count'),
        total_value = ('deal_value',     'sum'),
        avg_value   = ('deal_value',     'mean'),
        weighted    = ('weighted_value', 'sum')
    ).round(2)
    p(stage_summary.to_string())
    p()
    won  = deals[deals['is_won']]
    lost = deals[deals['is_lost']]
    win_rate = len(won) / (len(won) + len(lost)) * 100 \
               if (len(won) + len(lost)) > 0 else 0
    p(f"  Win Rate    : {win_rate:.1f}%")
    p(f"  Won deals   : {len(won):,}  (${won['deal_value'].sum():,.2f})")
    p(f"  Lost deals  : {len(lost):,}  (${lost['deal_value'].sum():,.2f})")
    p()
    p("  Pipeline by Product:")
    prod = deals.groupby('product').agg(
        count = ('deal_id',    'count'),
        value = ('deal_value', 'sum'),
        won   = ('is_won',     'sum')
    )
    prod['win_rate_%'] = (prod['won'] / prod['count'] * 100).round(1)
    p(prod.to_string())


def eda_velocity(deals):
    h("3. DEAL VELOCITY")
    closed = deals[deals['deal_velocity_days'].notna()]
    p(f"  Avg velocity (all closed) : {closed['deal_velocity_days'].mean():.1f} days")
    p(f"  Avg velocity (Won)        : {closed[closed['is_won']]['deal_velocity_days'].mean():.1f} days")
    p(f"  Avg velocity (Lost)       : {closed[closed['is_lost']]['deal_velocity_days'].mean():.1f} days")
    p(f"  Median velocity           : {closed['deal_velocity_days'].median():.1f} days")
    p(f"  Fastest deal              : {closed['deal_velocity_days'].min():.0f} days")
    p(f"  Slowest deal              : {closed['deal_velocity_days'].max():.0f} days")


def eda_reps(deals, reps):
    h("4. SALES REP PERFORMANCE")
    merged = deals.merge(
        reps[['rep_id','rep_name']], on='rep_id', how='left')
    agg = merged.groupby('rep_name').agg(
        total_deals  = ('deal_id',            'count'),
        won_deals    = ('is_won',             'sum'),
        lost_deals   = ('is_lost',            'sum'),
        total_value  = ('deal_value',         'sum'),
        avg_deal     = ('deal_value',         'mean'),
        avg_velocity = ('deal_velocity_days', 'mean')
    ).round(2)
    agg['win_rate_%'] = (agg['won_deals'] / agg['total_deals'] * 100).round(1)
    won_rev = merged[merged['is_won']].groupby('rep_name')['deal_value'].sum()
    agg['revenue_won'] = agg.index.map(won_rev).fillna(0).round(2)
    p(agg.to_string())


def eda_customers(companies, deals):
    h("5. CUSTOMER & CHURN ANALYSIS")
    p("  Companies by Industry:")
    p(companies['industry'].value_counts().to_string())
    p()
    if 'churn_risk_band' in companies.columns:
        p("  Companies by Churn Risk Band:")
        p(companies['churn_risk_band'].value_counts().to_string())
    p()
    if 'ltv_band' in companies.columns:
        p("  Companies by LTV Band:")
        p(companies['ltv_band'].value_counts().to_string())
    p()
    p("  Active vs Inactive:")
    p(companies['is_active'].value_counts().to_string())
    p()
    p("  Top 10 Companies by LTV:")
    cols = ['company_name','industry','region','customer_ltv']
    if 'churn_score' in companies.columns:
        cols.append('churn_score')
    top10 = companies.nlargest(10, 'customer_ltv')[cols]
    p(top10.to_string(index=False))


def eda_revenue(deals):
    h("6. MONTHLY REVENUE TREND")
    won = deals[deals['is_won']].copy()
    won['month'] = won['close_date'].dt.to_period('M')
    monthly = won.groupby('month')['deal_value'].agg(
        deals='count', revenue='sum').reset_index()
    monthly['month']   = monthly['month'].astype(str)
    monthly['revenue'] = monthly['revenue'].round(2)
    p(monthly.to_string(index=False))
    p()
    p(f"  Best month  : "
      f"{monthly.loc[monthly['revenue'].idxmax(),'month']} "
      f"(${monthly['revenue'].max():,.2f})")
    p(f"  Worst month : "
      f"{monthly.loc[monthly['revenue'].idxmin(),'month']} "
      f"(${monthly['revenue'].min():,.2f})")
    p(f"  Avg monthly : ${monthly['revenue'].mean():,.2f}")


def eda_activities(activities, deals):
    h("7. SALES ACTIVITY ANALYSIS")
    p("  Activity Type Breakdown:")
    p(activities['activity_type'].value_counts().to_string())
    p()
    p("  Outcome Distribution:")
    p(activities['outcome'].value_counts().to_string())
    p()
    merged = activities.merge(
        deals[['deal_id','is_won']], on='deal_id', how='left')
    won_acts = merged[merged['is_won'] == True].groupby(
        'deal_id')['activity_id'].count()
    p("  Activities per Won Deal:")
    p(f"    Mean : {won_acts.mean():.1f}")
    p(f"    Max  : {won_acts.max()}")
    p(f"    Min  : {won_acts.min()}")


def eda_losses(deals):
    h("8. LOSS REASON ANALYSIS")
    lost = deals[deals['is_lost']]
    p(f"  Total Lost Deals : {len(lost):,}")
    p(f"  Total Lost Value : ${lost['deal_value'].sum():,.2f}")
    p()
    p("  Loss Reasons:")
    p(lost['loss_reason'].value_counts().to_string())
    p()
    p("  Lost Value by Reason:")
    p(lost.groupby('loss_reason')['deal_value']
      .agg(['count','sum','mean']).round(2).to_string())


if __name__ == '__main__':
    print("\nPipelineIQ — Running EDA...\n")
    reps, companies, contacts, deals, activities = load()
    eda_overview(reps, companies, contacts, deals, activities)
    eda_pipeline(deals)
    eda_velocity(deals)
    eda_reps(deals, reps)
    eda_customers(companies, deals)
    eda_revenue(deals)
    eda_activities(activities, deals)
    eda_losses(deals)

    with open(REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"\n✓ EDA report saved to: {os.path.abspath(REPORT)}\n")