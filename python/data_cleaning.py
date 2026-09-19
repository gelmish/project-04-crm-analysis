"""
PipelineIQ — Data Cleaning
Project 4: CRM System Analysis
Gelmish Technology Ltd
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

RAW_DIR  = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
PROC_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
os.makedirs(PROC_DIR, exist_ok=True)

audit_log = []

def log(table, issue, original, fixed):
    audit_log.append({
        'table':     table,
        'issue':     issue,
        'original':  str(original),
        'fixed':     str(fixed),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

def save_audit():
    df = pd.DataFrame(audit_log)
    path = os.path.join(PROC_DIR, 'cleaning_audit.csv')
    df.to_csv(path, index=False)
    print(f"  cleaning_audit.csv       → {len(df)} log entries")


def clean_reps():
    df = pd.read_csv(os.path.join(RAW_DIR, 'sales_reps.csv'))
    n  = len(df)

    dupes = df.duplicated(subset='rep_id').sum()
    if dupes > 0:
        df = df.drop_duplicates(subset='rep_id')
        log('sales_reps', 'Duplicate rep_id removed', dupes, 0)

    df['hire_date'] = pd.to_datetime(df['hire_date'])
    df['active']    = df['active'].astype(bool)

    null_count = df.isnull().sum().sum()
    if null_count > 0:
        df = df.fillna('UNKNOWN')
        log('sales_reps', 'Nulls filled', null_count, 'UNKNOWN')

    df['years_of_service'] = (
        (pd.Timestamp.now() - df['hire_date']).dt.days / 365.25
    ).round(1)

    df.to_csv(os.path.join(PROC_DIR, 'sales_reps_clean.csv'), index=False)
    print(f"  sales_reps_clean.csv     → {len(df)} rows (was {n})")
    return df


def clean_companies():
    df = pd.read_csv(os.path.join(RAW_DIR, 'companies.csv'))
    n  = len(df)

    dupes = df.duplicated(subset='company_id').sum()
    if dupes > 0:
        df = df.drop_duplicates(subset='company_id')
        log('companies', 'Duplicate company_id removed', dupes, 0)

    df['created_date'] = pd.to_datetime(df['created_date'])
    df['is_active']    = df['is_active'].astype(bool)
    df['churn_score']  = df['churn_score'].astype(float)
    df['customer_ltv'] = df['customer_ltv'].astype(float)

    rev_nulls = df['annual_revenue'].isnull().sum()
    if rev_nulls > 0:
        median_rev = df['annual_revenue'].median()
        df['annual_revenue'] = df['annual_revenue'].fillna(median_rev)
        log('companies', 'annual_revenue nulls filled with median',
            rev_nulls, median_rev)

    size_order = ['1-10','11-50','51-200','201-500','501-1000','1000+']
    df['company_size'] = pd.Categorical(
        df['company_size'], categories=size_order, ordered=True)

    df['churn_risk_band'] = pd.cut(
        df['churn_score'],
        bins=[0, 0.2, 0.4, 0.6, 1.0],
        labels=['Low','Medium','High','Critical']
    )

    df['ltv_band'] = pd.cut(
        df['customer_ltv'],
        bins=[0, 50000, 150000, 300000, 500001],
        labels=['Bronze','Silver','Gold','Platinum']
    )

    df.to_csv(os.path.join(PROC_DIR, 'companies_clean.csv'), index=False)
    print(f"  companies_clean.csv      → {len(df)} rows (was {n})")
    return df


def clean_contacts():
    df = pd.read_csv(os.path.join(RAW_DIR, 'contacts.csv'))
    n  = len(df)

    dupes = df.duplicated(subset='contact_id').sum()
    if dupes > 0:
        df = df.drop_duplicates(subset='contact_id')
        log('contacts', 'Duplicate contact_id removed', dupes, 0)

    invalid_email = ~df['email'].str.contains('@', na=False)
    invalid_count = invalid_email.sum()
    if invalid_count > 0:
        df.loc[invalid_email, 'email'] = np.nan
        log('contacts', 'Invalid email set to null', invalid_count, np.nan)

    df['created_date'] = pd.to_datetime(df['created_date'])
    df['is_primary']   = df['is_primary'].astype(bool)
    df['first_name']   = df['first_name'].str.strip().str.title()
    df['last_name']    = df['last_name'].str.strip().str.title()
    df['full_name']    = df['first_name'] + ' ' + df['last_name']

    df.to_csv(os.path.join(PROC_DIR, 'contacts_clean.csv'), index=False)
    print(f"  contacts_clean.csv       → {len(df)} rows (was {n})")
    return df


def clean_deals():
    df = pd.read_csv(os.path.join(RAW_DIR, 'deals.csv'))
    n  = len(df)

    dupes = df.duplicated(subset='deal_id').sum()
    if dupes > 0:
        df = df.drop_duplicates(subset='deal_id')
        log('deals', 'Duplicate deal_id removed', dupes, 0)

    for col in ['created_date','close_date','expected_close_date']:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    df['deal_value']     = pd.to_numeric(df['deal_value'],     errors='coerce')
    df['weighted_value'] = pd.to_numeric(df['weighted_value'], errors='coerce')

    mask = (df['stage'] != 'Closed Lost') & df['loss_reason'].notna()
    open_with_loss = mask.sum()
    if open_with_loss > 0:
        df.loc[mask, 'loss_reason'] = np.nan
        log('deals', 'loss_reason cleared for non-lost deals',
            open_with_loss, np.nan)

    neg_values = (df['deal_value'] < 0).sum()
    if neg_values > 0:
        df.loc[df['deal_value'] < 0, 'deal_value'] = np.nan
        log('deals', 'Negative deal_value set to null', neg_values, np.nan)

    df['deal_size_band'] = pd.cut(
        df['deal_value'],
        bins=[0, 15000, 50000, 150000, 1000000],
        labels=['Small','Mid-Market','Enterprise','Strategic']
    )

    df['is_won']  = df['stage'] == 'Closed Won'
    df['is_lost'] = df['stage'] == 'Closed Lost'
    df['is_open'] = ~df['stage'].isin(['Closed Won','Closed Lost'])
    df['year_month'] = df['created_date'].dt.to_period('M').astype(str)

    df.to_csv(os.path.join(PROC_DIR, 'deals_clean.csv'), index=False)
    print(f"  deals_clean.csv          → {len(df)} rows (was {n})")
    return df


def clean_activities():
    df = pd.read_csv(os.path.join(RAW_DIR, 'activities.csv'))
    n  = len(df)

    dupes = df.duplicated(subset='activity_id').sum()
    if dupes > 0:
        df = df.drop_duplicates(subset='activity_id')
        log('activities', 'Duplicate activity_id removed', dupes, 0)

    df['activity_date'] = pd.to_datetime(df['activity_date'])
    df['duration_mins'] = pd.to_numeric(df['duration_mins'], errors='coerce')
    df['notes']         = df['notes'].fillna('')

    outliers = (df['duration_mins'] > 480).sum()
    if outliers > 0:
        df.loc[df['duration_mins'] > 480, 'duration_mins'] = 60
        log('activities', 'duration_mins > 480 capped at 60', outliers, 60)

    df['activity_month'] = df['activity_date'].dt.to_period('M').astype(str)
    df['is_positive']    = df['outcome'] == 'Positive'

    df.to_csv(os.path.join(PROC_DIR, 'activities_clean.csv'), index=False)
    print(f"  activities_clean.csv     → {len(df)} rows (was {n})")
    return df


if __name__ == '__main__':
    print("\nPipelineIQ — Cleaning data...\n")
    clean_reps()
    clean_companies()
    clean_contacts()
    clean_deals()
    clean_activities()
    save_audit()
    print("\n✓ All cleaned files written to data/processed/\n")