"""
PipelineIQ — Dashboard Data Generator
Project 4: CRM System Analysis
Gelmish Technology Ltd
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

PROC_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
DASH_DIR = os.path.join(os.path.dirname(__file__), '..', 'dashboard')
os.makedirs(DASH_DIR, exist_ok=True)
OUTPUT = os.path.join(DASH_DIR, 'data.js')

def load_csv(filename):
    path = os.path.join(PROC_DIR, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    print(f"  WARNING: {filename} not found")
    return pd.DataFrame()

def safe(val):
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return round(float(val), 2)
    if isinstance(val, float) and np.isnan(val):
        return None
    return val

def df_to_records(df, cols=None):
    if df.empty:
        return []
    if cols:
        df = df[[c for c in cols if c in df.columns]]
    records = []
    for row in df.to_dict(orient='records'):
        records.append({k: safe(v) for k, v in row.items()})
    return records

def build_kpis():
    df = load_csv('kpi_summary.csv')
    if df.empty:
        return {}
    r = df.iloc[0]
    return {
        'total_revenue':        safe(r['total_revenue_won']),
        'pipeline_weighted':    safe(r['total_pipeline_weighted']),
        'total_deals':          safe(r['total_deals']),
        'deals_won':            safe(r['deals_won']),
        'deals_lost':           safe(r['deals_lost']),
        'deals_open':           safe(r['deals_open']),
        'win_rate':             safe(r['win_rate_pct']),
        'avg_deal_size':        safe(r['avg_deal_size']),
        'avg_velocity_days':    safe(r['avg_deal_velocity_days']),
        'companies_high_churn': safe(r['companies_high_churn']),
        'avg_customer_ltv':     safe(r['avg_customer_ltv']),
        'total_activities':     safe(r['total_activities']),
        'activity_positive_rate': safe(r['activity_positive_rate']),
    }

def build_pipeline():
    df = load_csv('pipeline_by_stage.csv')
    if df.empty:
        return {}
    return {
        'labels':          df['stage'].tolist(),
        'deal_counts':     [safe(v) for v in df['deal_count']],
        'total_values':    [safe(v) for v in df['total_value']],
        'weighted_values': [safe(v) for v in df['weighted_value']],
        'avg_velocities':  [safe(v) for v in df['avg_velocity']],
        'conversion_pcts': [safe(v) for v in df['conversion_pct']],
    }

def build_revenue_trend():
    df = load_csv('revenue_trend.csv')
    if df.empty:
        return {}
    df = df.sort_values('month')
    return {
        'labels':     df['month'].tolist(),
        'revenue':    [safe(v) for v in df['revenue']],
        'deals_won':  [safe(v) for v in df['deals_won']],
        'avg_deal':   [safe(v) for v in df['avg_deal']],
        'mom_growth': [safe(v) for v in df['mom_growth_pct']],
        'rolling_3m': [safe(v) for v in df['rolling_3m_avg']],
    }

def build_rep_performance():
    df = load_csv('rep_performance.csv')
    if df.empty:
        return {}
    df = df.sort_values('revenue_won', ascending=False)
    return {
        'labels':           df['rep_name'].tolist(),
        'revenue_won':      [safe(v) for v in df['revenue_won']],
        'win_rate':         [safe(v) for v in df['win_rate_pct']],
        'quota_attainment': [safe(v) for v in df['quota_attainment_pct']],
        'total_deals':      [safe(v) for v in df['total_deals']],
        'won_deals':        [safe(v) for v in df['won_deals']],
        'avg_deal_size':    [safe(v) for v in df['avg_deal_size']],
        'avg_velocity':     [safe(v) for v in df['avg_velocity']],
        'annual_quota':     [safe(v) for v in df['annual_quota']],
        'regions':          df['region'].tolist(),
        'table':            df_to_records(df, [
                                'rep_name','region','title',
                                'total_deals','won_deals',
                                'revenue_won','win_rate_pct',
                                'quota_attainment_pct',
                                'avg_deal_size','avg_velocity'
                            ]),
    }

def build_churn():
    summary = load_csv('churn_risk_summary.csv')
    top20   = load_csv('churn_at_risk_top20.csv')
    band_order = ['Low','Medium','High','Critical']
    if not summary.empty:
        summary['churn_risk_band'] = pd.Categorical(
            summary['churn_risk_band'],
            categories=band_order, ordered=True)
        summary = summary.sort_values('churn_risk_band')
    return {
        'band_labels':    summary['churn_risk_band'].tolist()
                          if not summary.empty else [],
        'company_counts': [safe(v) for v in summary['company_count']]
                          if not summary.empty else [],
        'avg_ltv':        [safe(v) for v in summary['avg_ltv']]
                          if not summary.empty else [],
        'total_ltv':      [safe(v) for v in summary['total_ltv']]
                          if not summary.empty else [],
        'at_risk_table':  df_to_records(top20, [
                              'company_name','industry',
                              'region','churn_score',
                              'customer_ltv','revenue_won',
                              'churn_risk_band'
                          ]) if not top20.empty else [],
    }

def build_loss_analysis():
    df = load_csv('loss_analysis.csv')
    if df.empty:
        return {}
    df = df.sort_values('total_value', ascending=False)
    return {
        'labels':       df['loss_reason'].tolist(),
        'deal_counts':  [safe(v) for v in df['deal_count']],
        'total_values': [safe(v) for v in df['total_value']],
        'pct_losses':   [safe(v) for v in df['pct_of_losses']],
    }

def build_product_performance():
    df = load_csv('product_performance.csv')
    if df.empty:
        return {}
    return {
        'labels':      df['product'].tolist(),
        'revenue_won': [safe(v) for v in df['revenue_won']],
        'win_rate':    [safe(v) for v in df['win_rate_pct']],
        'total_deals': [safe(v) for v in df['total_deals']],
        'avg_value':   [safe(v) for v in df['avg_value']],
        'weighted':    [safe(v) for v in df['weighted']],
    }

def build_region_performance():
    df = load_csv('region_performance.csv')
    if df.empty:
        return {}
    df = df.sort_values('revenue_won', ascending=False)
    return {
        'labels':      df['region'].tolist(),
        'revenue_won': [safe(v) for v in df['revenue_won']],
        'win_rate':    [safe(v) for v in df['win_rate_pct']],
        'total_deals': [safe(v) for v in df['total_deals']],
        'avg_deal':    [safe(v) for v in df['avg_deal']],
    }

def build_activity_effectiveness():
    df = load_csv('activity_effectiveness.csv')
    if df.empty:
        return {}
    df = df.sort_values('total_activities', ascending=False)
    return {
        'labels':           df['activity_type'].tolist(),
        'total_activities': [safe(v) for v in df['total_activities']],
        'positive_rate':    [safe(v) for v in df['positive_rate_pct']],
        'avg_duration':     [safe(v) for v in df['avg_duration']],
        'linked_won':       [safe(v) for v in df['linked_won_deals']],
    }

def build_deal_velocity():
    df = load_csv('deal_velocity.csv')
    if df.empty:
        return {}
    return {
        'labels':          df['product'].tolist(),
        'avg_velocity':    [safe(v) for v in df['avg_velocity']],
        'median_velocity': [safe(v) for v in df['median_velocity']],
        'min_velocity':    [safe(v) for v in df['min_velocity']],
        'max_velocity':    [safe(v) for v in df['max_velocity']],
    }

def main():
    print("\nPipelineIQ — Building dashboard data...\n")
    payload = {
        'meta': {
            'project':      'PipelineIQ — CRM System Analysis',
            'company':      'Gelmish Technology Ltd',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'author':       'George Jerry Eze',
        },
        'kpis':                   build_kpis(),
        'pipeline':               build_pipeline(),
        'revenue_trend':          build_revenue_trend(),
        'rep_performance':        build_rep_performance(),
        'churn':                  build_churn(),
        'loss_analysis':          build_loss_analysis(),
        'product_performance':    build_product_performance(),
        'region_performance':     build_region_performance(),
        'activity_effectiveness': build_activity_effectiveness(),
        'deal_velocity':          build_deal_velocity(),
    }
    js = 'const DASHBOARD_DATA = ' + json.dumps(payload, indent=2) + ';'
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(js)
    size_kb = os.path.getsize(OUTPUT) / 1024
    print(f"  ✓ data.js written → {os.path.abspath(OUTPUT)}")
    print(f"  ✓ File size       → {size_kb:.1f} KB\n")

if __name__ == '__main__':
    main()