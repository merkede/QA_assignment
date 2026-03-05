#!/usr/bin/env python3
"""
generate_html.py — QA Allocation Tool

Generates a static single-file HTML dashboard for QA assignment management.

Usage:
    python generate_html.py
    python generate_html.py --out ./dist

Output:
    index.html — Full self-contained dashboard application
"""

import argparse
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

DOWNLOADS = Path.home() / "Downloads"
BASE_CSV     = DOWNLOADS / "QA_ASSIGNMENT_BASE.csv"
BACKLOG_CSV  = DOWNLOADS / "QA_COLLEAGUE_CALL_BACKLOG.csv"
CHANNELS_CSV = DOWNLOADS / "QA_CONTACT_CHANNELS.csv"

TODAY = date(2026, 3, 5)

TEAMS = {
    "HD RTL K": {"tl": "Katy Brown",   "ccl": "Mark Evans",  "site": "London"},
    "HD RTL M": {"tl": "James Clarke", "ccl": "Mark Evans",  "site": "London"},
    "HD RTL P": {"tl": "Sarah Mills",  "ccl": "Lisa Webb",   "site": "Leeds"},
    "HD RTL Q": {"tl": "David Jones",  "ccl": "Lisa Webb",   "site": "Leeds"},
    "HD RTL A": {"tl": "Emma Wilson",  "ccl": "Paul Knight", "site": "London"},
}

SKILLS            = ["HD RTL CUSTOMER", "HD CLM CUSTOMER", "HD RTL ESCALATIONS",
                     "CANCELLATION CS", "NEW BUSINESS CS", "RETENTION CS"]
LOBS              = ["CAR", "HOME", "VAN"]
BRANDS            = ["HAS", "ADV", "PRE"]
TRANSACTION_TYPES = ["MTA", "NB", "REN", "CAN", "ENQ", "ESC"]

COLLEAGUE_NAMES = [
    "Alice Thompson", "Ben Carter",   "Clara Davis",   "Dan Evans",
    "Eva Foster",     "Frank Green",  "Grace Hill",    "Harry Irving",
    "Isla Jones",     "Jack King",    "Karen Lee",     "Liam Moore",
    "Mia Norton",     "Noah Owen",    "Olivia Park",   "Peter Quinn",
    "Quinn Reed",     "Rachel Scott", "Sam Turner",    "Tara Underwood",
]

# ─────────────────────────────────────────────────────────────────────────────
# SYNTHETIC DATA
# ─────────────────────────────────────────────────────────────────────────────

def _seed():
    random.seed(42)
    np.random.seed(42)


def make_colleagues() -> pd.DataFrame:
    _seed()
    team_keys = list(TEAMS.keys())
    rows = []
    for i, name in enumerate(COLLEAGUE_NAMES):
        team = team_keys[i % len(team_keys)]
        td   = TEAMS[team]
        required    = random.choice([2, 3, 4, 5, 6])
        completed   = random.randint(0, required)
        outstanding = required - completed
        last_contact = TODAY - timedelta(days=random.randint(0, 4))
        rows.append(dict(
            WkComDate="2026-03-02",
            Year=2026,
            Month="2026-03-01",
            Colleague_Name=name,
            Colleague_ID=200000 + i * 1337,
            Agent_EmployeeNumber=500000000 + i * 12345,
            Working_Days=5,
            Number_of_checks_required=required,
            Team_Leader=td["tl"],
            team_name=team,
            CCL=td["ccl"],
            Site=td["site"],
            ASSIGNED=outstanding,
            COMPLETED=completed,
            OUTSTANDING=outstanding,
            CONTACTS_LAST_7_DAYS=random.randint(20, 150),
            CONTACTS_LAST_30_DAYS=random.randint(80, 400),
            LAST_CONTACT_DATE=last_contact.isoformat(),
        ))
    return pd.DataFrame(rows)


def make_backlog(colleagues: pd.DataFrame) -> pd.DataFrame:
    _seed()
    rows = []
    cid  = 5_000_000_000
    for _, col in colleagues.iterrows():
        for _ in range(int(col["ASSIGNED"])):
            ad  = TODAY - timedelta(days=random.randint(0, 7))
            due = TODAY + timedelta(days=random.randint(-2, 14))
            rows.append(dict(
                ID=len(rows) + 1,
                EMPLOYEE_ID=col["Agent_EmployeeNumber"],
                CALL_ID=cid + len(rows),
                COLLEAGUE_NAME=col["Colleague_Name"],
                COLLEAGUE_ID=col["Colleague_ID"],
                TEAM=col["team_name"],
                TEAM_LEADER=col["Team_Leader"],
                CCL=col["CCL"],
                SITE=col["Site"],
                ASSIGNED_DATE=ad.isoformat(),
                PRIORITY=random.choice([1, 1, 1, 2, 2, 3]),
                STATUS="ASSIGNED",
                MATCHED_DATE=None,
                NEXT_ASSIGNMENT_DUE=due.isoformat(),
                EXPIRED_FLAG=False,
                IS_ACTIVE=True,
                SKILL_NAME=random.choice(SKILLS),
                TRANSACTION=random.randint(1, 3),
                VULNERABLE=random.choice([0, 0, 0, 0, 1]),
                TRANSACTION_TYPE=random.choice(TRANSACTION_TYPES),
                POLICY_NUMBER=random.randint(100000, 999999),
                LINE_OF_BUSINESS=random.choice(LOBS),
                BRAND=random.choice(BRANDS),
                CALL_AHT_MINUTE=random.randint(3, 45),
            ))
        for _ in range(int(col["COMPLETED"])):
            ad = TODAY - timedelta(days=random.randint(7, 30))
            md = TODAY - timedelta(days=random.randint(0, 6))
            rows.append(dict(
                ID=len(rows) + 1,
                EMPLOYEE_ID=col["Agent_EmployeeNumber"],
                CALL_ID=cid + len(rows),
                COLLEAGUE_NAME=col["Colleague_Name"],
                COLLEAGUE_ID=col["Colleague_ID"],
                TEAM=col["team_name"],
                TEAM_LEADER=col["Team_Leader"],
                CCL=col["CCL"],
                SITE=col["Site"],
                ASSIGNED_DATE=ad.isoformat(),
                PRIORITY=random.choice([1, 1, 2, 3]),
                STATUS="COMPLETED",
                MATCHED_DATE=md.isoformat(),
                NEXT_ASSIGNMENT_DUE=None,
                EXPIRED_FLAG=False,
                IS_ACTIVE=False,
                SKILL_NAME=random.choice(SKILLS),
                TRANSACTION=random.randint(1, 3),
                VULNERABLE=random.choice([0, 0, 0, 0, 1]),
                TRANSACTION_TYPE=random.choice(TRANSACTION_TYPES),
                POLICY_NUMBER=random.randint(100000, 999999),
                LINE_OF_BUSINESS=random.choice(LOBS),
                BRAND=random.choice(BRANDS),
                CALL_AHT_MINUTE=random.randint(3, 45),
            ))
    return pd.DataFrame(rows)


def make_contact_pool(colleagues: pd.DataFrame, n: int = 400) -> pd.DataFrame:
    _seed()
    rows  = []
    start = datetime(2026, 1, 1)
    for i in range(n):
        cs  = start + timedelta(hours=random.randint(0, 24 * 60), minutes=random.randint(0, 59))
        ce  = cs + timedelta(minutes=random.randint(3, 45))
        col = colleagues.iloc[i % len(colleagues)]
        rows.append(dict(
            MASTER_CONTACT_ID=30_000_000 + i,
            CONTACT_ID=3_000_000 + i,
            USER_EMPLOYEEID=col["Agent_EmployeeNumber"],
            COLLEAGUE_NAME=col["Colleague_Name"],
            CALL_START=cs.isoformat(),
            CALL_END=ce.isoformat(),
            CALL_AHT_MINUTE=(ce - cs).seconds // 60,
            SKILL_NAME=random.choice(SKILLS),
            TRANSACTION_TYPE=random.choice(TRANSACTION_TYPES),
            TEAM_LEADER=col["Team_Leader"],
            CCL=col["CCL"],
            SITE=col["Site"],
            DEPARTMENT="SERVICE",
            TENURE=random.randint(100, 2000),
            FTE=1,
            TRANSACTION=random.randint(1, 3),
            VULNERABLE=random.choice([0, 0, 0, 0, 1]),
            POLICY_NUMBER=random.randint(100000, 999999),
            BRAND=random.choice(BRANDS),
            STATUS="ACTIVE",
            LINE_OF_BUSINESS=random.choice(LOBS),
        ))
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_data():
    synth_base = make_colleagues()
    try:
        real_base = pd.read_csv(BASE_CSV)
        base_df   = pd.concat([real_base, synth_base], ignore_index=True)
        base_df   = base_df.drop_duplicates(subset=["Colleague_ID"], keep="first")
    except Exception:
        base_df = synth_base

    base_df["Completion_Pct"] = (
        base_df["COMPLETED"] / base_df["Number_of_checks_required"].replace(0, np.nan) * 100
    ).round(1).fillna(0)

    synth_bl = make_backlog(base_df)
    try:
        real_bl    = pd.read_csv(BACKLOG_CSV)
        backlog_df = pd.concat([real_bl, synth_bl], ignore_index=True)
    except Exception:
        backlog_df = synth_bl

    synth_pool = make_contact_pool(base_df)
    try:
        real_ch     = pd.read_csv(CHANNELS_CSV)
        channels_df = pd.concat([real_ch, synth_pool], ignore_index=True)
    except Exception:
        channels_df = synth_pool

    return base_df, backlog_df, channels_df


def df_to_json(df: pd.DataFrame) -> str:
    df = df.copy()
    for col in df.select_dtypes(include=["datetime64[ns]"]).columns:
        df[col] = df[col].dt.strftime("%Y-%m-%d")
    records = df.where(pd.notnull(df), None).to_dict("records")
    return json.dumps(records, default=str)

# ─────────────────────────────────────────────────────────────────────────────
# HTML TEMPLATE
# ─────────────────────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>QA Allocation Tool</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
  <style>
    :root {
      --primary:    #2563eb;
      --primary-dk: #1d4ed8;
      --primary-lt: #eff6ff;
      --success:    #16a34a;
      --success-lt: #f0fdf4;
      --warning:    #d97706;
      --warning-lt: #fffbeb;
      --danger:     #dc2626;
      --danger-lt:  #fef2f2;
      --slate-50:   #f8fafc;
      --slate-100:  #f1f5f9;
      --slate-200:  #e2e8f0;
      --slate-300:  #cbd5e1;
      --slate-500:  #64748b;
      --slate-600:  #475569;
      --slate-700:  #334155;
      --slate-800:  #1e293b;
      --slate-900:  #0f172a;
    }
    *, *::before, *::after { box-sizing: border-box; }
    body { font-family: 'Inter', sans-serif; background: var(--slate-100); color: var(--slate-700); margin: 0; }

    /* TOP BAR */
    .qa-topbar {
      background: var(--slate-900); color: #fff;
      padding: 0 2rem; height: 60px;
      display: flex; align-items: center; justify-content: space-between;
      position: sticky; top: 0; z-index: 1030;
      box-shadow: 0 2px 8px rgba(0,0,0,.35);
    }
    .topbar-left { display: flex; align-items: center; gap: .75rem; }
    .topbar-icon {
      width: 34px; height: 34px; border-radius: 8px;
      background: var(--primary); display: flex; align-items: center; justify-content: center; font-size: 1rem;
    }
    .topbar-title { font-size: 1.05rem; font-weight: 700; letter-spacing: -.02em; }
    .topbar-env {
      background: rgba(37,99,235,.25); border: 1px solid rgba(37,99,235,.4);
      color: #93c5fd; font-size: .65rem; font-weight: 700;
      padding: .15rem .5rem; border-radius: 4px; letter-spacing: .08em;
    }
    .topbar-refresh { font-size: .75rem; color: #94a3b8; display: flex; align-items: center; gap: .4rem; }

    /* FILTER BAR */
    .filter-bar {
      background: #fff; border-bottom: 1px solid var(--slate-200);
      padding: .65rem 2rem; position: sticky; top: 60px; z-index: 1020;
      box-shadow: 0 1px 4px rgba(0,0,0,.05);
    }
    .filter-label {
      font-size: .68rem; font-weight: 700; color: var(--slate-500);
      text-transform: uppercase; letter-spacing: .07em; margin-bottom: .2rem; display: block;
    }
    .filter-bar .form-select {
      font-size: .8rem; border-color: var(--slate-200); border-radius: 6px;
      min-width: 140px; height: 32px; padding: .2rem .5rem;
    }
    .filter-bar .form-select:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(37,99,235,.12); }
    .filter-summary { font-size: .75rem; color: var(--slate-500); }

    /* KPI */
    .kpi-section { padding: 1.25rem 2rem .75rem; }
    .kpi-card {
      background: #fff; border-radius: 12px; padding: 1.25rem 1.5rem;
      border: 1px solid var(--slate-200);
      transition: transform .15s, box-shadow .15s;
    }
    .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(0,0,0,.08); }
    .kpi-icon {
      width: 40px; height: 40px; border-radius: 10px;
      display: flex; align-items: center; justify-content: center; font-size: 1rem; margin-bottom: .8rem;
    }
    .kpi-icon.blue  { background: #dbeafe; color: var(--primary); }
    .kpi-icon.amber { background: #fef3c7; color: #b45309; }
    .kpi-icon.green { background: #dcfce7; color: var(--success); }
    .kpi-value { font-size: 2rem; font-weight: 800; line-height: 1; color: var(--slate-900); }
    .kpi-label { font-size: .7rem; font-weight: 700; color: var(--slate-500); text-transform: uppercase; letter-spacing: .07em; margin-top: .3rem; }
    .kpi-sub   { font-size: .75rem; color: var(--slate-500); margin-top: .4rem; }
    .kpi-progress { height: 4px; border-radius: 2px; background: var(--slate-200); margin-top: .9rem; }
    .kpi-progress-fill { height: 100%; border-radius: 2px; transition: width .6s ease; }

    /* SECTION */
    .section { padding: .75rem 2rem 1.25rem; }
    .section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: .85rem; }
    .section-title { font-size: .95rem; font-weight: 700; color: var(--slate-900); display: flex; align-items: center; gap: .5rem; }
    .section-icon { width: 28px; height: 28px; border-radius: 7px; display: flex; align-items: center; justify-content: center; font-size: .8rem; }
    .section-icon.blue  { background: #dbeafe; color: var(--primary); }
    .section-icon.amber { background: #fef3c7; color: #b45309; }
    .section-icon.green { background: #dcfce7; color: var(--success); }
    .count-chip {
      background: var(--slate-100); color: var(--slate-600); border: 1px solid var(--slate-200);
      font-size: .68rem; font-weight: 700; padding: .15rem .55rem; border-radius: 999px;
    }

    /* TABLE CARD */
    .table-card { background: #fff; border-radius: 12px; border: 1px solid var(--slate-200); overflow: hidden; }
    .table-inner { padding: .75rem 1rem 1rem; }

    /* DATATABLES */
    .dataTables_wrapper .dataTables_filter input,
    .dataTables_wrapper .dataTables_length select {
      border: 1px solid var(--slate-200); border-radius: 6px; font-size: .78rem; font-family: 'Inter', sans-serif;
    }
    .dataTables_wrapper .dataTables_filter input:focus { border-color: var(--primary); outline: none; box-shadow: 0 0 0 3px rgba(37,99,235,.1); }
    .dataTables_wrapper .dataTables_info,
    .dataTables_wrapper .dataTables_paginate { font-size: .75rem; }
    .dataTables_wrapper .page-link { font-size: .75rem; }
    table.dataTable thead th {
      font-size: .68rem !important; font-weight: 700 !important;
      text-transform: uppercase; letter-spacing: .07em;
      color: var(--slate-500) !important; background: var(--slate-50) !important;
      border-bottom: 1px solid var(--slate-200) !important;
      white-space: nowrap; padding: .6rem .75rem !important;
    }
    table.dataTable tbody td { font-size: .8rem; vertical-align: middle; padding: .55rem .75rem !important; border-color: var(--slate-100) !important; }
    table.dataTable tbody tr:hover td { background: var(--slate-50) !important; }
    table.dataTable.no-footer { border-bottom: none; }

    /* PROGRESS */
    .prog-wrap { display: flex; align-items: center; gap: .5rem; min-width: 130px; }
    .prog-bar  { flex: 1; height: 6px; background: var(--slate-200); border-radius: 3px; overflow: hidden; }
    .prog-fill { height: 100%; border-radius: 3px; transition: width .5s; }
    .prog-fill.g { background: var(--success); }
    .prog-fill.a { background: var(--warning); }
    .prog-fill.r { background: var(--danger); }
    .prog-pct  { font-size: .72rem; font-weight: 700; min-width: 38px; text-align: right; }
    .prog-pct.g { color: var(--success); }
    .prog-pct.a { color: var(--warning); }
    .prog-pct.r { color: var(--danger); }

    /* RAG */
    .rag { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: .35rem; }
    .rag.g { background: var(--success); }
    .rag.a { background: var(--warning); }
    .rag.r { background: var(--danger); }

    /* BADGES */
    .badge-assigned  { font-size: .65rem; font-weight: 700; padding: .2rem .55rem; border-radius: 999px; background: #fff7ed; color: #9a3412; border: 1px solid #fed7aa; }
    .badge-completed { font-size: .65rem; font-weight: 700; padding: .2rem .55rem; border-radius: 999px; background: #f0fdf4; color: #14532d; border: 1px solid #bbf7d0; }
    .badge-prio { font-size: .65rem; font-weight: 800; padding: .2rem .45rem; border-radius: 5px; }
    .prio-1 { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
    .prio-2 { background: #fffbeb; color: #92400e; border: 1px solid #fde68a; }
    .prio-3 { background: var(--slate-100); color: var(--slate-500); border: 1px solid var(--slate-200); }
    .badge-vuln { font-size: .62rem; font-weight: 700; padding: .15rem .4rem; border-radius: 4px; background: #f5f3ff; color: #5b21b6; border: 1px solid #ddd6fe; }

    /* DUE DATE */
    .due-overdue { color: var(--danger); font-weight: 700; font-size: .78rem; }
    .due-urgent  { color: var(--warning); font-weight: 600; font-size: .78rem; }
    .due-ok      { color: var(--success); font-size: .78rem; }

    /* EXPORT */
    .btn-export {
      font-size: .75rem; font-weight: 600; padding: .28rem .7rem; border-radius: 6px;
      border: 1px solid var(--slate-200); background: #fff; color: var(--slate-600);
      cursor: pointer; display: inline-flex; align-items: center; gap: .35rem; transition: all .15s;
    }
    .btn-export:hover { background: var(--slate-50); border-color: var(--slate-300); color: var(--slate-800); }

    /* FAB */
    .fab {
      position: fixed; bottom: 2rem; right: 2rem;
      background: var(--primary); color: #fff; border: none; border-radius: 14px;
      padding: .75rem 1.4rem; font-size: .88rem; font-weight: 700;
      display: inline-flex; align-items: center; gap: .5rem;
      box-shadow: 0 4px 20px rgba(37,99,235,.45);
      transition: all .2s; cursor: pointer; z-index: 900;
    }
    .fab:hover { background: var(--primary-dk); transform: translateY(-3px); box-shadow: 0 8px 30px rgba(37,99,235,.55); }

    /* MODAL */
    .modal-content { border-radius: 16px; border: none; box-shadow: 0 24px 60px rgba(0,0,0,.18); }
    .modal-header  { border-bottom: 1px solid var(--slate-200); padding: 1.1rem 1.5rem; }
    .modal-body    { padding: 1.5rem; }
    .modal-footer  { border-top: 1px solid var(--slate-200); padding: 1rem 1.5rem; }
    .modal-title   { font-weight: 700; font-size: .95rem; display: flex; align-items: center; gap: .5rem; }

    /* STEPS */
    .steps     { display: flex; align-items: center; gap: .5rem; margin-bottom: 1.5rem; }
    .step-dot  { width: 26px; height: 26px; border-radius: 50%; font-size: .72rem; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .step-dot.active   { background: var(--primary); color: #fff; }
    .step-dot.done     { background: var(--success); color: #fff; }
    .step-dot.inactive { background: var(--slate-200); color: var(--slate-500); }
    .step-line     { flex: 1; height: 2px; background: var(--slate-200); border-radius: 1px; }
    .step-line.done { background: var(--success); }

    /* PREF TOGGLE */
    .pref-toggle { display: flex; gap: .5rem; }
    .pref-btn {
      flex: 1; padding: .6rem .5rem; font-size: .82rem; font-weight: 600;
      border-radius: 8px; border: 2px solid var(--slate-200); background: #fff;
      cursor: pointer; transition: all .15s; text-align: center;
    }
    .pref-btn.active { border-color: var(--primary); background: var(--primary-lt); color: var(--primary); }

    /* RESULT CARDS */
    .result-card    { border-radius: 12px; padding: 1.25rem; animation: slideUp .25s ease; }
    .result-success { background: var(--success-lt); border: 1px solid #bbf7d0; }
    .result-failure { background: var(--danger-lt);  border: 1px solid #fecaca; }
    .result-title   { font-weight: 700; font-size: .9rem; margin-bottom: .75rem; display: flex; align-items: center; gap: .5rem; }
    .result-meta    { font-size: .78rem; margin-bottom: .75rem; }
    .detail-grid    { display: grid; grid-template-columns: auto 1fr; gap: .3rem .75rem; font-size: .78rem; margin-top: .75rem; }
    .detail-key     { font-weight: 600; color: var(--slate-600); white-space: nowrap; }
    .detail-val     { color: var(--slate-800); font-weight: 500; }

    /* COLLEAGUE PANEL */
    .col-info-panel {
      background: var(--slate-50); border: 1px solid var(--slate-200); border-radius: 8px;
      padding: .85rem 1rem; font-size: .8rem; margin-top: .75rem;
    }

    @keyframes slideUp {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    .toast-container { z-index: 1100; }
    #mainToast { min-width: 240px; font-size: .82rem; font-family: 'Inter', sans-serif; }
    .page-end  { height: 5rem; }

    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--slate-300); border-radius: 3px; }

    @media (max-width: 768px) {
      .qa-topbar, .filter-bar, .kpi-section, .section { padding-left: 1rem; padding-right: 1rem; }
      .fab { bottom: 1rem; right: 1rem; }
    }
  </style>
</head>
<body>

<!-- TOP BAR -->
<header class="qa-topbar">
  <div class="topbar-left">
    <div class="topbar-icon"><i class="fa-solid fa-shield-check" style="color:#93c5fd"></i></div>
    <span class="topbar-title">QA Allocation Tool</span>
    <span class="topbar-env">LIVE</span>
  </div>
  <div class="topbar-refresh">
    <i class="fa-regular fa-clock"></i>
    Last refreshed: <span id="refreshTime"></span>
  </div>
</header>

<!-- FILTER BAR -->
<div class="filter-bar">
  <div class="d-flex flex-wrap align-items-end gap-3">
    <div>
      <span class="filter-label">Month</span>
      <select id="f-month" class="form-select" onchange="applyFilters()"><option value="">All Months</option></select>
    </div>
    <div>
      <span class="filter-label">CCL</span>
      <select id="f-ccl" class="form-select" onchange="applyFilters()"><option value="">All CCLs</option></select>
    </div>
    <div>
      <span class="filter-label">Team Leader</span>
      <select id="f-tl" class="form-select" onchange="applyFilters()"><option value="">All Team Leaders</option></select>
    </div>
    <div>
      <span class="filter-label">Colleague</span>
      <select id="f-colleague" class="form-select" onchange="applyFilters()"><option value="">All Colleagues</option></select>
    </div>
    <div>
      <span class="filter-label">Site</span>
      <select id="f-site" class="form-select" onchange="applyFilters()"><option value="">All Sites</option></select>
    </div>
    <div>
      <span class="filter-label">&nbsp;</span>
      <button class="btn btn-sm btn-outline-secondary" style="height:32px;font-size:.78rem;" onclick="clearFilters()">
        <i class="fa-solid fa-xmark me-1"></i>Clear
      </button>
    </div>
    <div class="ms-auto align-self-center">
      <span class="filter-summary" id="filterSummary"></span>
    </div>
  </div>
</div>

<!-- KPI CARDS -->
<div class="kpi-section">
  <div class="row g-3">
    <div class="col-12 col-md-4">
      <div class="kpi-card">
        <div class="kpi-icon blue"><i class="fa-solid fa-clipboard-list"></i></div>
        <div class="kpi-value" id="kpi-required">—</div>
        <div class="kpi-label">Required This Month</div>
        <div class="kpi-sub" id="kpi-sub-req"></div>
        <div class="kpi-progress"><div class="kpi-progress-fill" id="kpi-bar-req" style="width:100%;background:#bfdbfe;"></div></div>
      </div>
    </div>
    <div class="col-12 col-md-4">
      <div class="kpi-card">
        <div class="kpi-icon amber"><i class="fa-solid fa-hourglass-half"></i></div>
        <div class="kpi-value" id="kpi-assigned">—</div>
        <div class="kpi-label">Currently Assigned</div>
        <div class="kpi-sub" id="kpi-sub-asgn"></div>
        <div class="kpi-progress"><div class="kpi-progress-fill" id="kpi-bar-asgn" style="background:#fcd34d;"></div></div>
      </div>
    </div>
    <div class="col-12 col-md-4">
      <div class="kpi-card">
        <div class="kpi-icon green"><i class="fa-solid fa-circle-check"></i></div>
        <div class="kpi-value" id="kpi-completed">—</div>
        <div class="kpi-label">Completed This Month</div>
        <div class="kpi-sub" id="kpi-sub-comp"></div>
        <div class="kpi-progress"><div class="kpi-progress-fill" id="kpi-bar-comp" style="background:#86efac;"></div></div>
      </div>
    </div>
  </div>
</div>

<!-- SECTION 1: COLLEAGUE SUMMARY -->
<div class="section">
  <div class="section-header">
    <div class="section-title">
      <div class="section-icon blue"><i class="fa-solid fa-users"></i></div>
      Colleague Summary
      <span class="count-chip" id="chip-colleagues">0</span>
    </div>
    <button class="btn-export" onclick="exportTable('tbl-colleagues','colleague_summary')">
      <i class="fa-solid fa-download"></i> Export CSV
    </button>
  </div>
  <div class="table-card">
    <div class="table-inner">
      <table id="tbl-colleagues" class="table table-hover w-100">
        <thead><tr>
          <th>Colleague Name</th><th>Colleague ID</th><th>Required Vol</th>
          <th>Completed Vol</th><th>Outstanding Vol</th><th>Completion %</th>
          <th>Contacts (7d)</th><th>Contacts (30d)</th><th>Last Contact Date</th>
        </tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</div>

<!-- SECTION 2: OUTSTANDING -->
<div class="section">
  <div class="section-header">
    <div class="section-title">
      <div class="section-icon amber"><i class="fa-solid fa-hourglass"></i></div>
      Outstanding Contact Details
      <span class="count-chip" id="chip-outstanding">0</span>
    </div>
    <button class="btn-export" onclick="exportTable('tbl-outstanding','outstanding_contacts')">
      <i class="fa-solid fa-download"></i> Export CSV
    </button>
  </div>
  <div class="table-card">
    <div class="table-inner">
      <table id="tbl-outstanding" class="table table-hover w-100">
        <thead><tr>
          <th>Call ID</th><th>Colleague</th><th>Skill</th><th>Line of Business</th>
          <th>Brand</th><th>Transaction</th><th>Priority</th><th>Assigned Date</th>
          <th>Due Date</th><th>AHT (min)</th><th>Vulnerable</th><th>Status</th>
        </tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</div>

<!-- SECTION 3: COMPLETED -->
<div class="section">
  <div class="section-header">
    <div class="section-title">
      <div class="section-icon green"><i class="fa-solid fa-circle-check"></i></div>
      Completed Contact Details
      <span class="count-chip" id="chip-completed">0</span>
    </div>
    <button class="btn-export" onclick="exportTable('tbl-completed','completed_contacts')">
      <i class="fa-solid fa-download"></i> Export CSV
    </button>
  </div>
  <div class="table-card">
    <div class="table-inner">
      <table id="tbl-completed" class="table table-hover w-100">
        <thead><tr>
          <th>Call ID</th><th>Colleague</th><th>Skill</th><th>Line of Business</th>
          <th>Brand</th><th>Transaction</th><th>Priority</th><th>Assigned Date</th>
          <th>Matched Date</th><th>AHT (min)</th><th>Vulnerable</th><th>Status</th>
        </tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</div>

<div class="page-end"></div>

<!-- FAB -->
<button class="fab" onclick="openRequestModal()">
  <i class="fa-solid fa-plus"></i> Request Contact
</button>

<!-- REQUEST CONTACT MODAL -->
<div class="modal fade" id="requestModal" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered" style="max-width:480px;">
    <div class="modal-content">
      <div class="modal-header">
        <div class="modal-title">
          <div class="topbar-icon" style="width:28px;height:28px;border-radius:7px;font-size:.85rem;">
            <i class="fa-solid fa-plus" style="color:#fff"></i>
          </div>
          Request Contact Assignment
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <!-- Step indicator -->
        <div class="steps">
          <div class="step-dot active" id="sd-1">1</div>
          <div class="step-line" id="sl-1"></div>
          <div class="step-dot inactive" id="sd-2">2</div>
          <div class="step-line" id="sl-2"></div>
          <div class="step-dot inactive" id="sd-3">3</div>
        </div>

        <!-- Step 1 -->
        <div id="step-1">
          <p style="font-weight:600;font-size:.88rem;margin-bottom:.25rem;">Select Colleague</p>
          <p class="text-muted mb-3" style="font-size:.78rem;">Which colleague requires an additional or replacement contact?</p>
          <select id="modal-colleague" class="form-select mb-0" onchange="onColleagueChange()">
            <option value="">— Select colleague —</option>
          </select>
          <div id="col-info-panel" class="col-info-panel d-none"></div>
        </div>

        <!-- Step 2 -->
        <div id="step-2" class="d-none">
          <p style="font-weight:600;font-size:.88rem;margin-bottom:.25rem;">Contact Preference</p>
          <p class="text-muted mb-3" style="font-size:.78rem;">Select randomly, or filter by criteria to meet your quota requirements.</p>
          <div class="pref-toggle mb-3">
            <button class="pref-btn active" id="btn-random" onclick="setPref('random')">
              <i class="fa-solid fa-shuffle me-2"></i>Random
            </button>
            <button class="pref-btn" id="btn-pref" onclick="setPref('pref')">
              <i class="fa-solid fa-sliders me-2"></i>By Preference
            </button>
          </div>
          <div id="pref-options" class="d-none">
            <div class="row g-2">
              <div class="col-6">
                <label class="filter-label">Line of Business</label>
                <select id="modal-lob" class="form-select form-select-sm">
                  <option value="">Any</option>
                  <option>CAR</option><option>HOME</option><option>VAN</option>
                </select>
              </div>
              <div class="col-6">
                <label class="filter-label">Brand</label>
                <select id="modal-brand" class="form-select form-select-sm">
                  <option value="">Any</option>
                  <option>HAS</option><option>ADV</option><option>PRE</option>
                </select>
              </div>
              <div class="col-12">
                <label class="filter-label">Skill</label>
                <select id="modal-skill" class="form-select form-select-sm">
                  <option value="">Any skill</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 3 -->
        <div id="step-3" class="d-none">
          <div id="result-container"></div>
        </div>
      </div>

      <div class="modal-footer gap-2">
        <button class="btn btn-sm btn-outline-secondary" data-bs-dismiss="modal" id="btn-cancel">Cancel</button>
        <button class="btn btn-sm btn-outline-secondary d-none" id="btn-back" onclick="modalBack()">
          <i class="fa-solid fa-arrow-left me-1"></i>Back
        </button>
        <button class="btn btn-sm text-white" id="btn-next" onclick="modalNext()" style="background:var(--primary);font-weight:600;">
          Next <i class="fa-solid fa-arrow-right ms-1"></i>
        </button>
        <button class="btn btn-sm text-white d-none" id="btn-assign" onclick="doAssign()" style="background:var(--primary);font-weight:600;">
          <i class="fa-solid fa-plus me-1"></i>Assign Contact
        </button>
        <button class="btn btn-sm btn-success d-none" id="btn-done" data-bs-dismiss="modal">
          Done <i class="fa-solid fa-check ms-1"></i>
        </button>
      </div>
    </div>
  </div>
</div>

<!-- TOAST -->
<div class="toast-container position-fixed bottom-0 end-0 p-3">
  <div id="mainToast" class="toast align-items-center border-0 text-white" role="alert">
    <div class="d-flex">
      <div class="toast-body" id="toastBody"></div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  </div>
</div>

<!-- DATA -->
<script>
const DATA = {
  colleagues: __COLLEAGUES__,
  backlog:    __BACKLOG__,
  pool:       __POOL__
};
</script>

<!-- LIBS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js"></script>

<!-- APP -->
<script>
/* STATE */
let dtColleagues, dtOutstanding, dtCompleted;
let filteredColleagues = [], filteredBacklog = [];
let currentStep = 1, prefMode = 'random';

/* BOOT */
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('refreshTime').textContent =
    new Date().toLocaleString('en-GB', { dateStyle:'medium', timeStyle:'short' });
  populateFilters();
  initTables();
  applyFilters();
  populateModalSkills();
});

/* FILTERS */
function populateFilters() {
  const uniq = (key) => [...new Set(DATA.colleagues.map(r => r[key]).filter(Boolean))].sort();
  fillSelect('f-month',     uniq('Month'));
  fillSelect('f-ccl',       uniq('CCL'));
  fillSelect('f-tl',        uniq('Team_Leader'));
  fillSelect('f-colleague', uniq('Colleague_Name'));
  fillSelect('f-site',      uniq('Site'));
}

function fillSelect(id, values) {
  const sel = document.getElementById(id);
  values.forEach(v => { const o = document.createElement('option'); o.value = v; o.textContent = v; sel.appendChild(o); });
}

function getFilters() {
  return {
    month:     document.getElementById('f-month').value,
    ccl:       document.getElementById('f-ccl').value,
    tl:        document.getElementById('f-tl').value,
    colleague: document.getElementById('f-colleague').value,
    site:      document.getElementById('f-site').value,
  };
}

function applyFilters() {
  const f = getFilters();
  filteredColleagues = DATA.colleagues.filter(r =>
    (!f.month     || r.Month         === f.month) &&
    (!f.ccl       || r.CCL           === f.ccl) &&
    (!f.tl        || r.Team_Leader   === f.tl) &&
    (!f.colleague || r.Colleague_Name === f.colleague) &&
    (!f.site      || r.Site          === f.site)
  );
  const ids = new Set(filteredColleagues.map(r => r.Colleague_ID));
  filteredBacklog = DATA.backlog.filter(r => ids.has(r.COLLEAGUE_ID));
  updateKPIs();
  rebuildTables();
  updateFilterSummary(f);
  populateModalColleagues();
}

function clearFilters() {
  ['f-month','f-ccl','f-tl','f-colleague','f-site'].forEach(id => document.getElementById(id).value = '');
  applyFilters();
}

function updateFilterSummary(f) {
  const n = Object.values(f).filter(Boolean).length;
  document.getElementById('filterSummary').textContent = n
    ? `${n} filter${n>1?'s':''} active \u00b7 ${filteredColleagues.length} colleague${filteredColleagues.length!==1?'s':''} shown`
    : '';
}

/* KPIs */
function updateKPIs() {
  const sum = (key) => filteredColleagues.reduce((s,r) => s + (Number(r[key]) || 0), 0);
  const req  = sum('Number_of_checks_required');
  const comp = sum('COMPLETED');
  const asgn = sum('ASSIGNED');
  document.getElementById('kpi-required').textContent  = req;
  document.getElementById('kpi-assigned').textContent  = asgn;
  document.getElementById('kpi-completed').textContent = comp;
  const compPct = req ? Math.round(comp/req*100) : 0;
  const asgnPct = req ? Math.round(asgn/req*100) : 0;
  document.getElementById('kpi-sub-req').textContent  = filteredColleagues.length + ' colleague' + (filteredColleagues.length!==1?'s':'');
  document.getElementById('kpi-sub-asgn').textContent = asgnPct + '% of required';
  document.getElementById('kpi-sub-comp').textContent = compPct + '% completion rate';
  document.getElementById('kpi-bar-req').style.width  = '100%';
  document.getElementById('kpi-bar-asgn').style.width = asgnPct + '%';
  document.getElementById('kpi-bar-comp').style.width = compPct + '%';
}

/* TABLES */
const DT_OPTS = {
  pageLength: 10,
  dom: '<"row align-items-center mb-2"<"col-auto"l><"col ms-auto"f>>rtip',
  language: { search:'', searchPlaceholder:'Search\u2026', lengthMenu:'Show _MENU_' }
};

function initTables() {
  dtColleagues  = $('#tbl-colleagues').DataTable({ ...DT_OPTS });
  dtOutstanding = $('#tbl-outstanding').DataTable({ ...DT_OPTS, order:[[6,'asc'],[8,'asc']] });
  dtCompleted   = $('#tbl-completed').DataTable({   ...DT_OPTS, order:[[8,'desc']] });
}

function rebuildTables() {
  /* Colleagues */
  dtColleagues.clear();
  filteredColleagues.forEach(r => {
    const pct = r.Completion_Pct || 0;
    const c   = pct >= 80 ? 'g' : pct >= 50 ? 'a' : 'r';
    dtColleagues.row.add([
      `<span class="rag ${c}"></span><span style="font-weight:500">${r.Colleague_Name}</span>`,
      r.Colleague_ID,
      r.Number_of_checks_required,
      r.COMPLETED,
      r.OUTSTANDING,
      `<div class="prog-wrap"><div class="prog-bar"><div class="prog-fill ${c}" style="width:${pct}%"></div></div><span class="prog-pct ${c}">${pct}%</span></div>`,
      r.CONTACTS_LAST_7_DAYS,
      r.CONTACTS_LAST_30_DAYS,
      fmtDate(r.LAST_CONTACT_DATE),
    ]);
  });
  dtColleagues.draw();
  document.getElementById('chip-colleagues').textContent = filteredColleagues.length;

  /* Outstanding */
  const outstanding = filteredBacklog.filter(r => r.STATUS === 'ASSIGNED');
  dtOutstanding.clear();
  outstanding.forEach(r => {
    dtOutstanding.row.add([
      `<code style="font-size:.75rem">${r.CALL_ID}</code>`,
      r.COLLEAGUE_NAME, r.SKILL_NAME,
      lobBadge(r.LINE_OF_BUSINESS), r.BRAND, r.TRANSACTION_TYPE,
      prioBadge(r.PRIORITY),
      fmtDate(r.ASSIGNED_DATE), dueBadge(r.NEXT_ASSIGNMENT_DUE),
      r.CALL_AHT_MINUTE,
      r.VULNERABLE ? '<span class="badge-vuln">V</span>' : '<span style="color:#cbd5e1">&#8212;</span>',
      '<span class="badge-assigned">Assigned</span>',
    ]);
  });
  dtOutstanding.draw();
  document.getElementById('chip-outstanding').textContent = outstanding.length;

  /* Completed */
  const completed = filteredBacklog.filter(r => r.STATUS === 'COMPLETED');
  dtCompleted.clear();
  completed.forEach(r => {
    dtCompleted.row.add([
      `<code style="font-size:.75rem">${r.CALL_ID}</code>`,
      r.COLLEAGUE_NAME, r.SKILL_NAME,
      lobBadge(r.LINE_OF_BUSINESS), r.BRAND, r.TRANSACTION_TYPE,
      prioBadge(r.PRIORITY),
      fmtDate(r.ASSIGNED_DATE), fmtDate(r.MATCHED_DATE),
      r.CALL_AHT_MINUTE,
      r.VULNERABLE ? '<span class="badge-vuln">V</span>' : '<span style="color:#cbd5e1">&#8212;</span>',
      '<span class="badge-completed">Completed</span>',
    ]);
  });
  dtCompleted.draw();
  document.getElementById('chip-completed').textContent = completed.length;
}

/* HELPERS */
function fmtDate(s) {
  if (!s || s === 'null' || s === 'None') return '<span style="color:#cbd5e1">&#8212;</span>';
  try { return new Date(s).toLocaleDateString('en-GB'); } catch(e) { return s; }
}

function prioBadge(p) {
  const labels = {1:'P1',2:'P2',3:'P3'};
  return `<span class="badge-prio prio-${p}">${labels[p]||p}</span>`;
}

function lobBadge(lob) {
  const map = { CAR:'#dbeafe;color:#1e40af', HOME:'#dcfce7;color:#15803d', VAN:'#fef3c7;color:#92400e' };
  const s   = map[lob] || 'var(--slate-100);color:var(--slate-600)';
  const [bg, fg] = s.split(';');
  return `<span style="font-size:.68rem;font-weight:700;padding:.15rem .45rem;border-radius:4px;background:${bg};${fg}">${lob||'&#8212;'}</span>`;
}

function dueBadge(dueStr) {
  if (!dueStr || dueStr === 'null') return '<span style="color:#cbd5e1">&#8212;</span>';
  const today = new Date(); today.setHours(0,0,0,0);
  const due   = new Date(dueStr); due.setHours(0,0,0,0);
  const diff  = Math.round((due - today) / 86400000);
  const label = fmtDate(dueStr);
  if (diff < 0)  return `<span class="due-overdue"><i class="fa-solid fa-circle-exclamation me-1"></i>${label} (${Math.abs(diff)}d overdue)</span>`;
  if (diff <= 3) return `<span class="due-urgent"><i class="fa-solid fa-clock me-1"></i>${label} (${diff}d)</span>`;
  return `<span class="due-ok">${label} <small style="opacity:.6">(${diff}d)</small></span>`;
}

/* EXPORT */
function exportTable(tableId, filename) {
  const map = {'tbl-colleagues':dtColleagues,'tbl-outstanding':dtOutstanding,'tbl-completed':dtCompleted};
  const dt  = map[tableId];
  if (!dt) return;
  const rows = dt.rows({ search:'applied' }).data().toArray();
  if (!rows.length) { showToast('No data to export','warning'); return; }
  const strip = s => String(s).replace(/<[^>]*>/g,'').trim();
  const csv   = rows.map(r => r.map(c => '"'+strip(c).replace(/"/g,'""')+'"').join(',')).join('\n');
  const a     = document.createElement('a');
  a.href      = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
  a.download  = filename + '_' + new Date().toISOString().slice(0,10) + '.csv';
  a.click();
  showToast('Export downloaded successfully','success');
}

/* MODAL */
function populateModalColleagues() {
  const sel = document.getElementById('modal-colleague');
  const val = sel.value;
  sel.innerHTML = '<option value="">&#8212; Select colleague &#8212;</option>';
  filteredColleagues.forEach(c => {
    const o = document.createElement('option');
    o.value = c.Colleague_ID;
    o.textContent = `${c.Colleague_Name}  \u00b7  ${c.OUTSTANDING} outstanding`;
    sel.appendChild(o);
  });
  if (val) sel.value = val;
}

function populateModalSkills() {
  const sel    = document.getElementById('modal-skill');
  const skills = [...new Set(DATA.pool.map(r => r.SKILL_NAME).filter(Boolean))].sort();
  skills.forEach(s => { const o = document.createElement('option'); o.value = s; o.textContent = s; sel.appendChild(o); });
}

function openRequestModal() {
  currentStep = 1; prefMode = 'random';
  document.getElementById('modal-colleague').value = '';
  document.getElementById('col-info-panel').classList.add('d-none');
  document.getElementById('modal-lob').value = '';
  document.getElementById('modal-brand').value = '';
  document.getElementById('modal-skill').value = '';
  document.getElementById('result-container').innerHTML = '';
  setPref('random');
  setStep(1);
  new bootstrap.Modal(document.getElementById('requestModal')).show();
}

function onColleagueChange() {
  const colId = document.getElementById('modal-colleague').value;
  const panel = document.getElementById('col-info-panel');
  if (!colId) { panel.classList.add('d-none'); return; }
  const col = DATA.colleagues.find(c => String(c.Colleague_ID) === String(colId));
  if (!col) return;
  const pct = col.Completion_Pct || 0;
  const clr = pct >= 80 ? 'var(--success)' : pct >= 50 ? 'var(--warning)' : 'var(--danger)';
  panel.classList.remove('d-none');
  panel.innerHTML = `
    <div class="d-flex justify-content-between align-items-start mb-1">
      <span style="font-weight:700">${col.Colleague_Name}</span>
      <span style="font-size:.72rem;color:var(--slate-500)">${col.team_name} \u00b7 ${col.Site}</span>
    </div>
    <div class="d-flex flex-wrap gap-3" style="font-size:.75rem;color:var(--slate-600)">
      <span><i class="fa-solid fa-circle-check me-1" style="color:var(--success)"></i>${col.COMPLETED} completed</span>
      <span><i class="fa-solid fa-hourglass me-1" style="color:var(--warning)"></i>${col.OUTSTANDING} outstanding</span>
      <span><i class="fa-solid fa-clipboard-list me-1" style="color:var(--primary)"></i>${col.Number_of_checks_required} required</span>
      <span style="font-weight:700;color:${clr}">${pct}%</span>
    </div>`;
}

function setPref(mode) {
  prefMode = mode;
  ['random','pref'].forEach(m => document.getElementById('btn-'+m).classList.toggle('active', m===mode));
  document.getElementById('pref-options').classList.toggle('d-none', mode !== 'pref');
}

function setStep(step) {
  currentStep = step;
  [1,2,3].forEach(i => {
    document.getElementById('step-'+i).classList.toggle('d-none', i !== step);
    const dot = document.getElementById('sd-'+i);
    dot.className = 'step-dot ' + (i < step ? 'done' : i === step ? 'active' : 'inactive');
    if (i < 3) document.getElementById('sl-'+i).className = 'step-line' + (i < step ? ' done' : '');
  });
  document.getElementById('btn-cancel').classList.toggle('d-none', step === 3);
  document.getElementById('btn-back').classList.toggle('d-none',   step !== 2);
  document.getElementById('btn-next').classList.toggle('d-none',   step !== 1);
  document.getElementById('btn-assign').classList.toggle('d-none', step !== 2);
  document.getElementById('btn-done').classList.toggle('d-none',   step !== 3);
}

function modalNext() {
  if (!document.getElementById('modal-colleague').value) {
    showToast('Please select a colleague first','warning'); return;
  }
  setStep(2);
}

function modalBack() { if (currentStep > 1) setStep(currentStep - 1); }

function doAssign() {
  const colId = document.getElementById('modal-colleague').value;
  const col   = DATA.colleagues.find(c => String(c.Colleague_ID) === String(colId));
  const lob   = document.getElementById('modal-lob').value;
  const brand = document.getElementById('modal-brand').value;
  const skill = document.getElementById('modal-skill').value;

  let pool = DATA.pool.filter(r => r.STATUS === 'ACTIVE');
  if (prefMode === 'pref') {
    if (lob)   pool = pool.filter(r => r.LINE_OF_BUSINESS === lob);
    if (brand) pool = pool.filter(r => r.BRAND === brand);
    if (skill) pool = pool.filter(r => r.SKILL_NAME === skill);
  }

  const container = document.getElementById('result-container');

  if (!pool.length) {
    const crit = [];
    if (lob)   crit.push(`LoB: <strong>${lob}</strong>`);
    if (brand) crit.push(`Brand: <strong>${brand}</strong>`);
    if (skill) crit.push(`Skill: <strong>${skill}</strong>`);
    container.innerHTML = `
      <div class="result-card result-failure">
        <div class="result-title" style="color:#991b1b">
          <i class="fa-solid fa-circle-xmark" style="color:var(--danger)"></i>No Contacts Available
        </div>
        <p class="result-meta" style="color:#7f1d1d;margin:0">
          No active contacts match your criteria${crit.length?' ('+crit.join(', ')+')'':''}.
          Try broadening your selection or switch to <strong>Random</strong>.
        </p>
      </div>`;
    showToast('No contacts matched the criteria','warning');
  } else {
    const pick = pool[Math.floor(Math.random() * pool.length)];
    container.innerHTML = `
      <div class="result-card result-success">
        <div class="result-title" style="color:#14532d">
          <i class="fa-solid fa-circle-check" style="color:var(--success)"></i>Contact Successfully Assigned
        </div>
        <p class="result-meta" style="color:#166534">
          Assigned to <strong>${col ? col.Colleague_Name : 'colleague'}</strong> for QA review.
          ${pool.length > 1 ? `<span style="opacity:.65">(${pool.length} contacts matched &mdash; selected at random)</span>` : ''}
        </p>
        <div class="detail-grid">
          ${dRow('Contact ID',        pick.CONTACT_ID)}
          ${dRow('Master Contact ID', pick.MASTER_CONTACT_ID)}
          ${dRow('Skill',             pick.SKILL_NAME)}
          ${dRow('Line of Business',  pick.LINE_OF_BUSINESS)}
          ${dRow('Brand',             pick.BRAND)}
          ${dRow('Transaction Type',  pick.TRANSACTION_TYPE)}
          ${dRow('AHT (min)',         pick.CALL_AHT_MINUTE)}
          ${dRow('Vulnerable',        pick.VULNERABLE ? '\u26a0 Yes' : 'No')}
          ${dRow('Call Start',        fmtDate(pick.CALL_START))}
          ${dRow('Policy Number',     pick.POLICY_NUMBER)}
        </div>
      </div>`;
    showToast(`Contact ${pick.CONTACT_ID} assigned to ${col ? col.Colleague_Name : 'colleague'}`, 'success');
  }
  setStep(3);
}

function dRow(label, value) {
  return `<span class="detail-key">${label}</span><span class="detail-val">${value ?? '&#8212;'}</span>`;
}

/* TOAST */
function showToast(msg, type='success') {
  const el  = document.getElementById('mainToast');
  const map = { success:'bg-success', warning:'bg-warning text-dark', danger:'bg-danger' };
  el.className = `toast align-items-center border-0 ${map[type]||'bg-success'} text-white`;
  document.getElementById('toastBody').textContent = msg;
  bootstrap.Toast.getOrCreateInstance(el, { delay:3500 }).show();
}
</script>
</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate QA Allocation Tool HTML")
    parser.add_argument("--out", default=".", help="Output directory (default: current dir)")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading data...")
    base_df, backlog_df, channels_df = load_data()
    print(f"  Colleagues : {len(base_df)}")
    print(f"  Backlog    : {len(backlog_df)}")
    print(f"  Pool       : {len(channels_df)}")

    html = HTML_TEMPLATE
    html = html.replace("__COLLEAGUES__", df_to_json(base_df))
    html = html.replace("__BACKLOG__",    df_to_json(backlog_df))
    html = html.replace("__POOL__",       df_to_json(channels_df))

    out_path = out_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"\nDone  ->  {out_path.resolve()}")
    print("Preview:  python -m http.server 8080  then open http://localhost:8080")


if __name__ == "__main__":
    main()
