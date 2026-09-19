"""
PipelineIQ — CRM Data Generator (Fast)
Project 4: CRM System Analysis
Gelmish Technology Ltd
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
os.makedirs(RAW_DIR, exist_ok=True)

INDUSTRIES     = ['FinTech','HealthTech','EdTech','RetailTech',
                  'HRTech','LegalTech','PropTech','CyberSecurity']
COMPANY_SIZES  = ['1-10','11-50','51-200','201-500','501-1000','1000+']
REGIONS        = ['North America','Europe','APAC',
                  'Latin America','Middle East & Africa']
REP_NAMES      = [
    ('R001','Sarah Mitchell',  'Senior AE',        'North America'),
    ('R002','James Okafor',    'Account Executive', 'Europe'),
    ('R003','Priya Nair',      'Senior AE',        'APAC'),
    ('R004','Carlos Herrera',  'Account Executive', 'Latin America'),
    ('R005','Emma Thornton',   'Junior AE',        'Middle East & Africa'),
]
DEAL_STAGES   = ['Prospecting','Qualification','Proposal',
                 'Negotiation','Closed Won','Closed Lost']
STAGE_WEIGHTS = [0.20,0.25,0.20,0.15,0.12,0.08]
STAGE_PROB    = {'Prospecting':0.10,'Qualification':0.25,
                 'Proposal':0.50,'Negotiation':0.75,
                 'Closed Won':1.00,'Closed Lost':0.00}
LOSS_REASONS  = ['Price too high','Chose competitor','No budget',
                 'Project cancelled','Poor fit','No decision made']
ACTIVITY_TYPES= ['Email','Call','Demo','Meeting',
                 'Proposal Sent','Follow-up']
PRODUCTS      = ['PipelineIQ Starter','PipelineIQ Pro',
                 'PipelineIQ Enterprise']
PRODUCT_PRICES= {
    'PipelineIQ Starter':    (5000,  15000),
    'PipelineIQ Pro':        (15000, 50000),
    'PipelineIQ Enterprise': (50000,250000),
}
START_DATE = datetime(2023,1,1)
END_DATE   = datetime(2024,12,31)

# 500 unique names guaranteed — number suffix ensures uniqueness
COMPANY_PREFIXES = [
    'Apex','Nexus','Orion','Vega','Atlas','Nova','Helix','Zenith',
    'Pinnacle','Vertex','Stratos','Arcus','Solara','Lumex','Crestline',
    'Irongate','Bluewave','Redpoint','Horizon','Meridian','Quantum','Radiant',
    'Cobalt','Ember','Flint','Glacier','Harbor','Indigo'
]
COMPANY_SUFFIXES = [
    'Solutions','Systems','Technologies','Ventures','Group','Labs',
    'Digital','Analytics','Consulting','Dynamics','Networks','Platforms',
    'Intelligence','Innovations','Enterprises','Partners','Services',
    'Global','Cloud','Data'
]
FIRST_NAMES = [
    'James','Sarah','Michael','Emma','David','Olivia','Daniel','Sophia',
    'Chris','Ava','Matthew','Isabella','Joshua','Mia','Andrew','Charlotte',
    'Ethan','Amelia','Ryan','Harper','Kwame','Adaeze','Chidi','Ngozi',
    'Emeka','Fatima','Yusuf','Priya','Raj','Ananya','Carlos','Maria','Luis','Ana'
]
LAST_NAMES = [
    'Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis',
    'Wilson','Taylor','Anderson','Thomas','Jackson','White','Harris','Martin',
    'Thompson','Moore','Okafor','Eze','Nwosu','Adeleke','Ibrahim','Patel',
    'Kumar','Sharma','Herrera','Lopez','Nguyen','Chen'
]
JOB_TITLES = [
    'CEO','CTO','CFO','VP Sales','VP Operations','Head of IT',
    'Director of Engineering','Product Manager','Operations Manager',
    'Procurement Manager','IT Manager','Data Manager'
]

def random_date(start, end):
    return start + timedelta(days=random.randint(0,(end-start).days))

def random_date_after(date, max_days=180):
    return date + timedelta(days=random.randint(1,max_days))


# ── 1. Sales Reps ─────────────────────────────────────────────────
def generate_reps():
    reps = []
    for rep_id, name, title, region in REP_NAMES:
        reps.append({
            'rep_id':       rep_id,
            'rep_name':     name,
            'title':        title,
            'region':       region,
            'hire_date':    random_date(
                                datetime(2020,1,1),
                                datetime(2022,12,31)).date(),
            'annual_quota': random.choice([300000,400000,500000,600000]),
            'active':       True
        })
    df = pd.DataFrame(reps)
    df.to_csv(os.path.join(RAW_DIR,'sales_reps.csv'), index=False)
    print(f"  sales_reps.csv     → {len(df)} rows")
    return df


# ── 2. Companies — guaranteed unique names via index suffix ───────
def generate_companies(n=500):
    companies = []
    for i in range(1, n+1):
        prefix = random.choice(COMPANY_PREFIXES)
        suffix = random.choice(COMPANY_SUFFIXES)
        # append index to guarantee uniqueness — no loop needed
        name   = f"{prefix} {suffix} {i:03d}"
        companies.append({
            'company_id':     f"C{i:04d}",
            'company_name':   name,
            'industry':       random.choice(INDUSTRIES),
            'company_size':   random.choice(COMPANY_SIZES),
            'region':         random.choice(REGIONS),
            'annual_revenue': random.choice(
                                [None,100000,500000,1000000,
                                 5000000,10000000,50000000]),
            'churn_score':    round(np.random.beta(2,5),3),
            'customer_ltv':   round(random.uniform(10000,500000),2),
            'created_date':   random_date(
                                datetime(2022,1,1),START_DATE).date(),
            'is_active':      random.choices(
                                [True,False],weights=[0.82,0.18])[0]
        })
    df = pd.DataFrame(companies)
    df.to_csv(os.path.join(RAW_DIR,'companies.csv'), index=False)
    print(f"  companies.csv      → {len(df)} rows")
    return df


# ── 3. Contacts — dict lookup, no row scan ────────────────────────
def generate_contacts(companies_df, n=1500):
    company_ids    = companies_df['company_id'].tolist()
    company_lookup = companies_df.set_index('company_id')[
                         'region'].to_dict()
    contacts = []
    for i in range(1, n+1):
        first      = random.choice(FIRST_NAMES)
        last       = random.choice(LAST_NAMES)
        company_id = random.choice(company_ids)
        contacts.append({
            'contact_id':   f"CON{i:05d}",
            'first_name':   first,
            'last_name':    last,
            'email':        (f"{first.lower()}.{last.lower()}{i}"
                             f"@{company_id.lower()}.com"),
            'job_title':    random.choice(JOB_TITLES),
            'company_id':   company_id,
            'region':       company_lookup[company_id],
            'phone':        (f"+1-{random.randint(200,999)}-"
                             f"{random.randint(100,999)}-"
                             f"{random.randint(1000,9999)}"),
            'is_primary':   random.choices(
                                [True,False],weights=[0.3,0.7])[0],
            'created_date': random_date(
                                datetime(2022,6,1),START_DATE).date()
        })
    df = pd.DataFrame(contacts)
    df.to_csv(os.path.join(RAW_DIR,'contacts.csv'), index=False)
    print(f"  contacts.csv       → {len(df)} rows")
    return df


# ── 4. Deals ──────────────────────────────────────────────────────
def generate_deals(companies_df, reps_df, n=1200):
    company_ids = companies_df['company_id'].tolist()
    rep_ids     = reps_df['rep_id'].tolist()
    deals = []
    for i in range(1, n+1):
        product              = random.choice(PRODUCTS)
        price_min, price_max = PRODUCT_PRICES[product]
        deal_value           = round(random.uniform(price_min,price_max),2)
        stage                = random.choices(DEAL_STAGES,
                                              weights=STAGE_WEIGHTS)[0]
        rep_id               = random.choice(rep_ids)
        created              = random_date(START_DATE,END_DATE)
        close_date           = None
        expected_close       = None
        loss_reason          = None
        velocity             = None

        if stage in ('Closed Won','Closed Lost'):
            cd         = random_date_after(created,120)
            close_date = min(cd,END_DATE)
            velocity   = (close_date - created).days
        else:
            expected_close = random_date_after(created,90)

        if stage == 'Closed Lost':
            loss_reason = random.choice(LOSS_REASONS)

        deals.append({
            'deal_id':             f"D{i:05d}",
            'company_id':          random.choice(company_ids),
            'rep_id':              rep_id,
            'deal_name':           f"{product} — Deal {i:04d}",
            'product':             product,
            'deal_value':          deal_value,
            'stage':               stage,
            'probability':         int(STAGE_PROB[stage]*100),
            'created_date':        created.date(),
            'close_date':          close_date.date()
                                       if close_date else None,
            'expected_close_date': expected_close.date()
                                       if expected_close else None,
            'loss_reason':         loss_reason,
            'deal_velocity_days':  velocity,
            'weighted_value':      round(
                                       deal_value*STAGE_PROB[stage],2)
        })
    df = pd.DataFrame(deals)
    df.to_csv(os.path.join(RAW_DIR,'deals.csv'), index=False)
    print(f"  deals.csv          → {len(df)} rows")
    return df


# ── 5. Activities — vectorised index selection ────────────────────
def generate_activities(deals_df, reps_df, n=4800):
    deal_indices = np.random.randint(0,len(deals_df),size=n)
    activities   = []
    for i, idx in enumerate(deal_indices, start=1):
        deal_row = deals_df.iloc[idx]
        base     = datetime.combine(deal_row['created_date'],
                                    datetime.min.time())
        cap      = min(base + timedelta(days=120),END_DATE)
        act_date = random_date(base,cap)
        activities.append({
            'activity_id':   f"A{i:06d}",
            'deal_id':       deal_row['deal_id'],
            'rep_id':        deal_row['rep_id'],
            'activity_type': random.choice(ACTIVITY_TYPES),
            'activity_date': act_date.date(),
            'duration_mins': random.choice([15,30,45,60,90,120]),
            'outcome':       random.choices(
                                 ['Positive','Neutral',
                                  'Negative','No Response'],
                                 weights=[0.40,0.30,0.15,0.15])[0],
            'notes':         random.choice([
                                 'Follow up scheduled',
                                 'Sent pricing deck',
                                 'Decision deferred',
                                 'Champion confirmed',
                                 'Budget approved',
                                 'Stakeholder meeting set',
                                 'Awaiting legal review',
                                 None])
        })
    df = pd.DataFrame(activities)
    df.to_csv(os.path.join(RAW_DIR,'activities.csv'), index=False)
    print(f"  activities.csv     → {len(df)} rows")
    return df


# ── Main ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\nPipelineIQ — Generating CRM data...\n")
    reps       = generate_reps()
    companies  = generate_companies(500)
    contacts   = generate_contacts(companies,1500)
    deals      = generate_deals(companies,reps,1200)
    activities = generate_activities(deals,reps,4800)
    print(f"\n✓ All files written to: {os.path.abspath(RAW_DIR)}\n")