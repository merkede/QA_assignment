#!/usr/bin/env python3
"""
streamlit_app.py — QA Allocation Tool (Streamlit / Snowflake edition)

Local dev:   streamlit run streamlit_app.py
Snowflake:   Upload as a Streamlit in Snowflake (SiS) app

Data sources — Snowflake tables (same names as the CSV files):
  QA_ASSIGNMENT_BASE          → Colleague Summary
  QA_COLLEAGUE_CALL_BACKLOG   → Outstanding + Completed contacts
  QA_CONTACT_CHANNELS         → Contact pool for the bot

Local dev with secrets: create .streamlit/secrets.toml
  [snowflake]
  account   = "yourorg-youraccountname"
  user      = "you@example.com"
  password  = "..."
  warehouse = "..."
  database  = "..."
  schema    = "..."
"""

import random
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QA Allocation Tool",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Palette ───────────────────────────────────────────────────────────────────
P  = "#2563eb"; PD = "#1d4ed8"; PL = "#eff6ff"
G  = "#16a34a"; GL = "#f0fdf4"
W  = "#d97706"; WL = "#fffbeb"
R  = "#dc2626"; RL = "#fef2f2"
S0 = "#f8fafc"; S1 = "#f1f5f9"; S2 = "#e2e8f0"; S3 = "#cbd5e1"
S5 = "#64748b"; S6 = "#475569"; S7 = "#334155"; S8 = "#1e293b"; S9 = "#0f172a"

LOB_LIST  = ["CAR", "HOME", "VAN", "BIKE"]
QUOTA_PCT = 0.05
DUE_DAYS  = 3

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
<style>
html,body,[class*="css"]{{font-family:'Inter',sans-serif!important;font-size:12px;}}
#MainMenu{{visibility:hidden;}}footer{{visibility:hidden;}}header{{visibility:hidden;}}
.main .block-container{{padding-top:.5rem!important;padding-bottom:2rem!important;max-width:100%!important;}}
/* Filter labels */
.stSelectbox label{{font-size:.62rem!important;font-weight:800!important;color:{P}!important;text-transform:uppercase;letter-spacing:.07em;}}
.stSelectbox>div>div{{border:1.5px solid {S3}!important;border-radius:6px!important;font-size:.75rem!important;}}
.stSelectbox>div>div:focus-within{{border-color:{P}!important;box-shadow:0 0 0 3px rgba(37,99,235,.15)!important;}}
.stButton>button{{font-size:.7rem!important;font-weight:600!important;border-radius:6px!important;}}
/* Topbar */
.qa-topbar{{background:{S9};color:#fff;padding:0 1.25rem;height:48px;display:flex;align-items:center;
  justify-content:space-between;border-radius:8px;margin-bottom:.5rem;box-shadow:0 1px 5px rgba(0,0,0,.4);}}
.qa-tb-left{{display:flex;align-items:center;gap:.5rem;}}
.qa-tb-icon{{width:28px;height:28px;border-radius:6px;background:{P};display:flex;align-items:center;justify-content:center;font-size:.78rem;}}
.qa-tb-title{{font-size:.88rem;font-weight:700;letter-spacing:-.02em;}}
.qa-tb-env{{background:rgba(37,99,235,.3);border:1px solid rgba(37,99,235,.5);color:#93c5fd;
  font-size:.58rem;font-weight:700;padding:.08rem .35rem;border-radius:3px;letter-spacing:.08em;}}
.qa-tb-right{{font-size:.65rem;color:#94a3b8;}}
/* Fbar */
.fbar-wrap{{background:#fff;border-bottom:2px solid {P};padding:.4rem 0;border-radius:8px 8px 0 0;
  margin-bottom:.1rem;box-shadow:0 2px 8px rgba(37,99,235,.06);}}
/* KPI */
.kcard{{background:#fff;border-radius:8px;padding:.6rem .85rem;border:1px solid {S2};
  display:flex;align-items:center;gap:.65rem;}}
.kico{{width:30px;height:30px;border-radius:7px;display:flex;align-items:center;
  justify-content:center;font-size:.8rem;flex-shrink:0;}}
.kico-b{{background:#dbeafe;color:{P};}} .kico-a{{background:#fef3c7;color:#b45309;}} .kico-g{{background:#dcfce7;color:{G};}}
.kval{{font-size:1.45rem;font-weight:800;line-height:1;color:{S9};}}
.klbl{{font-size:.58rem;font-weight:700;color:{S5};text-transform:uppercase;letter-spacing:.06em;margin-top:.1rem;}}
.ksub{{font-size:.62rem;color:{S5};margin-top:.15rem;}}
.kbar{{height:3px;border-radius:2px;background:{S2};margin-top:.45rem;overflow:hidden;}}
.kbarf{{height:100%;border-radius:2px;}}
/* Quota */
.qbox{{background:#fff;border-radius:8px;padding:.6rem .85rem;border:1px solid {S2};height:100%;}}
.qbox-title{{font-size:.65rem;font-weight:700;color:{S9};display:flex;align-items:center;justify-content:space-between;margin-bottom:.45rem;}}
.qgrid{{display:grid;grid-template-columns:1fr 1fr;gap:.35rem;}}
.qtile{{border-radius:6px;padding:.4rem .5rem;display:flex;flex-direction:column;align-items:flex-start;gap:.12rem;}}
.qtile-name{{font-size:.6rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;}}
.qtile-val{{font-size:.88rem;font-weight:800;line-height:1;}}
.qtile-sub{{font-size:.55rem;font-weight:600;opacity:.8;}}
.qtile-bar{{width:100%;height:3px;border-radius:2px;background:rgba(255,255,255,.35);margin-top:.2rem;overflow:hidden;}}
.qtile-barf{{height:100%;border-radius:2px;background:rgba(255,255,255,.85);}}
.qtile.qg{{background:{G};color:#fff;border:1px solid #15803d;}}
.qtile.qa{{background:{W};color:#fff;border:1px solid #b45309;}}
.qtile.qr{{background:{R};color:#fff;border:1px solid #b91c1c;}}
/* Section */
.sec-title{{font-size:.75rem;font-weight:700;color:{S9};display:flex;align-items:center;
  gap:.35rem;margin:.5rem 0 .3rem;}}
.sico{{width:20px;height:20px;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:.65rem;}}
.sico-b{{background:#dbeafe;color:{P};}} .sico-a{{background:#fef3c7;color:#b45309;}} .sico-g{{background:#dcfce7;color:{G};}}
.chip{{background:{S1};color:{S5};border:1px solid {S2};font-size:.58rem;font-weight:700;padding:.08rem .4rem;border-radius:999px;}}
.pill{{display:inline-flex;align-items:center;gap:.2rem;background:{PL};border:1px solid rgba(37,99,235,.35);
  color:{P};font-size:.63rem;font-weight:700;padding:.1rem .45rem;border-radius:999px;margin-right:.2rem;}}
/* Expiry */
.expiry-banner{{background:{R};color:#fff;border-radius:8px;padding:.45rem 1rem;font-size:.72rem;
  font-weight:700;display:flex;align-items:center;gap:.5rem;box-shadow:0 4px 16px rgba(220,38,38,.4);margin:.35rem 0;}}
.expiry-badge{{background:rgba(255,255,255,.25);border-radius:999px;padding:.05rem .4rem;font-size:.7rem;font-weight:800;}}
/* Bot chat bubbles */
.chat-bot{{background:#fff;border:1px solid {S2};border-radius:3px 10px 10px 10px;
  padding:.45rem .65rem;max-width:84%;font-size:.72rem;line-height:1.45;color:{S8};margin:.2rem 0;}}
.chat-usr{{background:{P};color:#fff;border-radius:10px 3px 10px 10px;
  padding:.42rem .65rem;max-width:75%;font-size:.72rem;line-height:1.45;
  margin:.2rem 0 .2rem auto;text-align:right;}}
/* Result cards */
.res-ok{{background:{GL};border:1px solid #bbf7d0;border-radius:8px;padding:.65rem;font-size:.72rem;}}
.res-warn{{background:{WL};border:1px solid #fde68a;border-radius:8px;padding:.65rem;font-size:.72rem;}}
.res-err{{background:{RL};border:1px solid #fecaca;border-radius:8px;padding:.65rem;font-size:.72rem;}}
.dgrid{{display:grid;grid-template-columns:auto 1fr;gap:.2rem .55rem;font-size:.67rem;margin-top:.4rem;}}
.dk{{font-weight:600;color:{S5};white-space:nowrap;}} .dv{{color:{S8};font-weight:500;}}
[data-testid="stDataFrame"]{{border-radius:8px!important;border:1px solid {S2}!important;}}
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ────────────────────────────────────────────────────
def _ss(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

_ss("f_month", ""); _ss("f_ccl", ""); _ss("f_tl", "")
_ss("f_colleague", ""); _ss("f_site", "")
_ss("bot_step", "idle")   # idle | colleague | mode | prefs | assign | done
_ss("bot_col", None)      # selected colleague row dict
_ss("bot_mode", "random") # random | pref
_ss("bot_lob", ""); _ss("bot_brand", ""); _ss("bot_skill", "")
_ss("bot_msgs", [])       # [{role: bot|user, text: str}]
_ss("bot_pick", None)     # assigned contact row dict
_ss("bot_fallback", None)  # (pool_df, label) fallback result


def _make_demo():
    random.seed(42)
    TODAY = date(2026, 3, 5)
    TEAMS = {
        "HD RTL K": {"tl": "Katy Brown",   "ccl": "Mark Evans",  "site": "London"},
        "HD RTL M": {"tl": "James Clarke",  "ccl": "Mark Evans",  "site": "London"},
        "HD RTL P": {"tl": "Sarah Mills",   "ccl": "Lisa Webb",   "site": "Leeds"},
        "HD RTL Q": {"tl": "David Jones",   "ccl": "Lisa Webb",   "site": "Leeds"},
        "HD RTL A": {"tl": "Emma Wilson",   "ccl": "Paul Knight", "site": "London"},
    }
    SKILLS = ["HD RTL CUSTOMER","HD CLM CUSTOMER","HD RTL ESCALATIONS",
              "CANCELLATION CS","NEW BUSINESS CS","RETENTION CS"]
    BRANDS = ["HAS","ADV","PRE"]
    TXN    = ["MTA","NB","REN","CAN","ENQ","ESC"]
    NAMES  = ["Alice Thompson","Ben Carter","Clara Davis","Dan Evans","Eva Foster",
              "Frank Green","Grace Hill","Harry Irving","Isla Jones","Jack King",
              "Karen Lee","Liam Moore","Mia Norton","Noah Owen","Olivia Park",
              "Peter Quinn","Quinn Reed","Rachel Scott","Sam Turner","Tara Underwood"]
    tkeys = list(TEAMS.keys())
    p = random.choice; r = random.randint

    cols = []
    for i, name in enumerate(NAMES):
        t = tkeys[i % len(tkeys)]; td = TEAMS[t]
        req = p([2,3,4,5,6]); comp = r(0, req); out = req - comp
        cols.append({"WkComDate":"2026-03-02","Year":2026,"Month":"2026-03-01",
            "Colleague_Name":name,"Colleague_ID":200000+i*1337,
            "Agent_EmployeeNumber":500000000+i*12345,"Working_Days":5,
            "Number_of_checks_required":req,"Team_Leader":td["tl"],
            "team_name":t,"CCL":td["ccl"],"Site":td["site"],
            "ASSIGNED":out,"COMPLETED":comp,"OUTSTANDING":out,
            "CONTACTS_LAST_7_DAYS":r(20,150),"CONTACTS_LAST_30_DAYS":r(80,400),
            "LAST_CONTACT_DATE":(TODAY-timedelta(days=r(0,4))).isoformat(),
            "Completion_Pct":round(comp/req*100,1) if req else 0})

    bl = []; cid = 5_000_000_000
    for col in cols:
        for _ in range(col["ASSIGNED"]):
            bl.append({"ID":len(bl)+1,"EMPLOYEE_ID":col["Agent_EmployeeNumber"],
                "CALL_ID":cid+len(bl),"COLLEAGUE_NAME":col["Colleague_Name"],
                "COLLEAGUE_ID":col["Colleague_ID"],"TEAM":col["team_name"],
                "TEAM_LEADER":col["Team_Leader"],"CCL":col["CCL"],"SITE":col["Site"],
                "ASSIGNED_DATE":(TODAY-timedelta(days=r(0,3))).isoformat(),
                "PRIORITY":p([1,1,1,2,2,3]),"STATUS":"ASSIGNED","MATCHED_DATE":None,
                "NEXT_ASSIGNMENT_DUE":None,"SKILL_NAME":p(SKILLS),"TRANSACTION":r(1,3),
                "VULNERABLE":p([0,0,0,0,1]),"TRANSACTION_TYPE":p(TXN),
                "POLICY_NUMBER":r(100000,999999),"LINE_OF_BUSINESS":p(LOB_LIST),
                "BRAND":p(BRANDS),"CALL_AHT_MINUTE":r(3,45)})
        for _ in range(col["COMPLETED"]):
            bl.append({"ID":len(bl)+1,"EMPLOYEE_ID":col["Agent_EmployeeNumber"],
                "CALL_ID":cid+len(bl),"COLLEAGUE_NAME":col["Colleague_Name"],
                "COLLEAGUE_ID":col["Colleague_ID"],"TEAM":col["team_name"],
                "TEAM_LEADER":col["Team_Leader"],"CCL":col["CCL"],"SITE":col["Site"],
                "ASSIGNED_DATE":(TODAY-timedelta(days=r(7,30))).isoformat(),
                "PRIORITY":p([1,1,2,3]),"STATUS":"COMPLETED",
                "MATCHED_DATE":(TODAY-timedelta(days=r(0,6))).isoformat(),
                "NEXT_ASSIGNMENT_DUE":None,"SKILL_NAME":p(SKILLS),"TRANSACTION":r(1,3),
                "VULNERABLE":p([0,0,0,0,1]),"TRANSACTION_TYPE":p(TXN),
                "POLICY_NUMBER":r(100000,999999),"LINE_OF_BUSINESS":p(LOB_LIST),
                "BRAND":p(BRANDS),"CALL_AHT_MINUTE":r(3,45)})

    start = datetime(2026, 1, 1)
    pool = []
    for i in range(500):
        cs = start + timedelta(hours=r(0,24*60), minutes=r(0,59))
        ce = cs + timedelta(minutes=r(3,45))
        col = cols[i % len(cols)]
        pool.append({"MASTER_CONTACT_ID":30_000_000+i,"CONTACT_ID":3_000_000+i,
            "USER_EMPLOYEEID":col["Agent_EmployeeNumber"],"COLLEAGUE_NAME":col["Colleague_Name"],
            "CALL_START":cs.isoformat(),"CALL_END":ce.isoformat(),
            "CALL_AHT_MINUTE":(ce-cs).seconds//60,"SKILL_NAME":p(SKILLS),
            "TRANSACTION_TYPE":p(TXN),"TEAM_LEADER":col["Team_Leader"],
            "CCL":col["CCL"],"SITE":col["Site"],"TENURE":r(100,2000),
            "VULNERABLE":p([0,0,0,0,1]),"POLICY_NUMBER":r(100000,999999),
            "BRAND":p(BRANDS),"STATUS":"ACTIVE","LINE_OF_BUSINESS":p(LOB_LIST)})

    return pd.DataFrame(cols), pd.DataFrame(bl), pd.DataFrame(pool)


@st.cache_data(ttl=300)
def load_data():
    """Try SiS → local connector → synthetic demo, in that order."""
    try:
        from snowflake.snowpark.context import get_active_session
        sess = get_active_session()
        df_col  = sess.sql("SELECT * FROM QA_ASSIGNMENT_BASE").to_pandas()
        df_back = sess.sql("SELECT * FROM QA_COLLEAGUE_CALL_BACKLOG").to_pandas()
        df_pool = sess.sql("SELECT * FROM QA_CONTACT_CHANNELS").to_pandas()
        return df_col, df_back, df_pool, "Snowflake (SiS)"
    except Exception:
        pass
    try:
        import snowflake.connector
        c = st.secrets["snowflake"]
        conn = snowflake.connector.connect(
            account=c["account"], user=c["user"], password=c["password"],
            warehouse=c.get("warehouse",""), database=c.get("database",""),
            schema=c.get("schema","PUBLIC"),
        )
        def q(sql): return pd.read_sql(sql, conn)
        df_col  = q("SELECT * FROM QA_ASSIGNMENT_BASE")
        df_back = q("SELECT * FROM QA_COLLEAGUE_CALL_BACKLOG")
        df_pool = q("SELECT * FROM QA_CONTACT_CHANNELS")
        conn.close()
        return df_col, df_back, df_pool, "Snowflake (connector)"
    except Exception:
        pass
    df_col, df_back, df_pool = _make_demo()
    return df_col, df_back, df_pool, "Demo data"


# ── Normalise raw data ────────────────────────────────────────────────────────
def _prep(df_col, df_back, df_pool, source):
    # Colleagues
    df_col.columns = [c.strip() for c in df_col.columns]
    req  = pd.to_numeric(df_col.get("Number_of_checks_required", 0), errors="coerce").fillna(0)
    comp = pd.to_numeric(df_col.get("COMPLETED", 0), errors="coerce").fillna(0)
    if "ASSIGNED"    not in df_col.columns: df_col["ASSIGNED"]    = (req - comp).astype(int)
    if "OUTSTANDING" not in df_col.columns: df_col["OUTSTANDING"] = (req - comp).astype(int)
    df_col["Completion_Pct"] = (comp / req.replace(0, float("nan")) * 100).round(1).fillna(0)
    # Backlog
    df_back.columns = [c.upper().strip() for c in df_back.columns]
    # Pool
    df_pool.columns = [c.upper().strip() for c in df_pool.columns]
    return df_col, df_back, df_pool, source


df_col, df_back, df_pool, source = _prep(*load_data())


# ── Helpers ───────────────────────────────────────────────────────────────────
def _opts(df, col):
    if col not in df.columns: return []
    return sorted(df[col].dropna().astype(str).unique().tolist())

def _rag(pct):
    if pct >= 80: return "🟢"
    if pct >= 50: return "🟡"
    return "🔴"

def _pri_label(p):
    try: p = int(float(p))
    except Exception: return str(p)
    return {1:"🔴 P1", 2:"🟠 P2", 3:"⚪ P3"}.get(p, f"P{p}")

def _due_label(assigned_date_str):
    if not assigned_date_str or pd.isna(assigned_date_str): return "-"
    try:
        a = pd.to_datetime(assigned_date_str).date()
        due = a + timedelta(days=DUE_DAYS)
        diff = (due - date.today()).days
        lbl = due.strftime("%d/%m/%Y")
        if diff <= 0: return f"🔴 {lbl} (today)"
        if diff == 1: return f"🔴 {lbl} (tomorrow)"
        if diff <= 2: return f"🟠 {lbl} ({diff}d)"
        return f"🟢 {lbl} ({diff}d)"
    except Exception: return str(assigned_date_str)

def _fmt_date(s):
    if not s or pd.isna(s): return "-"
    try: return pd.to_datetime(s).strftime("%d/%m/%Y")
    except Exception: return str(s)


# ═════════════════════════════════════════════════════════════════════════════
# TOP BAR
# ═════════════════════════════════════════════════════════════════════════════
now_str = datetime.now().strftime("%d %b %Y, %H:%M")
st.markdown(f"""
<div class="qa-topbar">
  <div class="qa-tb-left">
    <div class="qa-tb-icon"><i class="fa-solid fa-shield-check" style="color:#93c5fd"></i></div>
    <span class="qa-tb-title">QA Allocation Tool</span>
    <span class="qa-tb-env">LIVE</span>
    <span style="font-size:.55rem;color:{S5};margin-left:.4rem">({source})</span>
  </div>
  <div class="qa-tb-right"><i class="fa-regular fa-clock"></i>&nbsp;Refreshed: {now_str}</div>
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# FILTER BAR
# ═════════════════════════════════════════════════════════════════════════════
fc1, fc2, fc3, fc4, fc5, fc6 = st.columns([1.1, 0.9, 1.4, 1.5, 0.9, 0.5])

def _sel(col, label, key, field, df=df_col):
    opts = [""] + _opts(df, field)
    cur = st.session_state[key]
    idx = opts.index(cur) if cur in opts else 0
    return col.selectbox(label, opts, index=idx, key=f"_sel_{key}")

with fc1: st.session_state.f_month    = _sel(fc1, "Month",       "f_month",    "Month")
with fc2: st.session_state.f_ccl      = _sel(fc2, "CCL",         "f_ccl",      "CCL")
with fc3: st.session_state.f_tl       = _sel(fc3, "Team Leader", "f_tl",       "Team_Leader")
with fc4: st.session_state.f_colleague= _sel(fc4, "Colleague",   "f_colleague","Colleague_Name")
with fc5: st.session_state.f_site     = _sel(fc5, "Site",        "f_site",     "Site")
with fc6:
    st.markdown("<div style='height:1.55rem'></div>", unsafe_allow_html=True)
    if st.button("✕ Clear", key="btn_clear"):
        for k in ("f_month","f_ccl","f_tl","f_colleague","f_site"):
            st.session_state[k] = ""
        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# APPLY FILTERS
# ═════════════════════════════════════════════════════════════════════════════
fc = df_col.copy()
if st.session_state.f_month     and "Month"         in fc.columns: fc = fc[fc["Month"]         == st.session_state.f_month]
if st.session_state.f_ccl       and "CCL"           in fc.columns: fc = fc[fc["CCL"]           == st.session_state.f_ccl]
if st.session_state.f_tl        and "Team_Leader"   in fc.columns: fc = fc[fc["Team_Leader"]   == st.session_state.f_tl]
if st.session_state.f_colleague and "Colleague_Name" in fc.columns: fc = fc[fc["Colleague_Name"] == st.session_state.f_colleague]
if st.session_state.f_site      and "Site"          in fc.columns: fc = fc[fc["Site"]          == st.session_state.f_site]

col_ids = set(fc["Colleague_ID"].tolist()) if "Colleague_ID" in fc.columns else set()
fb = df_back[df_back["COLLEAGUE_ID"].isin(col_ids)] if "COLLEAGUE_ID" in df_back.columns else df_back.copy()

# Active pills
active = {"Month": st.session_state.f_month, "CCL": st.session_state.f_ccl,
          "Team Leader": st.session_state.f_tl, "Colleague": st.session_state.f_colleague,
          "Site": st.session_state.f_site}
pills = "".join(f'<span class="pill">{k}: <strong>{v}</strong></span>' for k, v in active.items() if v)
if pills:
    fsum = f"&nbsp;&nbsp;<span style='font-size:.68rem;color:{S6};font-weight:600'>{len(fc)} of {len(df_col)} colleagues</span>"
    st.markdown(f"<div style='margin:.2rem 0 .35rem'>{pills}{fsum}</div>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# EXPIRY NOTIFICATION
# ═════════════════════════════════════════════════════════════════════════════
fb_asgn = fb[fb["STATUS"] == "ASSIGNED"] if "STATUS" in fb.columns else pd.DataFrame()
if not fb_asgn.empty and "ASSIGNED_DATE" in fb_asgn.columns:
    def _is_expiring(d):
        try: return ((pd.to_datetime(d).date() + timedelta(days=DUE_DAYS)) - date.today()).days <= 1
        except Exception: return False
    n_exp = int(fb_asgn["ASSIGNED_DATE"].apply(_is_expiring).sum())
    if n_exp > 0:
        st.markdown(f"""
        <div class="expiry-banner">
          <i class="fa-solid fa-triangle-exclamation"></i>
          QA Check Due &mdash; Shortly Expiring
          <span class="expiry-badge">{n_exp}</span>
          <span style="font-size:.65rem;opacity:.8;margin-left:.35rem">&#x2193; See Outstanding Contacts below</span>
        </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# KPIs + LOB QUAD
# ═════════════════════════════════════════════════════════════════════════════
def _num(df, col): return int(pd.to_numeric(df.get(col, pd.Series(dtype=float)), errors="coerce").fillna(0).sum())

req_t  = _num(fc, "Number_of_checks_required")
comp_t = _num(fc, "COMPLETED")
asgn_t = _num(fc, "ASSIGNED")
cp = round(comp_t / req_t * 100) if req_t else 0
ap = round(asgn_t / req_t * 100) if req_t else 0

def _kpi(icon, ico_cls, val, lbl, sub, bar_pct, bar_clr):
    return f"""<div class="kcard">
  <div class="kico kico-{ico_cls}"><i class="fa-solid fa-{icon}"></i></div>
  <div style="flex:1;min-width:0">
    <div class="kval">{val}</div><div class="klbl">{lbl}</div>
    <div class="ksub">{sub}</div>
    <div class="kbar"><div class="kbarf" style="width:{min(bar_pct,100)}%;background:{bar_clr}"></div></div>
  </div></div>"""

def _lob_quad():
    tiles = ""
    for lob in LOB_LIST:
        total    = int((df_pool["LINE_OF_BUSINESS"] == lob).sum()) if "LINE_OF_BUSINESS" in df_pool.columns else 1
        target   = max(1, int(total * QUOTA_PCT + 0.9999))
        achieved = int(((fb["LINE_OF_BUSINESS"] == lob) & (fb["STATUS"] == "COMPLETED")).sum()) \
                   if not fb.empty and "LINE_OF_BUSINESS" in fb.columns and "STATUS" in fb.columns else 0
        pct = min(100, round(achieved / target * 100))
        cls = "qg" if pct >= 80 else ("qa" if pct >= 50 else "qr")
        tiles += f"""<div class="qtile {cls}">
          <span class="qtile-name">{lob}</span>
          <span class="qtile-val">{pct}%</span>
          <span class="qtile-sub">{achieved} / {target} checks</span>
          <div class="qtile-bar"><div class="qtile-barf" style="width:{pct}%"></div></div>
        </div>"""
    return f"""<div class="qbox">
      <div class="qbox-title">
        <span><i class="fa-solid fa-chart-pie" style="color:{P};margin-right:.3rem"></i>Line of Business Coverage</span>
        <span style="font-size:.58rem;color:{S5};font-weight:600">Target: 5%</span>
      </div>
      <div class="qgrid">{tiles}</div>
    </div>"""

k1, k2, k3, k4 = st.columns([1, 1, 1, 1.35])
k1.markdown(_kpi("clipboard-list","b", req_t,  "Required",  f"{len(fc)} colleague{'s' if len(fc)!=1 else ''}", 100, "#bfdbfe"), unsafe_allow_html=True)
k2.markdown(_kpi("hourglass-half","a", asgn_t, "Assigned",  f"{ap}% of target", ap, "#fcd34d"), unsafe_allow_html=True)
k3.markdown(_kpi("circle-check",  "g", comp_t, "Completed", f"{cp}% completion",cp, "#86efac"), unsafe_allow_html=True)
k4.markdown(_lob_quad(), unsafe_allow_html=True)
st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TABLE HELPER: click-to-filter
# ═════════════════════════════════════════════════════════════════════════════
def _click_filter(sel_event, name_col, table_key):
    """If a row is selected, show a filter button."""
    if sel_event and hasattr(sel_event, "selection") and sel_event.selection.rows:
        row_idx = sel_event.selection.rows[0]
        name = sel_event.selection.rows  # avoid using unstable index
        # safer: get from the displayed df passed in
        return row_idx
    return None


# ═════════════════════════════════════════════════════════════════════════════
# COLLEAGUE SUMMARY
# ═════════════════════════════════════════════════════════════════════════════
st.markdown(f"""<div class="sec-title">
  <div class="sico sico-b"><i class="fa-solid fa-users"></i></div>
  Colleague Summary <span class="chip">{len(fc)}</span>
</div>""", unsafe_allow_html=True)

if not fc.empty:
    disp_col = pd.DataFrame({
        "Colleague":    fc.get("Colleague_Name", pd.Series(dtype=str)).values,
        "Team":         fc.get("team_name",      pd.Series(dtype=str)).values,
        "Required":     pd.to_numeric(fc.get("Number_of_checks_required",0), errors="coerce").fillna(0).astype(int).values,
        "Completed":    pd.to_numeric(fc.get("COMPLETED",  0), errors="coerce").fillna(0).astype(int).values,
        "Outstanding":  pd.to_numeric(fc.get("OUTSTANDING",0), errors="coerce").fillna(0).astype(int).values,
        "Completion %": fc.get("Completion_Pct",0).apply(lambda p: f"{_rag(p)} {p}%").values,
        "7d Contacts":  pd.to_numeric(fc.get("CONTACTS_LAST_7_DAYS",  0), errors="coerce").fillna(0).astype(int).values,
        "30d Contacts": pd.to_numeric(fc.get("CONTACTS_LAST_30_DAYS", 0), errors="coerce").fillna(0).astype(int).values,
        "Last Contact": fc.get("LAST_CONTACT_DATE", pd.Series(dtype=str)).apply(_fmt_date).values,
    })
    sel_col = st.dataframe(disp_col, height=220, use_container_width=True,
                           hide_index=True, on_select="rerun",
                           selection_mode="single-row", key="tbl_col")
    if sel_col.selection.rows:
        clicked = disp_col.iloc[sel_col.selection.rows[0]]["Colleague"]
        if st.button(f"🔍 Filter by colleague: {clicked}", key="btn_col_f"):
            st.session_state.f_colleague = clicked
            st.rerun()
else:
    st.info("No colleagues match the current filters.")


# ═════════════════════════════════════════════════════════════════════════════
# OUTSTANDING CONTACTS
# ═════════════════════════════════════════════════════════════════════════════
fb_out = fb[fb["STATUS"] == "ASSIGNED"].copy() if "STATUS" in fb.columns else pd.DataFrame()
st.markdown(f"""<div class="sec-title">
  <div class="sico sico-a"><i class="fa-solid fa-hourglass"></i></div>
  Outstanding Contact Details <span class="chip">{len(fb_out)}</span>
</div>""", unsafe_allow_html=True)

if not fb_out.empty:
    disp_out = pd.DataFrame({
        "Call ID":    fb_out.get("CALL_ID", pd.Series(dtype=str)).values,
        "Colleague":  fb_out.get("COLLEAGUE_NAME", pd.Series(dtype=str)).values,
        "Skill":      fb_out.get("SKILL_NAME",     pd.Series(dtype=str)).values,
        "LoB":        fb_out.get("LINE_OF_BUSINESS",pd.Series(dtype=str)).values,
        "Brand":      fb_out.get("BRAND",           pd.Series(dtype=str)).values,
        "Transaction":fb_out.get("TRANSACTION_TYPE",pd.Series(dtype=str)).values,
        "Priority":   fb_out.get("PRIORITY", pd.Series(dtype=str)).apply(_pri_label).values,
        "Assigned":   fb_out.get("ASSIGNED_DATE",  pd.Series(dtype=str)).apply(_fmt_date).values,
        "Due":        fb_out.get("ASSIGNED_DATE",  pd.Series(dtype=str)).apply(_due_label).values,
        "AHT":        fb_out.get("CALL_AHT_MINUTE",pd.Series(dtype=str)).astype(str).str.cat(["m"]*len(fb_out)).values,
        "Vuln":       fb_out.get("VULNERABLE", pd.Series(dtype=int)).apply(lambda v: "⚠️ V" if v else "-").values,
    })
    sel_out = st.dataframe(disp_out, height=220, use_container_width=True,
                           hide_index=True, on_select="rerun",
                           selection_mode="single-row", key="tbl_out")
    if sel_out.selection.rows:
        clicked = disp_out.iloc[sel_out.selection.rows[0]]["Colleague"]
        if st.button(f"🔍 Filter by colleague: {clicked}", key="btn_out_f"):
            st.session_state.f_colleague = clicked
            st.rerun()
else:
    st.info("No outstanding contacts for current filters.")


# ═════════════════════════════════════════════════════════════════════════════
# COMPLETED CONTACTS
# ═════════════════════════════════════════════════════════════════════════════
fb_comp = fb[fb["STATUS"] == "COMPLETED"].copy() if "STATUS" in fb.columns else pd.DataFrame()
st.markdown(f"""<div class="sec-title">
  <div class="sico sico-g"><i class="fa-solid fa-circle-check"></i></div>
  Completed Contact Details <span class="chip">{len(fb_comp)}</span>
</div>""", unsafe_allow_html=True)

if not fb_comp.empty:
    disp_comp = pd.DataFrame({
        "Call ID":    fb_comp.get("CALL_ID",          pd.Series(dtype=str)).values,
        "Colleague":  fb_comp.get("COLLEAGUE_NAME",   pd.Series(dtype=str)).values,
        "Skill":      fb_comp.get("SKILL_NAME",       pd.Series(dtype=str)).values,
        "LoB":        fb_comp.get("LINE_OF_BUSINESS", pd.Series(dtype=str)).values,
        "Brand":      fb_comp.get("BRAND",            pd.Series(dtype=str)).values,
        "Transaction":fb_comp.get("TRANSACTION_TYPE", pd.Series(dtype=str)).values,
        "Priority":   fb_comp.get("PRIORITY", pd.Series(dtype=str)).apply(_pri_label).values,
        "Assigned":   fb_comp.get("ASSIGNED_DATE",    pd.Series(dtype=str)).apply(_fmt_date).values,
        "Matched":    fb_comp.get("MATCHED_DATE",     pd.Series(dtype=str)).apply(_fmt_date).values,
        "AHT":        fb_comp.get("CALL_AHT_MINUTE",  pd.Series(dtype=str)).astype(str).str.cat(["m"]*len(fb_comp)).values,
        "Vuln":       fb_comp.get("VULNERABLE", pd.Series(dtype=int)).apply(lambda v: "⚠️ V" if v else "-").values,
        "Status":     ["✅ Completed"] * len(fb_comp),
    })
    sel_comp = st.dataframe(disp_comp, height=220, use_container_width=True,
                            hide_index=True, on_select="rerun",
                            selection_mode="single-row", key="tbl_comp")
    if sel_comp.selection.rows:
        clicked = disp_comp.iloc[sel_comp.selection.rows[0]]["Colleague"]
        if st.button(f"🔍 Filter by colleague: {clicked}", key="btn_comp_f"):
            st.session_state.f_colleague = clicked
            st.rerun()
else:
    st.info("No completed contacts for current filters.")


# ═════════════════════════════════════════════════════════════════════════════
# REQUEST CONTACT — CONVERSATIONAL BOT
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("<hr style='margin:1rem 0;border-color:#e2e8f0'>", unsafe_allow_html=True)

with st.expander("🤖  Request Contact — QA Assistant", expanded=False):

    # Render conversation history
    for msg in st.session_state.bot_msgs:
        cls = "chat-bot" if msg["role"] == "bot" else "chat-usr"
        prefix = "🤖 " if msg["role"] == "bot" else ""
        st.markdown(f'<div class="{cls}">{prefix}{msg["text"]}</div>', unsafe_allow_html=True)

    def _bot(text):  st.session_state.bot_msgs.append({"role":"bot",  "text": text})
    def _usr(text):  st.session_state.bot_msgs.append({"role":"user", "text": text})

    step = st.session_state.bot_step

    # ── Idle: start button ────────────────────────────────────────────────
    if step == "idle":
        if st.button("▶ Start new assignment", key="bot_start"):
            st.session_state.bot_msgs = []
            st.session_state.bot_step = "colleague"
            _bot("Hi! I can help assign a new QA contact. Who would you like to assign one to?")
            st.rerun()

    # ── Select colleague ──────────────────────────────────────────────────
    elif step == "colleague":
        col_names = fc["Colleague_Name"].tolist() if "Colleague_Name" in fc.columns and not fc.empty else []
        sel = st.selectbox("Select colleague", [""] + col_names, key="bot_col_sel")
        if st.button("Continue →", key="bot_col_go"):
            if not sel:
                st.warning("Please select a colleague.")
            else:
                _usr(sel)
                row = fc[fc["Colleague_Name"] == sel].iloc[0]
                st.session_state.bot_col = row.to_dict()
                p = float(row.get("Completion_Pct", 0))
                comp = int(row.get("COMPLETED", 0)); req = int(row.get("Number_of_checks_required", 0))
                lob_parts = []
                cid = row.get("Colleague_ID")
                for lob in LOB_LIST:
                    done = 0
                    if not fb.empty and "COLLEAGUE_ID" in fb.columns and "STATUS" in fb.columns and "LINE_OF_BUSINESS" in fb.columns:
                        done = int(((fb["COLLEAGUE_ID"] == cid) & (fb["STATUS"] == "COMPLETED") & (fb["LINE_OF_BUSINESS"] == lob)).sum())
                    if done > 0: lob_parts.append(f"{lob}: {done}")
                lob_str = ", ".join(lob_parts) or "none yet"
                _bot(f"**{sel}** — {comp}/{req} completed ({_rag(p)} {p}%). LoB breakdown: {lob_str}.")
                _bot("How would you like me to select a contact?")
                st.session_state.bot_step = "mode"
                st.rerun()

    # ── Select mode ───────────────────────────────────────────────────────
    elif step == "mode":
        m1, m2 = st.columns(2)
        with m1:
            if st.button("🔀 Random", key="bot_rand"):
                _usr("Random contact")
                _bot("On it — picking a random contact from the pool...")
                st.session_state.bot_mode = "random"
                st.session_state.bot_step = "assign"
                st.rerun()
        with m2:
            if st.button("🎛 By preference", key="bot_pref_btn"):
                _usr("I have a preference")
                _bot("Sure! Tell me what you need. Leave blank to match anything.")
                st.session_state.bot_mode = "pref"
                st.session_state.bot_step = "prefs"
                st.rerun()

    # ── Select preferences ────────────────────────────────────────────────
    elif step == "prefs":
        skills = _opts(df_pool, "SKILL_NAME"); brands = _opts(df_pool, "BRAND")
        p1, p2 = st.columns(2)
        with p1:
            st.session_state.bot_lob   = st.selectbox("Line of Business", [""] + LOB_LIST, key="pref_lob")
            st.session_state.bot_brand = st.selectbox("Brand",            [""] + brands,   key="pref_brand")
        with p2:
            st.session_state.bot_skill = st.selectbox("Skill",            [""] + skills,   key="pref_skill")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🔍 Search", key="bot_search"):
                parts = [x for x in [st.session_state.bot_lob, st.session_state.bot_brand, st.session_state.bot_skill] if x]
                _usr(" + ".join(parts) if parts else "Any")
                _bot(f"Searching{' for ' + ', '.join(parts) if parts else ''}...")
                st.session_state.bot_step = "assign"
                st.rerun()
        with b2:
            if st.button("🔀 Just random", key="bot_rand2"):
                _usr("Just random")
                st.session_state.bot_mode = "random"
                st.session_state.bot_step = "assign"
                st.rerun()

    # ── Assign ────────────────────────────────────────────────────────────
    elif step == "assign":
        pool = df_pool[df_pool["STATUS"] == "ACTIVE"].copy() if "STATUS" in df_pool.columns else df_pool.copy()
        lo = st.session_state.bot_lob
        br = st.session_state.bot_brand
        sk = st.session_state.bot_skill
        if st.session_state.bot_mode == "pref":
            if lo and "LINE_OF_BUSINESS" in pool.columns: pool = pool[pool["LINE_OF_BUSINESS"] == lo]
            if br and "BRAND"            in pool.columns: pool = pool[pool["BRAND"]            == br]
            if sk and "SKILL_NAME"       in pool.columns: pool = pool[pool["SKILL_NAME"]       == sk]

        col_name = (st.session_state.bot_col or {}).get("Colleague_Name", "?")

        if not pool.empty:
            pick = pool.sample(1).iloc[0]
            n = len(pool)
            _bot(f"Done ({n} matched)! Assigning to **{col_name}**:")
            st.markdown(f"""<div class="res-ok">
              <strong style="color:#14532d">✅ Contact Assigned</strong>
              <div class="dgrid">
                <span class="dk">ID</span>          <span class="dv">{pick.get('CONTACT_ID','-')}</span>
                <span class="dk">Skill</span>       <span class="dv">{pick.get('SKILL_NAME','-')}</span>
                <span class="dk">LoB</span>         <span class="dv">{pick.get('LINE_OF_BUSINESS','-')}</span>
                <span class="dk">Brand</span>       <span class="dv">{pick.get('BRAND','-')}</span>
                <span class="dk">Transaction</span> <span class="dv">{pick.get('TRANSACTION_TYPE','-')}</span>
                <span class="dk">AHT</span>         <span class="dv">{pick.get('CALL_AHT_MINUTE','-')}m</span>
                <span class="dk">Vuln</span>        <span class="dv">{'Yes' if pick.get('VULNERABLE') else 'No'}</span>
              </div>
            </div>""", unsafe_allow_html=True)
            st.session_state.bot_step = "done"
        else:
            # Smart fallback: relax filters progressively
            base = df_pool[df_pool["STATUS"] == "ACTIVE"].copy() if "STATUS" in df_pool.columns else df_pool.copy()
            fallback = None
            for try_pool, label in [
                (base[base["LINE_OF_BUSINESS"] == lo] if lo and "LINE_OF_BUSINESS" in base.columns else pd.DataFrame(), f"LoB: {lo}"),
                (base[base["BRAND"]            == br] if br and "BRAND"            in base.columns else pd.DataFrame(), f"Brand: {br}"),
                (base[base["SKILL_NAME"]       == sk] if sk and "SKILL_NAME"       in base.columns else pd.DataFrame(), f"Skill: {sk}"),
                (base, "any available"),
            ]:
                if not try_pool.empty:
                    fallback = (try_pool, label); break

            if fallback:
                fp, label = fallback
                _bot(f"No exact match. But I found **{len(fp)}** contacts by relaxing to: {label}.")
                st.markdown(f"""<div class="res-warn">
                  <strong style="color:#92400e">⚠️ Relaxed Match — {label}</strong><br>
                  <span style="font-size:.68rem">{len(fp)} contacts available with these criteria.</span>
                </div>""", unsafe_allow_html=True)
                if st.button("Assign from relaxed pool →", key="bot_assign_fb"):
                    pick = fp.sample(1).iloc[0]
                    _bot(f"Assigned contact **{pick.get('CONTACT_ID','-')}** to **{col_name}** (relaxed match).")
                    st.session_state.bot_step = "done"
                    st.rerun()
                if st.button("Try different criteria", key="bot_retry"):
                    st.session_state.bot_step = "prefs"
                    st.rerun()
            else:
                _bot("No contacts at all available in the pool. Please check with your data team.")
                st.markdown('<div class="res-err"><strong style="color:#991b1b">❌ No Contacts Available</strong><br>'
                            '<span style="font-size:.68rem">The contact pool appears empty.</span></div>',
                            unsafe_allow_html=True)
                st.session_state.bot_step = "done"

    # ── Done ──────────────────────────────────────────────────────────────
    elif step == "done":
        d1, d2 = st.columns(2)
        with d1:
            if st.button("✓ Done", key="bot_done"):
                st.session_state.bot_step = "idle"
                st.session_state.bot_msgs = []
                st.rerun()
        with d2:
            if st.button("↺ Assign another", key="bot_again"):
                st.session_state.bot_msgs = []
                st.session_state.bot_step = "colleague"
                _bot("Who would you like to assign another contact to?")
                st.rerun()
