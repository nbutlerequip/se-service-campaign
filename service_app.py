"""
Southeastern Equipment - Service Campaign
Spring 2026 - Seasonal Customer Targeting

Targets customers in the months they historically buy service.
Built from 3 years of NDS transaction data.
Every lead: 10%+ monthly signal, $1K+ spend, active customer.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

try:
    from google.oauth2.service_account import Credentials
    import gspread
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False

# =============================================================================
# CONFIG
# =============================================================================

st.set_page_config(
    page_title="SE Service Campaign",
    page_icon="SE",
    layout="wide",
    initial_sidebar_state="collapsed"
)

APP_DIR = Path(__file__).parent
DATA_FILE = APP_DIR / "service_campaign_data.csv"

SE_NAVY = "#1e3a5f"
ADMIN_PASSWORD = "SEservice2026"

BRANCHES = {
    1: "Cambridge", 2: "North Canton", 3: "Gallipolis", 4: "Dublin",
    5: "Monroe", 6: "Burlington", 7: "Perrysburg", 9: "Brunswick",
    11: "Mentor", 12: "Fort Wayne", 13: "Indianapolis", 14: "Mansfield",
    15: "Heath", 16: "Marietta", 17: "Evansville", 19: "Holt", 20: "Novi"
}

REGIONS = {
    "SE Region (Brian)": [1, 3, 4, 15, 16],
    "NE Region (Matt)": [2, 7, 9, 11, 14],
    "West Region (Carrie)": [5, 6, 12, 13, 17, 19, 20]
}

MONTHS = {3: "March", 4: "April", 5: "May"}

MONTH_THEMES = {
    3: {"theme": "Spring Service Push", "push": "These customers historically service equipment in March. Concentrated buyers have narrow windows - don't miss them."},
    4: {"theme": "Pre-Season Maintenance", "push": "April buyers are prepping for peak construction season. Offer PM packages and seasonal inspections before they're too busy."},
    5: {"theme": "Peak Season Support", "push": "May is go-time. These customers are running machines hard. Target pre-summer service and filter changes."}
}

# =============================================================================
# GOOGLE SHEETS
# =============================================================================

def get_gsheet_connection():
    if not GSHEETS_AVAILABLE:
        return None
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
            )
            return gspread.authorize(creds)
    except Exception:
        pass
    return None

def get_call_log_sheet(client):
    if client is None:
        return None
    try:
        sheet_url = st.secrets.get("sheet_url", None)
        if sheet_url:
            spreadsheet = client.open_by_url(sheet_url)
        else:
            spreadsheet = client.open("SE_Service_Campaign_Log")
        try:
            worksheet = spreadsheet.worksheet("CallLog")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title="CallLog", rows=10000, cols=10)
            worksheet.append_row([
                "Timestamp", "Branch", "BranchName", "Month",
                "Customer", "CustomerName", "Called", "FollowUp", "Notes"
            ])
        return worksheet
    except Exception:
        return None

def load_call_log_from_sheets(worksheet):
    if worksheet is None:
        return {}
    try:
        records = worksheet.get_all_records()
        call_log = {}
        for record in records:
            key = f"{record['Customer']}_{record['Month']}"
            call_log[key] = {
                'branch': record['Branch'],
                'branch_name': record['BranchName'],
                'month': record['Month'],
                'customer': str(record['Customer']),
                'customer_name': record['CustomerName'],
                'called': record['Called'] == 'TRUE' or record['Called'] == True,
                'followup': record['FollowUp'] == 'TRUE' or record['FollowUp'] == True,
                'notes': record.get('Notes', ''),
                'timestamp': record.get('Timestamp', '')
            }
        return call_log
    except Exception:
        return {}

def save_to_sheets(worksheet, branch_id, branch_name, month, customer, customer_name, called, followup, notes):
    if worksheet is None:
        return False
    try:
        cell = None
        try:
            cell_list = worksheet.findall(str(customer))
            for c in cell_list:
                row_vals = worksheet.row_values(c.row)
                if len(row_vals) > 3 and str(row_vals[3]) == str(month):
                    cell = c
                    break
        except:
            pass
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        row_data = [
            timestamp, branch_id, branch_name, month, customer,
            customer_name, str(called).upper(), str(followup).upper(), notes
        ]
        if cell:
            worksheet.update(f'A{cell.row}:I{cell.row}', [row_data])
        else:
            worksheet.append_row(row_data)
        return True
    except Exception:
        return False

# =============================================================================
# LOCAL FALLBACK
# =============================================================================

import json

LOCAL_LOG_FILE = APP_DIR / "call_log.json"

def load_local_call_log():
    if LOCAL_LOG_FILE.exists():
        try:
            with open(LOCAL_LOG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_local_call_log(log):
    try:
        with open(LOCAL_LOG_FILE, 'w') as f:
            json.dump(log, f, indent=2, default=str)
    except:
        pass

# =============================================================================
# STYLES
# =============================================================================

st.markdown(f"""
<style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    header {{visibility: hidden;}}

    .main .block-container {{
        padding-top: 0;
        padding-bottom: 2rem;
        max-width: 1400px;
    }}

    .header-bar {{
        background: {SE_NAVY};
        color: white;
        padding: 16px 24px;
        margin: -1rem -1rem 1.5rem -1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 15px;
    }}
    .header-bar .branch-name {{
        font-weight: 600;
        font-size: 16px;
    }}

    .info-banner {{
        background: #e8f0fd;
        color: {SE_NAVY};
        padding: 12px 16px;
        border-radius: 4px;
        font-size: 13px;
        margin-bottom: 16px;
    }}
    .warning-banner {{
        background: #fff3cd;
        color: #856404;
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 12px;
        margin-bottom: 16px;
    }}

    .stButton > button {{
        background: {SE_NAVY};
        color: white;
        border: none;
        font-weight: 500;
    }}
    .stButton > button:hover {{
        background: #152d4a;
        color: white;
    }}

    .login-container {{
        text-align: center;
        padding: 60px 20px;
    }}
    .login-title {{
        color: {SE_NAVY};
        font-size: 36px;
        font-weight: 600;
        margin-bottom: 8px;
    }}
    .login-subtitle {{
        color: #666;
        font-size: 18px;
        margin-bottom: 8px;
    }}
    .login-cats {{
        color: #888;
        font-size: 13px;
        margin-bottom: 40px;
    }}

    .col-header {{
        font-weight: 600;
        font-size: 11px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding-bottom: 8px;
        border-bottom: 2px solid #ddd;
        margin-bottom: 8px;
    }}
    .customer-name {{
        font-weight: 500;
        font-size: 14px;
    }}
    .customer-acct {{
        font-size: 12px;
        color: #888;
    }}
    .cell-text {{
        font-size: 13px;
        color: #555;
    }}
    .empty-cell {{
        color: #bbb;
        font-style: italic;
    }}
    .row-divider {{
        border-bottom: 1px solid #eee;
        margin: 8px 0;
    }}

    .metric-card {{
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
    }}
    .metric-value {{
        font-size: 32px;
        font-weight: 600;
        color: {SE_NAVY};
    }}
    .metric-label {{
        font-size: 12px;
        color: #666;
        text-transform: uppercase;
    }}
    .region-header {{
        background: #f5f5f5;
        padding: 10px 15px;
        font-weight: 600;
        border-radius: 4px;
        margin: 20px 0 10px 0;
    }}

    .tier-strong {{
        background: #1e3a5f;
        color: white;
        font-size: 9px;
        font-weight: 600;
        padding: 1px 6px;
        border-radius: 3px;
        display: inline-block;
    }}
    .tier-good {{
        background: #2d7d9a;
        color: white;
        font-size: 9px;
        font-weight: 600;
        padding: 1px 6px;
        border-radius: 3px;
        display: inline-block;
    }}
    .tier-target {{
        background: #6c757d;
        color: white;
        font-size: 9px;
        font-weight: 600;
        padding: 1px 6px;
        border-radius: 3px;
        display: inline-block;
    }}

    .pattern-concentrated {{
        background: #dc3545;
        color: white;
        font-size: 9px;
        font-weight: 600;
        padding: 1px 6px;
        border-radius: 3px;
        display: inline-block;
    }}
    .pattern-seasonal {{
        background: #fd7e14;
        color: white;
        font-size: 9px;
        font-weight: 600;
        padding: 1px 6px;
        border-radius: 3px;
        display: inline-block;
    }}
    .pattern-yearround {{
        background: #28a745;
        color: white;
        font-size: 9px;
        font-weight: 600;
        padding: 1px 6px;
        border-radius: 3px;
        display: inline-block;
    }}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATA
# =============================================================================

@st.cache_data
def load_campaign_data():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
        for col in ['MonthRevenue', 'MonthPct', 'Y2023', 'Y2024', 'Y2025',
                     'TotalRevenue', 'TotalInvoices', 'MachineCount', 'YearsActive']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df['Customer'] = df['Customer'].astype(str)
        return df
    return None

# =============================================================================
# SESSION STATE
# =============================================================================

if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'branch' not in st.session_state:
    st.session_state.branch = None
if 'month' not in st.session_state:
    st.session_state.month = 3
if 'call_log' not in st.session_state:
    st.session_state.call_log = {}
if 'gsheet_connected' not in st.session_state:
    st.session_state.gsheet_connected = False
if 'worksheet' not in st.session_state:
    st.session_state.worksheet = None

if not st.session_state.gsheet_connected:
    client = get_gsheet_connection()
    if client:
        worksheet = get_call_log_sheet(client)
        if worksheet:
            st.session_state.worksheet = worksheet
            st.session_state.call_log = load_call_log_from_sheets(worksheet)
            st.session_state.gsheet_connected = True
    if not st.session_state.gsheet_connected:
        st.session_state.call_log = load_local_call_log()

# =============================================================================
# LOGIN
# =============================================================================

def show_login():
    st.markdown("""
    <div class="login-container">
        <div class="login-title">Service Campaign</div>
        <div class="login-subtitle">Spring 2026</div>
        <div class="login-cats">Seasonal customer targeting &bull; March - May</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if not st.session_state.gsheet_connected:
            st.markdown('<div class="warning-banner">&#9888; Local mode - Progress may not persist after restart</div>', unsafe_allow_html=True)

        options = ["Select your branch..."]
        branch_map = {}
        for num, name in sorted(BRANCHES.items()):
            label = f"{num} - {name}"
            options.append(label)
            branch_map[label] = num
        selected = st.selectbox("Branch", options, label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        month_options = list(MONTHS.values())
        selected_month = st.selectbox(
            "Campaign Month", month_options, index=0,
            help="Select which month's customer list to work"
        )
        month_num = [k for k, v in MONTHS.items() if v == selected_month][0]

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Start Campaign", use_container_width=True, type="primary"):
            if selected != "Select your branch...":
                st.session_state.branch = branch_map[selected]
                st.session_state.month = month_num
                st.session_state.page = 'dashboard'
                st.rerun()
            else:
                st.warning("Please select a branch")

        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("Admin Dashboard", use_container_width=True):
            st.session_state.page = 'admin_login'
            st.rerun()

    st.markdown("""
    <br><br><br>
    <div style="text-align: center; color: #999; font-size: 11px;">
        Created by Nick Butler &bull; Southeastern Equipment
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# ADMIN LOGIN
# =============================================================================

def show_admin_login():
    st.markdown("""
    <div class="login-container">
        <div class="login-title">Admin Dashboard</div>
        <div class="login-subtitle">Regional Performance View</div>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        password = st.text_input("Password", type="password")
        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("\u2190 Back", use_container_width=True):
                st.session_state.page = 'login'
                st.rerun()
        with col_b:
            if st.button("Login", use_container_width=True, type="primary"):
                if password == ADMIN_PASSWORD:
                    st.session_state.page = 'admin'
                    st.rerun()
                else:
                    st.error("Incorrect password")

# =============================================================================
# ADMIN DASHBOARD
# =============================================================================

def show_admin_dashboard():
    import altair as alt
    import calendar

    data = load_campaign_data()
    if data is None:
        st.error("Campaign data not found")
        return

    st.markdown(f"""
    <div class="header-bar">
        <span class="branch-name">Admin Dashboard - Spring 2026 Service Campaign</span>
        <span>Pacing & Performance</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        if st.button("\u2190 Logout"):
            st.session_state.page = 'login'
            st.rerun()
    with col3:
        if st.button("\u21bb Refresh"):
            if st.session_state.gsheet_connected:
                st.session_state.call_log = load_call_log_from_sheets(st.session_state.worksheet)
            st.rerun()

    call_log = st.session_state.call_log

    def get_business_days(year, month):
        cal = calendar.Calendar()
        return sum(1 for day in cal.itermonthdays2(year, month) if day[0] != 0 and day[1] < 5)

    def get_elapsed_business_days(year, month, day):
        cal = calendar.Calendar()
        return sum(1 for d, wd in cal.itermonthdays2(year, month) if d != 0 and d <= day and wd < 5)

    today = datetime.now()
    current_month = today.month
    default_month = MONTHS.get(current_month, "March")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 3])
    with col1:
        month_filter = st.selectbox("Campaign Month", list(MONTHS.values()),
                                     index=list(MONTHS.values()).index(default_month))
    selected_month_num = [k for k, v in MONTHS.items() if v == month_filter][0]

    total_biz_days = get_business_days(2026, selected_month_num)
    if selected_month_num == current_month and today.year == 2026:
        elapsed_biz_days = get_elapsed_business_days(2026, selected_month_num, today.day)
    elif (today.year == 2026 and current_month > selected_month_num) or today.year > 2026:
        elapsed_biz_days = total_biz_days
    else:
        elapsed_biz_days = 0
    days_remaining = total_biz_days - elapsed_biz_days
    expected_pct = (elapsed_biz_days / total_biz_days * 100) if total_biz_days > 0 else 0

    def get_stats(branch_ids, month_name):
        month_num = [k for k, v in MONTHS.items() if v == month_name][0]
        total = called = followups = 0
        for branch_id in branch_ids:
            bmd = data[(data['Branch'] == branch_id) & (data['Month'] == month_num)]
            total += len(bmd)
            for _, row in bmd.iterrows():
                key = f"{row['Customer']}_{month_num}"
                if key in call_log:
                    if call_log[key].get('called', False): called += 1
                    if call_log[key].get('followup', False): followups += 1
        return total, called, followups

    all_branch_ids = list(BRANCHES.keys())
    total, called, followups = get_stats(all_branch_ids, month_filter)
    actual_pct = (called / total * 100) if total > 0 else 0
    pace_diff = actual_pct - expected_pct
    if pace_diff >= 5: pace_status, pace_color = "Ahead", "#28a745"
    elif pace_diff >= -5: pace_status, pace_color = "On Pace", "#ffc107"
    else: pace_status, pace_color = "Behind", "#dc3545"

    # Revenue opportunity for this month
    month_data = data[data['Month'] == selected_month_num]
    month_rev = month_data['MonthRevenue'].sum()

    st.markdown("### Pacing Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{called:,}</div><div class="metric-label">Calls Made</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{total - called:,}</div><div class="metric-label">Remaining</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{actual_pct:.0f}%</div><div class="metric-label">Complete</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{expected_pct:.0f}%</div><div class="metric-label">Expected</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: {pace_color}; font-size: 18px;">{pace_status}</div><div class="metric-label">{days_remaining} days left</div></div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="position: relative; margin: 20px 0 40px 0;">
        <div style="background: #e0e0e0; border-radius: 10px; height: 24px; overflow: hidden;">
            <div style="background: {SE_NAVY}; width: {min(actual_pct, 100)}%; height: 100%; border-radius: 10px;"></div>
        </div>
        <div style="position: absolute; left: {min(expected_pct, 100)}%; top: -5px; transform: translateX(-50%);">
            <div style="width: 3px; height: 34px; background: #333;"></div>
            <div style="font-size: 10px; color: #666; margin-top: 2px; white-space: nowrap;">Target ({expected_pct:.0f}%)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Bar chart
    st.markdown("### Branch Performance")
    branch_chart_data = []
    for region_name, branch_ids in REGIONS.items():
        for branch_id in branch_ids:
            branch_name = BRANCHES[branch_id]
            b_total, b_called, b_followups = get_stats([branch_id], month_filter)
            b_pct = (b_called / b_total * 100) if b_total > 0 else 0
            branch_chart_data.append({
                'Branch': branch_name, 'Region': region_name.split(' (')[0],
                'Completion': b_pct, 'Called': b_called, 'Total': b_total
            })
    branch_df = pd.DataFrame(branch_chart_data)
    branch_df['sort_order'] = branch_df['Region'].map({'SE Region': 0, 'NE Region': 1, 'West Region': 2})
    branch_df = branch_df.sort_values(['sort_order', 'Completion'], ascending=[True, False])
    branch_order = branch_df['Branch'].tolist()

    chart = alt.Chart(branch_df).mark_bar().encode(
        x=alt.X('Branch:N', sort=branch_order, axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('Completion:Q', scale=alt.Scale(domain=[0, 100]), title='% Complete'),
        color=alt.Color('Region:N', scale=alt.Scale(
            domain=['SE Region', 'NE Region', 'West Region'],
            range=[SE_NAVY, '#2d7d9a', '#28a745']
        )),
        tooltip=['Branch', 'Region', alt.Tooltip('Completion:Q', format='.0f'), 'Called', 'Total']
    ).properties(height=350)
    rule = alt.Chart(pd.DataFrame({'y': [expected_pct]})).mark_rule(
        color='#333', strokeDash=[5, 5], strokeWidth=2
    ).encode(y='y:Q')
    st.altair_chart(chart + rule, use_container_width=True)
    st.caption(f"Dashed line = Expected pace ({expected_pct:.0f}%) | Bars colored by region")

    # Regional tables
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Regional Details")
    for region_name, branch_ids in REGIONS.items():
        r_total, r_called, r_followups = get_stats(branch_ids, month_filter)
        r_pct = (r_called / r_total * 100) if r_total > 0 else 0
        st.markdown(f'<div class="region-header">{region_name} \u2014 {r_pct:.0f}% Complete ({r_called}/{r_total})</div>', unsafe_allow_html=True)
        branch_table = []
        for branch_id in branch_ids:
            bn = BRANCHES[branch_id]
            b_total, b_called, b_followups = get_stats([branch_id], month_filter)
            b_pct = (b_called / b_total * 100) if b_total > 0 else 0
            b_pd = b_pct - expected_pct
            b_status = "Ahead" if b_pd >= 5 else ("On Pace" if b_pd >= -5 else "Behind")
            exp_calls = int(expected_pct / 100 * b_total)
            behind = max(0, exp_calls - b_called)
            branch_table.append({
                'Branch': bn, 'Called': b_called, 'Remaining': b_total - b_called,
                'Complete': f"{b_pct:.0f}%", 'Status': b_status,
                'To Catch Up': behind if behind > 0 else "\u2014", 'Follow-ups': b_followups
            })
        st.dataframe(pd.DataFrame(branch_table), use_container_width=True, hide_index=True)

    # Follow-ups
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Follow-ups Flagged")
    followup_data = []
    for key, log in call_log.items():
        if log.get('followup', False) and log.get('month') == selected_month_num:
            followup_data.append({
                'Branch': log.get('branch_name', ''), 'Customer': log.get('customer_name', ''),
                'Account': log.get('customer', ''), 'Notes': log.get('notes', ''),
                'Updated': log.get('timestamp', '')
            })
    if followup_data:
        st.dataframe(pd.DataFrame(followup_data), use_container_width=True, hide_index=True)
    else:
        st.info("No follow-ups flagged yet for this month")

    # Export
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Export")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export All Call Logs", use_container_width=True):
            export_data = [{
                'Timestamp': l.get('timestamp', ''), 'Branch': l.get('branch_name', ''),
                'Month': MONTHS.get(l.get('month', 0), ''), 'Customer': l.get('customer', ''),
                'CustomerName': l.get('customer_name', ''),
                'Called': 'Yes' if l.get('called', False) else '',
                'FollowUp': 'Yes' if l.get('followup', False) else '',
                'Notes': l.get('notes', '')
            } for l in call_log.values()]
            if export_data:
                csv = pd.DataFrame(export_data).to_csv(index=False)
                st.download_button("Download CSV", csv,
                    f"service_logs_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv",
                    use_container_width=True)
            else:
                st.info("No data to export")
    with col2:
        if st.button("Export Follow-ups Only", use_container_width=True):
            if followup_data:
                csv = pd.DataFrame(followup_data).to_csv(index=False)
                st.download_button("Download Follow-ups", csv,
                    f"service_followups_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv",
                    use_container_width=True)
            else:
                st.info("No follow-ups to export")

# =============================================================================
# BRANCH DASHBOARD
# =============================================================================

def show_dashboard():
    branch_id = st.session_state.branch
    month_id = st.session_state.month
    branch_name = BRANCHES.get(branch_id, "Unknown")
    month_name = MONTHS.get(month_id, "Unknown")

    data = load_campaign_data()
    if data is None:
        st.error("Data file not found.")
        if st.button("\u2190 Back"):
            st.session_state.page = 'login'
            st.rerun()
        return

    df = data[(data['Branch'] == branch_id) & (data['Month'] == month_id)].copy()

    if len(df) == 0:
        st.warning(f"No customers found for {branch_name} in {month_name}")
        if st.button("\u2190 Back"):
            st.session_state.page = 'login'
            st.rerun()
        return

    call_log = st.session_state.call_log
    df['Called'] = df.apply(
        lambda row: call_log.get(f"{row['Customer']}_{month_id}", {}).get('called', False), axis=1
    )
    df['FollowUp'] = df.apply(
        lambda row: call_log.get(f"{row['Customer']}_{month_id}", {}).get('followup', False), axis=1
    )

    total = len(df)
    called = df['Called'].sum()
    followups = df['FollowUp'].sum()
    month_rev = df['MonthRevenue'].sum()
    strong_ct = len(df[df['Tier'] == 'STRONG'])

    # Header
    st.markdown(f"""
    <div class="header-bar">
        <span class="branch-name">{branch_name} \u2014 {month_name} Campaign</span>
        <span>{called} of {total} Called &bull; {followups} Follow-ups</span>
    </div>
    """, unsafe_allow_html=True)

    # Month switcher
    col1, col2, col3 = st.columns([2, 4, 1])
    with col1:
        month_options = list(MONTHS.values())
        current_index = list(MONTHS.keys()).index(month_id)
        selected_month = st.selectbox(
            "Campaign Month", month_options, index=current_index,
            key="month_selector", label_visibility="collapsed"
        )
        new_month_id = [k for k, v in MONTHS.items() if v == selected_month][0]
        if new_month_id != month_id:
            st.session_state.month = new_month_id
            st.rerun()
    with col3:
        if st.button("\u2190 Branch"):
            st.session_state.page = 'login'
            st.rerun()

    theme = MONTH_THEMES.get(month_id, {})
    campaign_theme = theme.get('theme', 'Service Campaign')
    campaign_push = theme.get('push', '')

    st.markdown(f"""
    <div class="info-banner">
        <strong>{month_name} Campaign: {campaign_theme}</strong> &bull; ${month_rev:,.0f} historical {month_name} revenue &bull; {strong_ct} proven multi-year buyers<br>
        {campaign_push}<br>
        "History" shows what each customer spends in {month_name} and how reliable the pattern is.
    </div>
    <div class="warning-banner">
        <strong>Before Calling:</strong> Verify customer service history and open work orders on NDS.
        Use the equipment info to offer specific maintenance recommendations.
    </div>
    """, unsafe_allow_html=True)

    # Filters
    col1, col2, col3 = st.columns([1.5, 3.5, 1])
    with col1:
        hide_called = st.checkbox("Hide called", value=True)
    with col2:
        search = st.text_input("Search", placeholder="Search customer or equipment...",
                               label_visibility="collapsed")

    filtered = df.copy()
    if hide_called:
        filtered = filtered[~filtered['Called']]
    if search:
        mask = (
            filtered['CustomerName'].str.contains(search, case=False, na=False) |
            filtered['Equipment'].astype(str).str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]

    # Sort: STRONG first, then GOOD, then TARGET, then by revenue
    tier_order = {'STRONG': 0, 'GOOD': 1, 'TARGET': 2}
    filtered['_ts'] = filtered['Tier'].map(tier_order)
    filtered = filtered.sort_values(['Called', '_ts', 'MonthRevenue'], ascending=[True, True, False])

    st.caption(f"{len(filtered)} customers shown")

    # Column headers
    c1, c2, c3, c4, c5, c6 = st.columns([0.6, 0.8, 2.5, 1.8, 1.8, 2.8])
    c1.markdown('<div class="col-header">Called</div>', unsafe_allow_html=True)
    c2.markdown('<div class="col-header">Follow-Up</div>', unsafe_allow_html=True)
    c3.markdown('<div class="col-header">Customer</div>', unsafe_allow_html=True)
    c4.markdown('<div class="col-header">Equipment</div>', unsafe_allow_html=True)
    c5.markdown('<div class="col-header">History</div>', unsafe_allow_html=True)
    c6.markdown('<div class="col-header">Notes</div>', unsafe_allow_html=True)

    for _, row in filtered.iterrows():
        cust_id = str(row['Customer'])
        cust_name = row['CustomerName'] or cust_id
        key = f"{cust_id}_{month_id}"
        log_entry = call_log.get(key, {})
        is_called = log_entry.get('called', False)
        is_followup = log_entry.get('followup', False)
        saved_notes = log_entry.get('notes', '')

        c1, c2, c3, c4, c5, c6 = st.columns([0.6, 0.8, 2.5, 1.8, 1.8, 2.8])

        with c1:
            new_called = st.checkbox("", value=is_called, key=f"called_{key}", label_visibility="collapsed")
        with c2:
            new_followup = st.checkbox("", value=is_followup, key=f"followup_{key}", label_visibility="collapsed")

        # Customer name with tier badge
        with c3:
            tier = row['Tier']
            tier_class = f'tier-{tier.lower()}'
            st.markdown(f'<div class="customer-name">{cust_name} <span class="{tier_class}">{tier}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="customer-acct">Acct: {cust_id}</div>', unsafe_allow_html=True)

        # Equipment
        with c4:
            equip = row['Equipment'] if pd.notna(row['Equipment']) and row['Equipment'] != '' else ""
            if equip:
                st.markdown(f'<div class="cell-text">{equip}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-cell">\u2014</div>', unsafe_allow_html=True)

        # History
        with c5:
            m_rev = row['MonthRevenue'] if pd.notna(row['MonthRevenue']) else 0
            m_pct = row['MonthPct'] if pd.notna(row['MonthPct']) else 0
            years = int(row['YearsActive']) if pd.notna(row['YearsActive']) else 0
            svc_type = row['ServiceType'] if pd.notna(row['ServiceType']) else ''
            years_bought = row['YearsBought'] if pd.notna(row['YearsBought']) else ''

            rev_str = f"${m_rev:,.0f} ({m_pct:.0f}% of annual)"
            year_str = f"{years}/3 yrs" if years > 0 else ""
            detail = f"{svc_type}" if svc_type else ""
            if years_bought:
                detail = f"{detail} &bull; {years_bought}" if detail else years_bought

            st.markdown(f'<div class="cell-text">{rev_str} &bull; {year_str}</div>', unsafe_allow_html=True)
            if detail:
                st.markdown(f'<div style="font-size:11px;color:#888;">{detail}</div>', unsafe_allow_html=True)

        # Notes
        with c6:
            new_notes = st.text_input("", value=saved_notes, key=f"notes_{key}",
                                      label_visibility="collapsed", placeholder="Add notes...")

        # Save changes
        if new_called != is_called or new_followup != is_followup or new_notes != saved_notes:
            st.session_state.call_log[key] = {
                'branch': branch_id, 'branch_name': branch_name,
                'month': month_id, 'customer': cust_id, 'customer_name': cust_name,
                'called': new_called, 'followup': new_followup,
                'notes': new_notes,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            if st.session_state.gsheet_connected:
                save_to_sheets(st.session_state.worksheet, branch_id, branch_name, month_id,
                    cust_id, cust_name, new_called, new_followup, new_notes)
            else:
                save_local_call_log(st.session_state.call_log)
            if new_called != is_called:
                st.rerun()

        st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)

    # Export
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Export to CSV", use_container_width=True):
            export_data = []
            for _, row in df.iterrows():
                cid = str(row['Customer'])
                key = f"{cid}_{month_id}"
                log = call_log.get(key, {})
                export_data.append({
                    'Branch': branch_name, 'Month': month_name,
                    'Account': cid, 'Customer': row['CustomerName'],
                    'Tier': row['Tier'], 'Equipment': row['Equipment'] if pd.notna(row['Equipment']) else '',
                    'MonthRevenue': row['MonthRevenue'], 'MonthPct': row['MonthPct'],
                    'YearsActive': row['YearsActive'], 'ServiceType': row['ServiceType'] if pd.notna(row['ServiceType']) else '',
                    'ActiveMonths': row['ActiveMonths'] if pd.notna(row['ActiveMonths']) else '',
                    'Called': 'Yes' if log.get('called', False) else '',
                    'Follow_Up': 'Yes' if log.get('followup', False) else '',
                    'Notes': log.get('notes', ''), 'Last_Updated': log.get('timestamp', '')
                })
            csv = pd.DataFrame(export_data).to_csv(index=False)
            st.download_button("Download", csv,
                f"service_{branch_name.replace(' ', '_')}_{month_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv", use_container_width=True)

    st.markdown("""
    <br><br>
    <div style="text-align: center; color: #999; font-size: 11px; padding: 20px 0; border-top: 1px solid #eee;">
        Created by Nick Butler &bull; Southeastern Equipment &bull; Spring 2026
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# MAIN
# =============================================================================

if st.session_state.page == 'login':
    show_login()
elif st.session_state.page == 'admin_login':
    show_admin_login()
elif st.session_state.page == 'admin':
    show_admin_dashboard()
elif st.session_state.page == 'dashboard':
    show_dashboard()
else:
    show_login()
