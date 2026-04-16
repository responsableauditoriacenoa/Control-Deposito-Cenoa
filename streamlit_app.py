from __future__ import annotations

from datetime import date, datetime
import html
import io

import pandas as pd
import streamlit as st

from streamlit_backend import (
    AUDITORES_DEFAULT,
    DB_DISPLAY,
    MODULOS_ACTIVOS,
    MODULO_NOMBRES,
    PONDERACION_EQUIVALENTE,
    close_audit,
    create_audit,
    fetch_table,
    get_audit,
    get_config,
    import_creditos,
    import_transferencias,
    import_ventas_internas,
    init_db,
    list_audits,
    list_reports,
    save_close_draft,
    save_config,
    save_creditos_edits,
    save_transferencias_edits,
    save_ventas_edits,
    update_manual_control,
)


st.set_page_config(page_title="Control Integral de Depositos", layout="wide")
init_db()


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(1200px 600px at -10% -10%, rgba(99, 102, 241, 0.12) 0%, rgba(99, 102, 241, 0) 55%),
                radial-gradient(1000px 500px at 110% -10%, rgba(56, 189, 248, 0.1) 0%, rgba(56, 189, 248, 0) 55%),
                #f3f6fb;
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stToolbar"] { right: 1rem; }
        [data-testid="stSidebar"] {
            background: linear-gradient(170deg, #0c1739 0%, #111f4d 55%, #13275f 100%);
            border-right: 1px solid rgba(129, 140, 248, 0.25);
        }
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.2rem;
        }
        [data-testid="stSidebar"] * { color: #eef4ff; }
        .sidebar-brand h2 {
            color:#ffffff;
            font-size:27px;
            font-weight:800;
            letter-spacing:.01em;
            margin:0;
        }
        .sidebar-brand p {
            color:#c7d3f8;
            margin:6px 0 0 0;
            font-size:13px;
            opacity:.95;
        }
        [data-testid="stSidebar"] h2 {
            font-size: 30px;
            font-weight: 800;
            letter-spacing: -.02em;
        }
        [data-testid="stSidebar"] .stCaption {
            color: #c7d3f8 !important;
        }
        [data-testid="stSidebar"] .stRadio > label,
        [data-testid="stSidebar"] .stSelectbox > label {
            color: #c7d3f8 !important;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: .08em;
            font-weight: 700;
        }
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(199, 210, 254, 0.35);
            border-radius: 12px;
            min-height: 46px;
        }
        .stForm {
            background: rgba(255,255,255,.72);
            border: 1px solid #dbe4f2;
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 10px 24px rgba(15,23,42,.05);
        }
        .stTextInput > label,
        .stTextArea > label,
        .stDateInput > label,
        .stNumberInput > label,
        .stSelectbox > label,
        .stFileUploader > label {
            color:#64748b !important;
            font-size:12px !important;
            text-transform:uppercase;
            letter-spacing:.08em;
            font-weight:800 !important;
        }
        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        .stTextArea textarea {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%) !important;
            color:#0f172a !important;
            border:1px solid #d6e0f0 !important;
            border-radius:12px !important;
            box-shadow:none !important;
        }
        .stTextInput input::placeholder,
        .stNumberInput input::placeholder,
        .stDateInput input::placeholder,
        .stTextArea textarea::placeholder {
            color:#94a3b8 !important;
        }
        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stDateInput input:focus,
        .stTextArea textarea:focus {
            border-color:#818cf8 !important;
            box-shadow:0 0 0 4px rgba(99,102,241,.12) !important;
        }
        .stTextArea textarea {
            min-height: 124px !important;
        }
        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%) !important;
            color:#0f172a !important;
            border:1px solid #d6e0f0 !important;
            border-radius:12px !important;
            min-height:48px !important;
            box-shadow:none !important;
        }
        .stSelectbox div[data-baseweb="select"] span,
        .stMultiSelect div[data-baseweb="select"] span,
        .stSelectbox div[data-baseweb="select"] svg,
        .stMultiSelect div[data-baseweb="select"] svg {
            color:#334155 !important;
            fill:#334155 !important;
        }
        .stFileUploader [data-testid="stFileUploaderDropzone"] {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%) !important;
            border: 1px solid #d6e0f0 !important;
            border-radius: 16px !important;
            padding: 16px !important;
        }
        .stFileUploader [data-testid="stFileUploaderDropzone"]:hover {
            border-color:#a5b4fc !important;
            background:#f8fbff !important;
        }
        .stFileUploader [data-testid="stFileUploaderDropzone"] * {
            color:#475569 !important;
        }
        .stFileUploader section button {
            background:#ffffff !important;
            color:#334155 !important;
            border:1px solid #cbd5e1 !important;
            border-radius:12px !important;
            box-shadow:none !important;
        }
        .sidebar-group-title {
            color:#c7d3f8;
            font-size:12px;
            text-transform:uppercase;
            letter-spacing:.08em;
            font-weight:800;
            margin:18px 0 10px;
        }
        .sidebar-nav-active {
            width:100%;
            min-height:46px;
            display:flex;
            align-items:center;
            border-radius:12px;
            border:1px solid #a5b4fc;
            background:linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
            color:#ffffff;
            font-size:15px;
            font-weight:700;
            padding:0 14px;
            box-shadow:0 6px 16px rgba(79,70,229,.28);
            margin-bottom:10px;
        }
        [data-testid="stSidebar"] .stButton > button {
            width:100%;
            justify-content:flex-start;
            text-align:left;
            min-height:46px;
            border-radius:12px !important;
            border:1px solid rgba(255,255,255,0.18) !important;
            background:rgba(255,255,255,0.05) !important;
            color:#ecf1ff !important;
            box-shadow:none !important;
            padding:0 14px !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background:rgba(255,255,255,0.12) !important;
            border-color:rgba(199,210,254,.75) !important;
        }
        [data-testid="stSidebar"] .stButton > button[data-active="true"] {
            background:linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
            border-color:#a5b4fc !important;
            box-shadow:0 6px 16px rgba(79,70,229,.28) !important;
        }
        .hero-card, .metric-card, .table-card, .surface-card {
            background: white;
            border: 1px solid #dbe4f2;
            border-radius: 18px;
            padding: 18px 20px;
            box-shadow: 0 10px 24px rgba(15,23,42,.06);
        }
        .hero-card { background: linear-gradient(135deg,#1f2a6b 0%,#3f4cc9 52%,#6366f1 100%); color: white; border: none; }
        .hero-card h1, .hero-card p { color: white; margin: 0; }
        .metric-card.metric-primary {
            background: linear-gradient(145deg, #3f45b3 0%, #5548d8 52%, #6d5ef0 100%);
            border: 1px solid rgba(199, 210, 254, 0.65);
        }
        .metric-card.metric-primary .metric-label,
        .metric-card.metric-primary .metric-value,
        .metric-card.metric-primary .metric-sub {
            color: #eef2ff;
        }
        .metric-label { font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: .08em; font-weight: 700; }
        .metric-value { font-size: 32px; font-weight: 800; color: #0f172a; margin-top: 8px; letter-spacing: -0.3px; }
        .metric-sub { font-size: 12px; color: #64748b; margin-top: 6px; min-height: 16px; }
        .section-title { font-size: 26px; font-weight: 800; color: #0f172a; margin-bottom: 8px; }
        .section-copy { color: #475569; margin-bottom: 14px; }
        .indicator-header {
            display:flex;
            align-items:flex-start;
            justify-content:space-between;
            gap:16px;
            margin-bottom:14px;
        }
        .indicator-header h2 {
            margin:0;
            font-size:28px;
            color:#0f172a;
            font-weight:800;
        }
        .indicator-header p {
            margin:6px 0 0 0;
            color:#64748b;
            font-size:14px;
        }
        .auditoria-info-panel {
            display:grid;
            grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));
            gap:10px;
            margin:0 0 16px 0;
            background:#f8fbff;
            border:1px solid #dbe4f2;
            border-radius:14px;
            padding:14px;
        }
        .auditoria-info-item {
            color:#334155;
            font-size:14px;
            line-height:1.45;
        }
        .auditoria-info-item strong {
            color:#0f172a;
        }
        .indicator-nav-active {
            width:100%;
            border:1px solid #a5b4fc;
            background:linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
            color:#fff;
            border-radius:11px;
            padding:10px 12px;
            font-weight:700;
            box-shadow:0 8px 16px rgba(79,70,229,.24);
            margin-bottom:8px;
        }
        .indicator-screen-card {
            background:#ffffff;
            border:1px solid #dbe4f2;
            border-radius:16px;
            padding:16px;
            box-shadow:0 8px 20px rgba(15,23,42,.05);
        }
        .indicator-screen-card h3 {
            margin:0 0 8px 0;
            color:#0f172a;
            font-size:22px;
            font-weight:800;
        }
        .helper-text {
            color:#64748b;
            margin-bottom:12px;
            font-size:14px;
        }
        .summary-card {
            background:#f8fbff;
            border:1px solid #dbe4f2;
            border-radius:11px;
            padding:10px 12px;
            margin-bottom:10px;
        }
        .summary-card span {
            display:block;
            font-size:12px;
            color:#64748b;
            margin-bottom:5px;
            text-transform:uppercase;
            letter-spacing:.05em;
            font-weight:700;
        }
        .summary-card strong {
            font-size:22px;
            color:#4f46e5;
        }
        .resumen-cierre {
            margin-top:20px;
            padding:18px;
            border:1px solid #d6e0f0;
            border-radius:14px;
            background:linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            box-shadow:0 6px 16px rgba(15,23,42,.05);
        }
        .resumen-cierre-grid {
            display:grid;
            grid-template-columns:repeat(2, minmax(280px, 1fr));
            gap:14px;
            margin-top:8px;
        }
        .resumen-cierre-panel {
            border:1px solid #dbe4f3;
            border-radius:12px;
            padding:12px;
            background:linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            box-shadow:0 6px 16px rgba(15,23,42,.05);
        }
        .resumen-cierre-panel h4 {
            margin:0 0 10px 0;
            font-size:15px;
            color:#0f172a;
            font-weight:800;
        }
        .cierre-note {
            margin-top:12px;
            padding:10px 12px;
            border-radius:10px;
            font-size:13px;
        }
        .cierre-note.warn {
            border:1px solid #fecaca;
            background:#fff1f2;
            color:#9f1239;
        }
        .cierre-note.info {
            border:1px solid #bfdbfe;
            background:#eff6ff;
            color:#1e3a8a;
        }
        .total-card-grid {
            display:grid;
            grid-template-columns:repeat(auto-fit, minmax(240px, 1fr));
            gap:16px;
            margin-top:18px;
            margin-bottom:18px;
        }
        .total-card {
            background:linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
            border-radius:14px;
            padding:20px;
            color:#ffffff;
            text-align:center;
            box-shadow:0 10px 24px rgba(79,70,229,.24);
        }
        .total-card h4 {
            margin:0 0 12px 0;
            font-size:14px;
            font-weight:600;
            opacity:.95;
        }
        .total-card .score-value {
            font-size:32px;
            font-weight:800;
            margin:0;
            letter-spacing:-.5px;
        }
        .total-card .calificacion-value {
            font-size:18px;
            font-weight:700;
            margin:0;
        }
        @media (max-width: 1024px) {
            .resumen-cierre-grid {
                grid-template-columns:1fr;
            }
        }
        .audit-chip {
            display:inline-block; padding:8px 12px; border-radius:999px; background:#e8eefb; color:#29417f;
            font-weight:600; font-size:13px; margin-right:10px; margin-bottom:8px;
        }
        .traffic-card {
            border: 1px solid #dbe4f2;
            border-radius: 12px;
            padding: 12px 14px;
            background: #fff;
            box-shadow: 0 4px 14px rgba(15,23,42,.04);
        }
        .traffic-title { font-size: 13px; color: #475569; font-weight: 700; }
        .traffic-value { margin-top: 6px; font-size: 24px; font-weight: 800; color: #0f172a; }
        .status-ok, .status-warn, .status-bad {
            display:inline-block; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:700;
        }
        .status-ok { background:#dcfce7; color:#166534; }
        .status-warn { background:#fef3c7; color:#92400e; }
        .status-bad { background:#fee2e2; color:#991b1b; }
        .subsection-title {
            font-size: 18px; font-weight: 800; color: #0f172a; margin: 20px 0 10px 0;
            padding-bottom: 8px; border-bottom: 2px solid #d7e2fa;
        }
        .stExpander {
            border: 1px solid #dbe4f2 !important;
            border-radius: 14px !important;
            background: rgba(255,255,255,0.92) !important;
            box-shadow: 0 6px 18px rgba(15,23,42,.05);
        }
        .stExpander summary {
            font-weight: 800 !important;
            color: #0f172a !important;
        }
        .stDataFrame, div[data-testid="stDataFrame"] {
            border-radius: 14px !important;
            overflow: hidden;
            border: 1px solid #dbe4f2;
            background: white;
        }
        div[data-testid="stDataFrame"] [data-testid="stTable"] thead tr th,
        div[data-testid="stDataEditor"] [data-testid="stTable"] thead tr th {
            background: linear-gradient(180deg,#f8fbff 0%,#eef4ff 100%) !important;
            color: #334155 !important;
            font-size: 12px !important;
            text-transform: uppercase;
            letter-spacing: .06em;
            font-weight: 800 !important;
            border-bottom: 1px solid #dbe4f2 !important;
        }
        div[data-testid="stDataFrame"] [data-testid="stTable"] tbody tr:nth-child(even),
        div[data-testid="stDataEditor"] [data-testid="stTable"] tbody tr:nth-child(even) {
            background: #fbfdff !important;
        }
        div[data-testid="stDataFrame"] [data-testid="stTable"] tbody tr td,
        div[data-testid="stDataEditor"] [data-testid="stTable"] tbody tr td {
            color:#0f172a !important;
            background:#ffffff !important;
            border-bottom:1px solid #e7edf7 !important;
        }
        div[data-testid="stDataFrame"] [data-testid="stTable"] tbody tr:hover,
        div[data-testid="stDataEditor"] [data-testid="stTable"] tbody tr:hover {
            background: #f5f8ff !important;
        }
        div[data-testid="stDataEditor"] {
            border-radius: 14px !important;
            overflow: hidden;
            border: 1px solid #dbe4f2;
            box-shadow: 0 6px 18px rgba(15,23,42,.05);
            background: white;
        }
        div[data-testid="stDataEditor"] input,
        div[data-testid="stDataEditor"] textarea,
        div[data-testid="stDataEditor"] select {
            background:#ffffff !important;
            color:#0f172a !important;
            border:1px solid #cfd9ea !important;
            border-radius:8px !important;
        }
        div[data-testid="stDataEditor"] input[type="checkbox"] {
            accent-color:#6366f1 !important;
        }
        .mini-kpi {
            background:#f8fbff;
            border:1px solid #dbe4f2;
            border-radius:14px;
            padding:12px 14px;
        }
        .mini-kpi-label {
            font-size:11px;
            font-weight:800;
            color:#64748b;
            text-transform:uppercase;
            letter-spacing:.08em;
        }
        .mini-kpi-value {
            font-size:24px;
            font-weight:800;
            color:#0f172a;
            margin-top:6px;
        }
        .table-shell {
            background:white;
            border:1px solid #dbe4f2;
            border-radius:18px;
            padding:12px;
            box-shadow:0 8px 20px rgba(15,23,42,.05);
        }
        .table-shell + .table-shell {
            margin-top: 14px;
        }
        .readonly-table-wrap {
            overflow-x:auto;
            border:1px solid #dbe4f2;
            border-radius:14px;
            background:#fff;
        }
        .readonly-table {
            width:100%;
            min-width:780px;
            border-collapse:collapse;
            background:#fff;
        }
        .readonly-table thead {
            background:#f4f7fd;
        }
        .readonly-table th {
            color:#0f172a;
            font-weight:800;
            padding:12px 12px;
            text-align:left;
            font-size:12px;
            text-transform:uppercase;
            letter-spacing:.05em;
            border-bottom:1px solid #dbe4f2;
            white-space:nowrap;
        }
        .readonly-table td {
            padding:12px 12px;
            color:#1f2937;
            font-size:14px;
            border-bottom:1px solid #e7edf7;
            vertical-align:middle;
        }
        .readonly-table tbody tr:nth-child(even) {
            background:#fcfdff;
        }
        .readonly-table tbody tr:hover {
            background:#f7faff;
        }
        .cell-code {
            font-weight:800;
            color:#1f2a6b;
        }
        .score-pill,
        .status-pill {
            display:inline-flex;
            align-items:center;
            justify-content:center;
            border-radius:999px;
            padding:6px 10px;
            font-weight:700;
            font-size:12px;
            white-space:nowrap;
        }
        .score-pill {
            background:#eef2ff;
            color:#3730a3;
        }
        .status-pill.status-completada {
            background:#dcfce7;
            color:#166534;
        }
        .status-pill.status-en-progreso {
            background:#fef3c7;
            color:#92400e;
        }
        .status-pill.status-default {
            background:#e2e8f0;
            color:#334155;
        }
        .sidebar-session {
            background: rgba(255,255,255,.1);
            border-radius: 12px;
            padding: 10px 12px;
            border: 1px solid rgba(255,255,255,.12);
        }
        .sidebar-footer {
            margin-top: 14px;
            border-top: 1px dashed rgba(185, 199, 234, 0.35);
            padding-top: 12px;
            display:flex;
            flex-direction:column;
            gap:10px;
        }
        .sidebar-session-label {
            font-size:12px;
            color:#c7d3f8;
            text-transform:uppercase;
            letter-spacing:.08em;
            font-weight:700;
        }
        .sidebar-session-name {
            font-size:14px;
            color:#fff;
            font-weight:700;
            margin-top:6px;
            white-space:nowrap;
            overflow:hidden;
            text-overflow:ellipsis;
        }
        .sidebar-audit {
            margin-top:10px;
            font-size:13px;
            color:#c7d3f8;
            line-height:1.4;
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 11px !important;
            font-weight: 700 !important;
            border: 1px solid #d6e0f0 !important;
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%) !important;
            color:#1e293b !important;
            box-shadow: 0 6px 18px rgba(15,23,42,.05);
        }
        .stButton > button[kind="primary"], .stDownloadButton > button {
            background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
            color: white !important;
            border-color:#818cf8 !important;
            box-shadow: 0 8px 20px rgba(79,70,229,.22);
        }
        .stButton > button:hover {
            border-color:#a5b4fc !important;
            background:#f8fbff !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            background: rgba(255,255,255,.65);
            border: 1px solid #dbe4f2;
            border-radius: 10px;
            padding: 8px 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    st.session_state.setdefault("auditor_nombre", AUDITORES_DEFAULT[0])
    st.session_state.setdefault("section", "Dashboard")
    st.session_state.setdefault("selected_audit_id", None)
    st.session_state.setdefault("operation_module", 1)


def fmt_percent(value: float | None) -> str:
    return f"{(float(value or 0) * 100):.2f}%"


def parse_json_list(value: str | None) -> list[dict]:
    if not value:
        return []
    try:
        import json

        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def next_item_id(prefix: str, items: list[dict]) -> str:
    max_num = 0
    for item in items:
        import re
        match = re.search(r"\d+", str(item.get("id", "")))
        if match:
            max_num = max(max_num, int(match.group(0)))
    return f"{prefix}{max_num + 1}"


def pretty_status(value: str | None) -> str:
    raw = str(value or "").strip()
    if raw == "en_progreso":
        return "En progreso"
    if raw == "completada":
        return "Completada"
    return raw or "-"


def pretty_text(value: object, default: str = "-") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan", "nat"}:
        return default
    return text


def pretty_date(value: object) -> str:
    text = pretty_text(value, default="")
    if not text:
        return "-"
    try:
        parsed = pd.to_datetime(text, errors="coerce")
    except Exception:
        return text
    if pd.isna(parsed):
        return text
    return parsed.strftime("%d/%m/%Y")


def pretty_score(value: object) -> str:
    try:
        numeric = float(value)
    except Exception:
        return "-"
    if pd.isna(numeric):
        return "-"
    return fmt_percent(numeric)


def score_pill(value: object) -> str:
    return f'<span class="score-pill">{html.escape(pretty_score(value))}</span>'


def status_pill(value: object) -> str:
    label = pretty_status(value)
    raw = str(value or "").strip().lower().replace("_", "-")
    cls = "status-default"
    if raw == "completada":
        cls = "status-completada"
    elif raw == "en-progreso":
        cls = "status-en-progreso"
    return f'<span class="status-pill {cls}">{html.escape(label)}</span>'


def render_readonly_table(rows: list[dict[str, str]], columns: list[tuple[str, str]]) -> None:
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body_rows: list[str] = []
    for row in rows:
        cells = "".join(f"<td>{row.get(key, '-')}</td>" for key, _ in columns)
        body_rows.append(f"<tr>{cells}</tr>")
    body = "".join(body_rows) if body_rows else f"<tr><td colspan='{len(columns)}'>Sin datos.</td></tr>"
    st.markdown(
        f"""
        <div class="table-shell">
            <div class="readonly-table-wrap">
                <table class="readonly-table">
                    <thead><tr>{head}</tr></thead>
                    <tbody>{body}</tbody>
                </table>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_info_panel(items: list[tuple[str, str]]) -> None:
    cells = "".join(
        f'<div class="auditoria-info-item"><strong>{html.escape(label)}:</strong> {html.escape(value)}</div>'
        for label, value in items
    )
    st.markdown(f'<div class="auditoria-info-panel">{cells}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, sub: str = "", primary: bool = False) -> None:
    st.markdown(
        f"""
        <div class="metric-card {'metric-primary' if primary else ''}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def traffic_card(title: str, value: str, status: str) -> None:
    cls = "status-ok" if status == "Verde" else "status-warn" if status == "Amarillo" else "status-bad"
    st.markdown(
        f"""
        <div class="traffic-card">
            <div class="traffic-title">{title}</div>
            <div class="traffic-value">{value}</div>
            <span class="{cls}">{status}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mini_kpi_row(items: list[tuple[str, str]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        with col:
            st.markdown(
                (
                    '<div class="mini-kpi">'
                    f'<div class="mini-kpi-label">{label}</div>'
                    f'<div class="mini-kpi-value">{value}</div>'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )


def compute_dashboard_metrics(audits: list[dict]) -> dict[str, str]:
    if not audits:
        return {
            "total": "0",
            "ultimos30": "0",
            "cierre": "-",
            "promedio": "-",
            "mediana": "-",
            "desviacion": "-",
            "brecha": "-",
            "empresas": "-",
            "riesgo": "0",
            "backlog": "0",
            "completitud": "-",
            "concentracion": "-",
            "top_empresa": "-",
            "semaforo_cierre": "Sin datos",
            "semaforo_score": "Sin datos",
            "semaforo_riesgo": "Sin datos",
            "semaforo_cobertura": "Sin datos",
        }
    df = pd.DataFrame(audits)
    now = pd.Timestamp.utcnow()
    fechas = pd.to_datetime(df["fecha_realizacion"], errors="coerce", utc=True)
    total = len(df)
    ultimos30 = int(((now - fechas).dt.total_seconds() <= 30 * 24 * 60 * 60) .fillna(False).sum())
    cierre = f"{((df['estado'] == 'completada').sum() / total) * 100:.1f}%"
    scores = pd.to_numeric(df["score_final"], errors="coerce")
    con_score = scores.dropna()
    promedio_raw = con_score.mean() if not con_score.empty else None
    promedio = fmt_percent(promedio_raw) if promedio_raw is not None else "-"
    mediana_raw = con_score.median() if not con_score.empty else None
    mediana = fmt_percent(mediana_raw) if mediana_raw is not None else "-"
    desviacion = f"{(con_score.std(ddof=0) * 100):.2f} pp" if not con_score.empty else "-"
    brecha = f"{((con_score.max() - con_score.min()) * 100):.2f} pp" if not con_score.empty else "-"
    empresas = str(df["empresa"].fillna("-").nunique())
    riesgo_count = int(((scores < 0.65) | df["calificacion"].fillna("").astype(str).str.upper().str.contains("INS|NAD")).fillna(False).sum())
    riesgo = str(riesgo_count)
    antiguedad = (now - fechas).dt.total_seconds().fillna(31 * 24 * 60 * 60)
    backlog_count = int(((df["estado"] == "en_progreso") & ((scores < 0.65) | scores.isna()) & (antiguedad > 30 * 24 * 60 * 60)).sum())
    backlog = str(backlog_count)
    completitud_raw = (con_score.shape[0] / total) if total else None
    completitud = f"{(completitud_raw * 100):.1f}%" if completitud_raw is not None else "-"
    empresa_counts = df["empresa"].fillna("Sin empresa").astype(str).value_counts()
    top_empresa = empresa_counts.index[0] if not empresa_counts.empty else "-"
    concentracion = f"{((empresa_counts.iloc[0] / total) * 100):.1f}%" if not empresa_counts.empty else "-"

    cierre_raw = ((df["estado"] == "completada").sum() / total) if total else None
    cobertura_raw = (df["empresa"].fillna("").astype(str).replace("", pd.NA).dropna().nunique() / len(get_config()["empresas"])) if len(get_config()["empresas"]) else None
    riesgo_raw = (riesgo_count / total) if total else None

    def semaforo(value: float | None, ok: float, neutral: float, inverse: bool = False) -> str:
        if value is None:
            return "Sin datos"
        if inverse:
            if value <= ok:
                return "Verde"
            if value <= neutral:
                return "Amarillo"
            return "Rojo"
        if value >= ok:
            return "Verde"
        if value >= neutral:
            return "Amarillo"
        return "Rojo"

    return {
        "total": str(total),
        "ultimos30": str(ultimos30),
        "cierre": cierre,
        "promedio": promedio,
        "mediana": mediana,
        "desviacion": desviacion,
        "brecha": brecha,
        "empresas": empresas,
        "riesgo": riesgo,
        "backlog": backlog,
        "completitud": completitud,
        "concentracion": concentracion,
        "top_empresa": top_empresa,
        "semaforo_cierre": semaforo(cierre_raw, 0.70, 0.40),
        "semaforo_score": semaforo(promedio_raw, 0.85, 0.70),
        "semaforo_riesgo": semaforo(riesgo_raw, 0.10, 0.25, inverse=True),
        "semaforo_cobertura": semaforo(cobertura_raw, 0.90, 0.70),
    }


def build_report_payload(audit: dict) -> dict:
    controles = [item for item in audit.get("controles", []) if item.get("modulo_numero") in MODULOS_ACTIVOS]
    return {
        "auditoria": {
            "id": audit.get("id"),
            "codigo": audit.get("codigo"),
            "auditor": audit.get("auditor_nombre") or audit.get("auditor_id"),
            "empresa": audit.get("empresa"),
            "sucursal": audit.get("sucursal"),
            "fecha_realizacion": audit.get("fecha_realizacion"),
            "estado": audit.get("estado"),
            "score_final": audit.get("score_final"),
            "calificacion": audit.get("calificacion"),
        },
        "indicadores": [
            {
                "numero": control.get("modulo_numero"),
                "nombre": control.get("modulo_nombre"),
                "etapa": control.get("etapa"),
                "ponderacion": control.get("ponderacion"),
                "score_cumplimiento": control.get("score_cumplimiento"),
                "resultado_final": control.get("resultado_final"),
                "total_items": control.get("total_items"),
                "items_observacion": control.get("items_observacion"),
            }
            for control in controles
        ],
        "hallazgos": parse_json_list(audit.get("hallazgos")),
        "recomendaciones": parse_json_list(audit.get("recomendaciones")),
        "fecha_exportacion": datetime.utcnow().isoformat() + "Z",
    }


def build_report_html(audit: dict) -> str:
    payload = build_report_payload(audit)
    auditoria = payload["auditoria"]
    rows = "".join(
        f"<tr><td>{item['nombre']}</td><td>{item['etapa'] or '-'}</td><td>{fmt_percent(item['ponderacion'])}</td><td>{fmt_percent(item['score_cumplimiento'])}</td><td>{fmt_percent(item['resultado_final'])}</td></tr>"
        for item in payload["indicadores"]
    )
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Informe - {auditoria['codigo']}</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #1f2937; margin: 40px; }}
    h1 {{ color: #1e3a8a; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
    th {{ background: #eff6ff; }}
  </style>
</head>
<body>
  <h1>Control Integral de Deposito</h1>
  <p><strong>Auditoria:</strong> {auditoria['codigo']}</p>
  <p><strong>Empresa:</strong> {auditoria.get('empresa') or '-'}</p>
  <p><strong>Sucursal:</strong> {auditoria.get('sucursal') or '-'}</p>
  <p><strong>Auditor:</strong> {auditoria.get('auditor') or '-'}</p>
  <p><strong>Score:</strong> {fmt_percent(auditoria.get('score_final'))}</p>
  <p><strong>Calificacion:</strong> {auditoria.get('calificacion') or '-'}</p>
  <table>
    <thead>
      <tr><th>Modulo</th><th>Etapa</th><th>Ponderacion</th><th>% Cumplimiento</th><th>Resultado</th></tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>
    """.strip()


def render_sidebar(audits: list[dict]) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <h2>Control Integral</h2>
                <p>Grupo Cenoa</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sidebar-group-title">Auditor activo</div>', unsafe_allow_html=True)
        st.selectbox("Auditor activo", AUDITORES_DEFAULT, key="auditor_nombre")
        st.markdown('<div class="sidebar-group-title">Secciones</div>', unsafe_allow_html=True)
        sections = ["Dashboard", "Nueva Auditoria", "Configuracion", "Auditorias", "Informes", "Operacion"]
        for section in sections:
            if st.session_state["section"] == section:
                st.markdown(f'<div class="sidebar-nav-active">{html.escape(section)}</div>', unsafe_allow_html=True)
            else:
                if st.button(section, key=f"nav_{section}", use_container_width=True):
                    st.session_state["section"] = section
                    st.rerun()
        if audits:
            st.markdown('<div class="sidebar-group-title">Auditoria activa</div>', unsafe_allow_html=True)
            options = {
                f"{item['codigo']} | {item.get('empresa', '-')} | {item.get('sucursal', '-')}": item["id"]
                for item in audits
            }
            labels = list(options.keys())
            current = st.session_state.get("selected_audit_id")
            current_index = 0
            if current in options.values():
                current_index = list(options.values()).index(current)
            selected_label = st.selectbox("Auditoria activa", labels, index=current_index)
            st.session_state["selected_audit_id"] = options[selected_label]
        else:
            st.info("Sin auditorias activas.")
            selected_label = "Sin auditoria activa"
        st.markdown(
            f"""
            <div class="sidebar-footer">
                <div class="sidebar-session">
                    <div class="sidebar-session-label">Sesion</div>
                    <div class="sidebar-session-name">{html.escape(pretty_text(st.session_state['auditor_nombre']))}</div>
                    <div class="sidebar-audit">{html.escape(pretty_text(selected_label, default='Sin auditoria activa'))}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Base activa: {DB_DISPLAY}")


def render_header() -> None:
    st.markdown(
        f"""
        <div class="hero-card">
            <h1>Control Integral de Depositos</h1>
            <p>Auditor activo: {st.session_state['auditor_nombre']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(audits: list[dict]) -> None:
    st.markdown('<div class="section-title">Estado General</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Vista ejecutiva con indicadores principales del sistema.</div>', unsafe_allow_html=True)
    metrics = compute_dashboard_metrics(audits)
    cols = st.columns(4)
    with cols[0]:
        metric_card("Auditorias Totales", metrics["total"], "Base historica del tablero", primary=True)
    with cols[1]:
        metric_card("Ultimos 30 dias", metrics["ultimos30"], "Ritmo reciente de gestion", primary=True)
    with cols[2]:
        metric_card("% Cierre", metrics["cierre"], "Completadas sobre total", primary=True)
    with cols[3]:
        metric_card("Score Promedio", metrics["promedio"], "Rendimiento global ponderado", primary=True)
    cols = st.columns(4)
    with cols[0]:
        metric_card("Mediana Score", metrics["mediana"], "Comportamiento central")
    with cols[1]:
        metric_card("Desviacion", metrics["desviacion"], "Variabilidad entre auditorias")
    with cols[2]:
        metric_card("Brecha", metrics["brecha"], "Mejor vs peor score")
    with cols[3]:
        metric_card("Cobertura de Empresas", metrics["empresas"], "Empresas auditadas")
    cols = st.columns(4)
    with cols[0]:
        metric_card("Riesgo Alto", metrics["riesgo"], "Score menor a 65%")
    with cols[1]:
        metric_card("Backlog Critico", metrics["backlog"], "En progreso con bajo score")
    with cols[2]:
        metric_card("Completitud Score", metrics["completitud"], "Auditorias con score")
    with cols[3]:
        metric_card("Concentracion Empresa", metrics["concentracion"], metrics["top_empresa"])

    st.markdown('<div class="subsection-title">Semaforo Ejecutivo</div>', unsafe_allow_html=True)
    sem_cols = st.columns(4)
    with sem_cols[0]:
        traffic_card("Cierre Operativo", metrics["cierre"], metrics["semaforo_cierre"])
    with sem_cols[1]:
        traffic_card("Rendimiento Global", metrics["promedio"], metrics["semaforo_score"])
    with sem_cols[2]:
        traffic_card("Exposicion a Riesgo", metrics["riesgo"], metrics["semaforo_riesgo"])
    with sem_cols[3]:
        traffic_card("Cobertura Corporativa", metrics["empresas"], metrics["semaforo_cobertura"])

    if audits:
        st.markdown('<div class="subsection-title">Base de Auditorias</div>', unsafe_allow_html=True)
        df = pd.DataFrame(audits)
        rows = []
        for _, item in df.iterrows():
            rows.append(
                {
                    "codigo": f'<span class="cell-code">{html.escape(pretty_text(item.get("codigo")))}</span>',
                    "empresa": html.escape(pretty_text(item.get("empresa"))),
                    "sucursal": html.escape(pretty_text(item.get("sucursal"))),
                    "auditor_nombre": html.escape(pretty_text(item.get("auditor_nombre"))),
                    "estado": status_pill(item.get("estado")),
                    "score_final": score_pill(item.get("score_final")),
                    "calificacion": html.escape(pretty_text(item.get("calificacion"))),
                }
            )
        render_readonly_table(
            rows,
            [
                ("codigo", "Codigo"),
                ("empresa", "Empresa"),
                ("sucursal", "Sucursal"),
                ("auditor_nombre", "Auditor"),
                ("estado", "Estado"),
                ("score_final", "Score"),
                ("calificacion", "Calificacion"),
            ],
        )


def render_new_audit() -> None:
    st.markdown('<div class="section-title">Crear Nueva Auditoria</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Carga inicial de la auditoria con empresa, sucursal y fecha de realizacion.</div>', unsafe_allow_html=True)
    config = get_config()
    empresas = config["empresas"]
    selected_empresa = st.selectbox(
        "Empresa",
        empresas,
        index=empresas.index(config["empresa_default"]) if config["empresa_default"] in empresas else 0,
    )
    sucursales = config["sucursales_por_empresa"].get(selected_empresa, [])
    with st.form("crear_auditoria"):
        codigo = st.text_input("Codigo de auditoria")
        sucursal = st.selectbox("Sucursal", sucursales)
        fecha_realizacion = st.date_input("Fecha de realizacion", value=date.today())
        submitted = st.form_submit_button("Crear auditoria", use_container_width=True)
        if submitted:
            try:
                auditoria_id = create_audit(
                    codigo,
                    st.session_state["auditor_nombre"],
                    selected_empresa,
                    sucursal,
                    fecha_realizacion,
                )
                st.session_state["selected_audit_id"] = auditoria_id
                st.success("Auditoria creada correctamente.")
                st.rerun()
            except Exception as error:
                st.error(str(error))


def render_configuracion() -> None:
    st.markdown('<div class="section-title">Configuracion</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Gestiona ponderaciones, empresa por defecto y sucursales en una vista centralizada.</div>', unsafe_allow_html=True)
    config = get_config()
    empresas_text = st.text_area("Empresas", value="\n".join(config["empresas"]), height=120)
    empresas = [item.strip() for item in empresas_text.splitlines() if item.strip()]
    empresa_default = st.selectbox(
        "Empresa por defecto",
        empresas or config["empresas"],
        index=0 if not empresas else max(0, empresas.index(config["empresa_default"]) if config["empresa_default"] in empresas else 0),
    )

    st.markdown('<div class="subsection-title">Sucursales por Empresa</div>', unsafe_allow_html=True)
    sucursales_por_empresa: dict[str, list[str]] = {}
    for empresa in empresas or config["empresas"]:
        current = config["sucursales_por_empresa"].get(empresa, [])
        text_value = st.text_area(
            f"Sucursales - {empresa}",
            value="\n".join(current),
            height=110,
            key=f"suc_{empresa}",
        )
        sucursales_por_empresa[empresa] = [item.strip() for item in text_value.splitlines() if item.strip()]

    st.markdown('<div class="subsection-title">Ponderaciones</div>', unsafe_allow_html=True)
    ponderaciones: dict[str, float] = {}
    cols = st.columns(len(MODULOS_ACTIVOS))
    for index, modulo in enumerate(MODULOS_ACTIVOS):
        with cols[index]:
            ponderaciones[str(modulo)] = st.number_input(
                f"M{modulo}",
                min_value=0.0,
                max_value=100.0,
                value=float(config["ponderaciones"].get(str(modulo), PONDERACION_EQUIVALENTE) * 100),
                step=0.5,
                key=f"pond_{modulo}",
            )

    if st.button("Guardar configuracion", use_container_width=True):
        try:
            save_config(empresas or config["empresas"], empresa_default, sucursales_por_empresa, ponderaciones)
            st.success("Configuracion guardada.")
            st.rerun()
        except Exception as error:
            st.error(str(error))


def render_auditorias(audits: list[dict]) -> None:
    st.markdown('<div class="section-title">Auditorias</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Listado operativo de auditorias creadas y su estado actual.</div>', unsafe_allow_html=True)
    if not audits:
        st.info("Todavia no hay auditorias.")
        return
    df = pd.DataFrame(audits)
    mini_kpi_row([
        ("Total", str(len(df))),
        ("Completadas", str(int((df["estado"] == "completada").sum()))),
        ("En progreso", str(int((df["estado"] == "en_progreso").sum()))),
        ("Score promedio", fmt_percent(pd.to_numeric(df["score_final"], errors="coerce").fillna(0).mean())),
    ])
    rows = []
    for _, item in df.iterrows():
        rows.append(
            {
                "codigo": f'<span class="cell-code">{html.escape(pretty_text(item.get("codigo")))}</span>',
                "empresa": html.escape(pretty_text(item.get("empresa"))),
                "sucursal": html.escape(pretty_text(item.get("sucursal"))),
                "auditor_nombre": html.escape(pretty_text(item.get("auditor_nombre"))),
                "estado": status_pill(item.get("estado")),
                "score_final": score_pill(item.get("score_final")),
                "calificacion": html.escape(pretty_text(item.get("calificacion"))),
                "fecha_realizacion": html.escape(pretty_date(item.get("fecha_realizacion"))),
            }
        )
    render_readonly_table(
        rows,
        [
            ("codigo", "Codigo"),
            ("empresa", "Empresa"),
            ("sucursal", "Sucursal"),
            ("auditor_nombre", "Auditor"),
            ("estado", "Estado"),
            ("score_final", "Score"),
            ("calificacion", "Calificacion"),
            ("fecha_realizacion", "Fecha"),
        ],
    )


def render_informes() -> None:
    st.markdown('<div class="section-title">Informes</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Consulta de auditorias cerradas y descarga de reportes.</div>', unsafe_allow_html=True)
    reports = list_reports()
    if not reports:
        st.info("No hay auditorias cerradas todavia.")
        return
    df = pd.DataFrame(reports)
    mini_kpi_row([
        ("Informes", str(len(df))),
        ("Promedio", fmt_percent(pd.to_numeric(df["score_final"], errors="coerce").fillna(0).mean())),
        ("Hallazgos", str(sum(len(parse_json_list(item)) for item in df["hallazgos"].fillna("")))),
        ("Recomendaciones", str(sum(len(parse_json_list(item)) for item in df["recomendaciones"].fillna("")))),
    ])
    rows = []
    for _, item in df.iterrows():
        rows.append(
            {
                "codigo": f'<span class="cell-code">{html.escape(pretty_text(item.get("codigo")))}</span>',
                "empresa": html.escape(pretty_text(item.get("empresa"))),
                "sucursal": html.escape(pretty_text(item.get("sucursal"))),
                "auditor_nombre": html.escape(pretty_text(item.get("auditor_nombre"))),
                "fecha_cierre": html.escape(pretty_date(item.get("fecha_cierre"))),
                "score_final": score_pill(item.get("score_final")),
                "calificacion": html.escape(pretty_text(item.get("calificacion"))),
            }
        )
    render_readonly_table(
        rows,
        [
            ("codigo", "Codigo"),
            ("empresa", "Empresa"),
            ("sucursal", "Sucursal"),
            ("auditor_nombre", "Auditor"),
            ("fecha_cierre", "Cierre"),
            ("score_final", "Score"),
            ("calificacion", "Calificacion"),
        ],
    )

    options = {f"{item['codigo']} | {item.get('empresa', '-')} | {item.get('sucursal', '-')}": item["id"] for item in reports}
    selected = st.selectbox("Informe seleccionado", list(options.keys()), key="report_select")
    audit = get_audit(options[selected])
    payload = build_report_payload(audit)
    html_report = build_report_html(audit)
    import json

    col1, col2 = st.columns(2)
    col1.download_button(
        "Descargar JSON",
        data=json.dumps(payload, indent=2, ensure_ascii=False),
        file_name=f"Informe_{audit['codigo']}.json",
        mime="application/json",
        use_container_width=True,
    )
    col2.download_button(
        "Descargar HTML",
        data=html_report,
        file_name=f"Informe_{audit['codigo']}.html",
        mime="text/html",
        use_container_width=True,
    )


def render_manual_modules(audit: dict) -> None:
    st.markdown('<div class="subsection-title">Indicadores Manuales</div>', unsafe_allow_html=True)
    for control in audit["controles"]:
        if control["modulo_numero"] not in (3, 4, 7):
            continue
        with st.expander(control["modulo_nombre"]):
            col1, col2, col3 = st.columns(3)
            col1.metric("Ponderacion", fmt_percent(control.get("ponderacion")))
            col2.metric("% Cumplimiento", fmt_percent(control.get("score_cumplimiento")))
            col3.metric("Resultado", fmt_percent(control.get("resultado_final")))
            percent = st.number_input(
                "% de cumplimiento",
                min_value=0.0,
                max_value=100.0,
                value=float((control.get("score_cumplimiento") or 0) * 100),
                step=0.5,
                key=f"manual_score_{control['id']}",
            )
            if st.button("Guardar modulo", key=f"save_{control['id']}"):
                update_manual_control(control["id"], float(percent))
                st.success("Modulo actualizado.")
                st.rerun()


def render_transfer_section(audit: dict, modulo: int) -> None:
    st.markdown(f"<h3>{html.escape(MODULO_NOMBRES[modulo])}</h3>", unsafe_allow_html=True)
    st.markdown(
        '<div class="helper-text">Importa el Excel de transferencias pendientes para clasificar por sucursal destino.</div>',
        unsafe_allow_html=True,
    )
    uploader = st.file_uploader("Importar Excel", type=["xlsx", "xls"], key=f"up_transfer_{modulo}")
    if uploader and st.button("Procesar", key=f"process_transfer_{modulo}"):
        import_transferencias(audit["id"], audit["sucursal"], audit["fecha_realizacion"], uploader)
        st.success("Transferencias importadas.")
        st.rerun()
    df = fetch_table(
        """
        SELECT id, fecha_transferencia, numero_comprobante, sucursal_origen, sucursal_destino,
               dias_habiles, cumple_base, justificado, cumple_final, observacion
        FROM transferencias
        WHERE auditoria_id = ? AND modulo_numero = ?
        ORDER BY dias_habiles DESC, fecha_transferencia ASC
        """,
        (audit["id"], modulo),
    )
    if df.empty:
        st.caption("Sin registros importados.")
        return
    total = len(df)
    observadas = int((df["cumple_final"] == 0).sum())
    cumplen = total - observadas
    mini_kpi_row([
        ("Total", str(total)),
        ("Cumplen", str(cumplen)),
        ("No cumplen", str(observadas)),
        ("% Cumplimiento", fmt_percent(cumplen / total if total else 0)),
    ])
    edited = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        disabled=["id", "fecha_transferencia", "numero_comprobante", "sucursal_origen", "sucursal_destino", "dias_habiles", "cumple_base", "cumple_final"],
        key=f"transfer_editor_{modulo}",
        column_config={
            "fecha_transferencia": st.column_config.TextColumn("Fecha", width="small"),
            "numero_comprobante": st.column_config.TextColumn("Comprobante", width="small"),
            "sucursal_origen": st.column_config.TextColumn("Origen", width="medium"),
            "sucursal_destino": st.column_config.TextColumn("Destino", width="medium"),
            "dias_habiles": st.column_config.NumberColumn("Dias", width="small"),
            "justificado": st.column_config.CheckboxColumn(
                "Justificado",
                help="Solo aplica cuando la transferencia no cumple por dias habiles.",
            ),
            "observacion": st.column_config.TextColumn("Observacion", width="large"),
        },
    )
    if st.button("Guardar cambios", key=f"save_transfer_{modulo}"):
        save_transferencias_edits(audit["id"], modulo, edited)
        st.success("Transferencias actualizadas.")
        st.rerun()


def render_creditos_section(audit: dict) -> None:
    st.markdown(f"<h3>{html.escape(MODULO_NOMBRES[2])}</h3>", unsafe_allow_html=True)
    st.markdown(
        '<div class="helper-text">Importa la base de creditos pendientes y marca los reclamos asociados.</div>',
        unsafe_allow_html=True,
    )
    uploader = st.file_uploader("Importar Excel de creditos", type=["xlsx", "xls"], key="up_creditos")
    if uploader and st.button("Procesar creditos"):
        import_creditos(audit["id"], uploader)
        st.success("Creditos importados.")
        st.rerun()
    df = fetch_table(
        """
        SELECT id, fecha, articulo, numero_comprobante, sucursal_origen, sucursal_destino,
               cantidad, importe, tiene_reclamo, cumple_final, observacion
        FROM creditos_pendientes
        WHERE auditoria_id = ?
        ORDER BY fecha ASC, numero_comprobante ASC
        """,
        (audit["id"],),
    )
    if df.empty:
        st.caption("Sin registros importados.")
        return
    total = len(df)
    observadas = int((df["cumple_final"] == 0).sum())
    cumplen = total - observadas
    mini_kpi_row([
        ("Total", str(total)),
        ("Cumplen", str(cumplen)),
        ("No cumplen", str(observadas)),
        ("% Cumplimiento", fmt_percent(cumplen / total if total else 0)),
    ])
    edited = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        disabled=["id", "fecha", "articulo", "numero_comprobante", "sucursal_origen", "sucursal_destino", "cantidad", "importe", "cumple_final"],
        key="creditos_editor",
        column_config={
            "fecha": st.column_config.TextColumn("Fecha", width="small"),
            "articulo": st.column_config.TextColumn("Articulo", width="medium"),
            "numero_comprobante": st.column_config.TextColumn("Comprobante", width="small"),
            "cantidad": st.column_config.NumberColumn("Cantidad", width="small", format="%.2f"),
            "importe": st.column_config.NumberColumn("Importe", width="small", format="%.2f"),
            "tiene_reclamo": st.column_config.CheckboxColumn("Reclamo"),
            "observacion": st.column_config.TextColumn("Observacion", width="large"),
        },
    )
    if st.button("Guardar cambios creditos"):
        save_creditos_edits(audit["id"], edited)
        st.success("Creditos actualizados.")
        st.rerun()


def render_ventas_section(audit: dict) -> None:
    st.markdown(f"<h3>{html.escape(MODULO_NOMBRES[8])}</h3>", unsafe_allow_html=True)
    st.markdown(
        '<div class="helper-text">Trabaja sobre la muestra de comprobantes y valida firmas, justificación y observaciones.</div>',
        unsafe_allow_html=True,
    )
    uploader = st.file_uploader("Importar Excel de ventas internas", type=["xlsx", "xls"], key="up_ventas")
    if uploader and st.button("Procesar ventas internas"):
        import_ventas_internas(audit["id"], uploader)
        st.success("Ventas internas importadas.")
        st.rerun()
    df = fetch_table(
        """
        SELECT id, fecha, tipo_comprobante, numero_comprobante, articulo_codigo, articulo_descripcion,
               importe, en_muestra, firma_responsable_deposito, firma_gerente_sector,
               justificado, cumple_final, observacion
        FROM ventas_internas
        WHERE auditoria_id = ? AND en_muestra = 1
        ORDER BY fecha ASC, numero_comprobante ASC
        """,
        (audit["id"],),
    )
    if df.empty:
        st.caption("Sin muestra generada todavia.")
        return
    vta_mostrador_rows = df[df["tipo_comprobante"].map(is_mostrador_sale)].copy()
    total_comprobantes_vta_mostrador = int(vta_mostrador_rows["numero_comprobante"].fillna(vta_mostrador_rows["id"]).astype(str).nunique())
    total_comprobantes_muestra = int(vta_mostrador_rows[vta_mostrador_rows["en_muestra"] == 1]["numero_comprobante"].fillna(vta_mostrador_rows["id"]).astype(str).nunique()) if not vta_mostrador_rows.empty else 0
    grouped = (
        df.groupby("numero_comprobante", dropna=False)
        .agg(
            id=("id", "first"),
            fecha=("fecha", "first"),
            tipo_comprobante=("tipo_comprobante", "first"),
            imputacion_contable=("imputacion_contable", "first"),
            articulo_codigo=("articulo_codigo", lambda s: " | ".join([str(v) for v in s.fillna("") if str(v)])),
            articulo_descripcion=("articulo_descripcion", lambda s: " | ".join([str(v) for v in s.fillna("") if str(v)])),
            importe=("importe", "sum"),
            firma_responsable_deposito=("firma_responsable_deposito", "first"),
            firma_gerente_sector=("firma_gerente_sector", "first"),
            justificado=("justificado", "first"),
            cumple_final=("cumple_final", "max"),
            observacion=("observacion", "first"),
        )
        .reset_index()
    )
    total = len(grouped)
    observadas = int((grouped["cumple_final"] == 0).sum())
    cumplen = total - observadas
    mini_kpi_row([
        ("En muestra", str(total)),
        ("Cpbtes Vta. Mostrador", str(total_comprobantes_vta_mostrador)),
        ("Cpbtes en muestra", str(total_comprobantes_muestra)),
        ("Cumplen", str(cumplen)),
        ("No cumplen", str(observadas)),
        ("% Cumplimiento", fmt_percent(cumplen / total if total else 0)),
    ])
    export_rows = []
    for _, row in grouped.iterrows():
        export_rows.append(
            {
                "Fecha": pretty_date(row.get("fecha")),
                "Comprobante": pretty_text(row.get("tipo_comprobante")),
                "NumeroComprobante": pretty_text(row.get("numero_comprobante")),
                "Articulos": pretty_text(row.get("articulo_codigo"), "") + (" / " if pretty_text(row.get("articulo_codigo"), "") and pretty_text(row.get("articulo_descripcion"), "") else "") + pretty_text(row.get("articulo_descripcion"), ""),
                "ImputacionContable": pretty_text(row.get("imputacion_contable")),
                "ImporteTotalComprobante": float(row.get("importe") or 0),
                "FirmaDeposito": "Si" if bool(row.get("firma_responsable_deposito")) else "No",
                "FirmaGerenteJefe": "Si" if bool(row.get("firma_gerente_sector")) else "No",
                "Justificado": "Si" if bool(row.get("justificado")) else "No",
                "Cumple": "Si cumple" if int(row.get("cumple_final", 0)) == 1 else "No cumple",
                "Observacion": pretty_text(row.get("observacion"), ""),
            }
        )
    if export_rows:
        export_df = pd.DataFrame(export_rows)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            export_df.to_excel(writer, index=False, sheet_name="Muestra Ventas Internas")
        st.download_button(
            "Descargar muestra",
            data=buffer.getvalue(),
            file_name=f"muestra_ventas_internas_{audit['codigo']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    edited = st.data_editor(
        grouped,
        use_container_width=True,
        hide_index=True,
        disabled=["id", "fecha", "tipo_comprobante", "numero_comprobante", "articulo_codigo", "articulo_descripcion", "imputacion_contable", "importe", "cumple_final"],
        key="ventas_editor",
        column_config={
            "fecha": st.column_config.TextColumn("Fecha", width="small"),
            "tipo_comprobante": st.column_config.TextColumn("Comprobante", width="small"),
            "numero_comprobante": st.column_config.TextColumn("Numero", width="small"),
            "articulo_codigo": st.column_config.TextColumn("Codigos", width="medium"),
            "articulo_descripcion": st.column_config.TextColumn("Articulos", width="large"),
            "imputacion_contable": st.column_config.TextColumn("Imputacion", width="medium"),
            "importe": st.column_config.NumberColumn("Importe", width="small", format="%.2f"),
            "firma_responsable_deposito": st.column_config.CheckboxColumn("Firma deposito"),
            "firma_gerente_sector": st.column_config.CheckboxColumn("Firma gerente"),
            "justificado": st.column_config.CheckboxColumn("Justificado"),
            "observacion": st.column_config.TextColumn("Observacion", width="large"),
        },
    )
    if st.button("Guardar cambios ventas internas"):
        save_ventas_edits(audit["id"], edited)
        st.success("Ventas internas actualizadas.")
        st.rerun()


def render_close_section(audit: dict) -> None:
    controles = [item for item in audit["controles"] if item["modulo_numero"] in MODULOS_ACTIVOS]
    faltantes = [item["modulo_nombre"] for item in controles if pd.isna(item.get("score_cumplimiento"))]
    read_only = audit.get("estado") == "completada"
    hallazgo_state_key = f"close_hallazgos_{audit['id']}"
    recomendacion_state_key = f"close_recomendaciones_{audit['id']}"
    if hallazgo_state_key not in st.session_state:
        hallazgos_prev = parse_json_list(audit.get("hallazgos"))
        st.session_state[hallazgo_state_key] = hallazgos_prev or [{
            "id": "H1",
            "indicador": str(controles[0]["modulo_numero"]) if controles else "",
            "gravedad": "media",
            "descripcion": "",
        }]
    if recomendacion_state_key not in st.session_state:
        recomendaciones_prev = parse_json_list(audit.get("recomendaciones"))
        st.session_state[recomendacion_state_key] = recomendaciones_prev or [{
            "id": "R1",
            "hallazgoId": st.session_state[hallazgo_state_key][0]["id"] if st.session_state[hallazgo_state_key] else "H1",
            "descripcion": "",
        }]
    hallazgos_state = st.session_state[hallazgo_state_key]
    recomendaciones_state = st.session_state[recomendacion_state_key]
    rows = []
    for control in controles:
        rows.append(
            {
                "modulo": f"<strong>{html.escape(pretty_text(control.get('modulo_nombre')))}</strong>",
                "etapa": html.escape(pretty_text(control.get("etapa"))),
                "ponderacion": html.escape(pretty_score(control.get("ponderacion"))),
                "score": html.escape(pretty_score(control.get("score_cumplimiento"))),
                "resultado": html.escape(pretty_score(control.get("resultado_final"))),
            }
        )
    render_readonly_table(
        rows,
        [
            ("modulo", "Indicador"),
            ("etapa", "Etapa"),
            ("ponderacion", "Ponderacion"),
            ("score", "% Cumplimiento"),
            ("resultado", "Aporte Final"),
        ],
    )
    st.markdown(
        f"""
        <div class="total-card-grid">
            <div class="total-card">
                <h4>Score Final</h4>
                <p class="score-value">{html.escape(pretty_score(audit.get("score_final")))}</p>
            </div>
            <div class="total-card">
                <h4>Calificacion</h4>
                <p class="calificacion-value">{html.escape(pretty_text(audit.get("calificacion")))}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="resumen-cierre"><h3>Cierre de Auditoria</h3><div class="helper-text">Se habilita cuando todos los indicadores tienen su % de cumplimiento guardado.</div></div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="resumen-cierre-panel"><h4>Hallazgos</h4></div>', unsafe_allow_html=True)
        if not read_only and st.button("Agregar nuevo hallazgo", key=f"add_hallazgo_{audit['id']}"):
            hallazgos_state.append({
                "id": next_item_id("H", hallazgos_state),
                "indicador": str(controles[0]["modulo_numero"]) if controles else "",
                "gravedad": "media",
                "descripcion": "",
            })
            st.rerun()
        for index, hallazgo in enumerate(hallazgos_state):
            st.markdown(f"**Hallazgo {index + 1}**")
            h1, h2 = st.columns(2)
            hallazgo["id"] = h1.text_input("ID hallazgo", value=str(hallazgo.get("id", f"H{index+1}")), key=f"hallazgo_id_{audit['id']}_{index}", disabled=read_only)
            indicador_options = [str(item["modulo_numero"]) for item in controles]
            hallazgo["indicador"] = h2.selectbox(
                "Indicador de referencia",
                indicador_options,
                index=max(0, indicador_options.index(str(hallazgo.get("indicador"))) if indicador_options and str(hallazgo.get("indicador")) in indicador_options else 0),
                key=f"hallazgo_indicador_{audit['id']}_{index}",
                disabled=read_only,
            ) if controles else ""
            hallazgo["gravedad"] = st.selectbox(
                "Gravedad",
                ["alta", "media", "baja"],
                index=["alta", "media", "baja"].index(str(hallazgo.get("gravedad", "media")).lower()) if str(hallazgo.get("gravedad", "media")).lower() in ["alta", "media", "baja"] else 1,
                key=f"hallazgo_gravedad_{audit['id']}_{index}",
                disabled=read_only,
            )
            hallazgo["descripcion"] = st.text_area(
                "Descripcion del hallazgo",
                value=str(hallazgo.get("descripcion", "")),
                height=120,
                key=f"hallazgo_desc_{audit['id']}_{index}",
                disabled=read_only,
            ).strip()
            if not read_only and len(hallazgos_state) > 1 and st.button("Eliminar hallazgo", key=f"del_hallazgo_{audit['id']}_{index}"):
                removed = hallazgos_state.pop(index)
                recomendaciones_state[:] = [r for r in recomendaciones_state if str(r.get("hallazgoId")) != str(removed.get("id"))]
                st.rerun()
    with right:
        st.markdown('<div class="resumen-cierre-panel"><h4>Recomendaciones</h4></div>', unsafe_allow_html=True)
        if not read_only and st.button("Agregar recomendacion", key=f"add_recomendacion_{audit['id']}"):
            if not hallazgos_state:
                st.warning("Primero agrega un hallazgo para poder asociar una recomendacion.")
            else:
                recomendaciones_state.append({
                    "id": next_item_id("R", recomendaciones_state),
                    "hallazgoId": str(hallazgos_state[0].get("id", "H1")),
                    "descripcion": "",
                })
                st.rerun()
        hallazgo_ids = [str(item.get("id", "")).strip() for item in hallazgos_state if str(item.get("id", "")).strip()]
        for index, recomendacion in enumerate(recomendaciones_state):
            st.markdown(f"**Recomendacion {index + 1}**")
            r1, r2 = st.columns(2)
            recomendacion["id"] = r1.text_input("ID recomendacion", value=str(recomendacion.get("id", f"R{index+1}")), key=f"rec_id_{audit['id']}_{index}", disabled=read_only)
            recomendacion["hallazgoId"] = r2.selectbox(
                "Hallazgo de referencia",
                hallazgo_ids or ["H1"],
                index=max(0, (hallazgo_ids or ["H1"]).index(str(recomendacion.get("hallazgoId"))) if str(recomendacion.get("hallazgoId")) in (hallazgo_ids or ["H1"]) else 0),
                key=f"rec_hallazgo_{audit['id']}_{index}",
                disabled=read_only,
            )
            recomendacion["descripcion"] = st.text_area(
                "Descripcion de la recomendacion",
                value=str(recomendacion.get("descripcion", "")),
                height=120,
                key=f"rec_desc_{audit['id']}_{index}",
                disabled=read_only,
            ).strip()
            if not read_only and len(recomendaciones_state) > 1 and st.button("Eliminar recomendacion", key=f"del_rec_{audit['id']}_{index}"):
                recomendaciones_state.pop(index)
                st.rerun()
    hallazgos_payload = [
        {
            "id": str(item.get("id", "")).strip(),
            "indicador": str(item.get("indicador", "")).strip(),
            "gravedad": str(item.get("gravedad", "")).strip().lower(),
            "descripcion": str(item.get("descripcion", "")).strip(),
        }
        for item in hallazgos_state
    ]
    hallazgos_validos = [
        item for item in hallazgos_payload
        if item["id"] and item["indicador"] and item["gravedad"] in {"alta", "media", "baja"} and item["descripcion"]
    ]
    hallazgo_ids_validos = {item["id"] for item in hallazgos_validos}
    recomendaciones_payload = [
        {
            "id": str(item.get("id", "")).strip(),
            "hallazgoId": str(item.get("hallazgoId", "")).strip(),
            "descripcion": str(item.get("descripcion", "")).strip(),
        }
        for item in recomendaciones_state
    ]
    recomendaciones_validas = [
        item for item in recomendaciones_payload
        if item["id"] and item["hallazgoId"] in hallazgo_ids_validos and item["descripcion"]
    ]
    hallazgo_ok = len(hallazgos_validos) > 0
    recomendacion_ok = len(recomendaciones_validas) > 0
    checklist = [
        ("Indicadores completos", not faltantes),
        ("Hallazgos completos", hallazgo_ok),
        ("Recomendaciones completas", recomendacion_ok),
    ]
    checklist_html = "".join(
        f"<li>{'OK' if ok else 'Pendiente'} - {html.escape(label)}</li>" for label, ok in checklist
    )
    st.markdown(f'<div class="cierre-note info"><strong>Checklist de cierre</strong><ul>{checklist_html}</ul></div>', unsafe_allow_html=True)
    if faltantes or not hallazgo_ok or not recomendacion_ok:
        motivos = []
        if faltantes:
            motivos.append(f"Faltan % de cumplimiento en: {', '.join(faltantes)}")
        if not hallazgo_ok:
            motivos.append("Debes cargar un hallazgo completo.")
        if not recomendacion_ok:
            motivos.append("Debes cargar una recomendacion valida vinculada al hallazgo.")
        motivos_html = "".join(f"<li>{html.escape(item)}</li>" for item in motivos)
        st.markdown(f'<div class="cierre-note warn"><strong>Motivos de bloqueo</strong><ul>{motivos_html}</ul></div>', unsafe_allow_html=True)
    import json
    save1, save2 = st.columns(2)
    if save1.button("Guardar hallazgos y recomendaciones", use_container_width=True, disabled=read_only):
        save_close_draft(
            audit["id"],
            json.dumps(hallazgos_payload, ensure_ascii=True),
            json.dumps(recomendaciones_payload, ensure_ascii=True),
        )
        st.success("Borrador guardado correctamente.")
        st.rerun()
    if save2.button("Cerrar auditoria", type="primary", use_container_width=True, disabled=bool(read_only or faltantes or not hallazgo_ok or not recomendacion_ok)):
        import json

        close_audit(
            audit["id"],
            json.dumps(hallazgos_payload, ensure_ascii=True),
            json.dumps(recomendaciones_payload, ensure_ascii=True),
        )
        st.success("Auditoria cerrada correctamente.")
        st.rerun()


def render_operacion(audits: list[dict]) -> None:
    audit_id = st.session_state.get("selected_audit_id")
    if not audit_id and audits:
        audit_id = audits[0]["id"]
        st.session_state["selected_audit_id"] = audit_id
    if not audit_id:
        st.info("Crea una auditoria para empezar.")
        return

    audit = get_audit(audit_id)
    st.markdown(
        f"""
        <div class="indicator-header">
            <div>
                <h2>Pantallas por Indicador</h2>
                <p>{html.escape(pretty_text(audit.get('codigo')))} | {html.escape(pretty_text(audit.get('empresa')))} | {html.escape(pretty_text(audit.get('sucursal')))}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_info_panel(
        [
            ("Auditor", pretty_text(audit.get("auditor_nombre") or audit.get("auditor_id"))),
            ("Sucursal", pretty_text(audit.get("sucursal"))),
            ("Fecha", pretty_date(audit.get("fecha_realizacion"))),
            ("Estado", pretty_status(audit.get("estado"))),
            ("Score final", pretty_score(audit.get("score_final"))),
            ("Calificacion", pretty_text(audit.get("calificacion"))),
        ]
    )
    controles_df = pd.DataFrame(audit["controles"])[
        ["modulo_numero", "modulo_nombre", "etapa", "ponderacion", "score_cumplimiento", "resultado_final", "total_items", "items_observacion"]
    ].copy()
    mini_kpi_row([
        ("Empresa", str(audit.get("empresa") or "-")),
        ("Sucursal", str(audit.get("sucursal") or "-")),
        ("Fecha", pretty_date(audit.get("fecha_realizacion"))),
        ("Modulos", str(len([item for item in audit["controles"] if item["modulo_numero"] in MODULOS_ACTIVOS]))),
    ])
    payload = build_report_payload(audit)
    html_report = build_report_html(audit)
    import json

    d1, d2 = st.columns(2)
    d1.download_button(
        "Descargar informe JSON",
        data=json.dumps(payload, indent=2, ensure_ascii=False),
        file_name=f"Informe_{audit['codigo']}.json",
        mime="application/json",
        use_container_width=True,
    )
    d2.download_button(
        "Descargar informe HTML",
        data=html_report,
        file_name=f"Informe_{audit['codigo']}.html",
        mime="text/html",
        use_container_width=True,
    )
    nav_col, content_col = st.columns([1, 4])
    module_options = [
        (1, "Indicador 1"),
        (2, "Indicador 2"),
        (3, "Indicador 3"),
        (4, "Indicador 4"),
        (7, "Indicador 5"),
        (8, "Indicador 6"),
        (9, "Indicador 7"),
        ("resumen", "Resumen"),
    ]
    with nav_col:
        for module_value, label in module_options:
            if st.session_state.get("operation_module") == module_value:
                st.markdown(f'<div class="indicator-nav-active">{html.escape(label)}</div>', unsafe_allow_html=True)
            else:
                if st.button(label, key=f"operation_module_{module_value}", use_container_width=True):
                    st.session_state["operation_module"] = module_value
                    st.rerun()
    with content_col:
        st.markdown('<div class="indicator-screen-card">', unsafe_allow_html=True)
        active_module = st.session_state.get("operation_module", 1)
        if active_module == 1:
            render_transfer_section(audit, 1)
        elif active_module == 2:
            render_creditos_section(audit)
        elif active_module in (3, 4, 7):
            control = next((item for item in audit["controles"] if item["modulo_numero"] == active_module), None)
            if control:
                st.markdown(f"<h3>{html.escape(control['modulo_nombre'])}</h3>", unsafe_allow_html=True)
                st.markdown('<div class="helper-text">Carga el porcentaje de cumplimiento parametrizado para este indicador manual.</div>', unsafe_allow_html=True)
                summary_cols = st.columns(3)
                summary_cols[0].markdown(f'<div class="summary-card"><span>Ponderacion</span><strong>{html.escape(fmt_percent(control.get("ponderacion")))}</strong></div>', unsafe_allow_html=True)
                summary_cols[1].markdown(f'<div class="summary-card"><span>% Cumplimiento</span><strong>{html.escape(fmt_percent(control.get("score_cumplimiento")))}</strong></div>', unsafe_allow_html=True)
                summary_cols[2].markdown(f'<div class="summary-card"><span>Resultado</span><strong>{html.escape(fmt_percent(control.get("resultado_final")))}</strong></div>', unsafe_allow_html=True)
                percent = st.number_input(
                    "% de cumplimiento",
                    min_value=0.0,
                    max_value=100.0,
                    value=float((control.get("score_cumplimiento") or 0) * 100),
                    step=0.5,
                    key=f"manual_score_{control['id']}",
                )
                if st.button("Guardar modulo", key=f"save_{control['id']}"):
                    update_manual_control(control["id"], float(percent))
                    st.success("Modulo actualizado.")
                    st.rerun()
        elif active_module == 8:
            render_ventas_section(audit)
        elif active_module == 9:
            render_transfer_section(audit, 9)
        else:
            st.markdown("<h3>Resumen de Auditoria</h3>", unsafe_allow_html=True)
            st.markdown('<div class="helper-text">Desglose por indicador, hallazgos, recomendaciones y cierre operativo.</div>', unsafe_allow_html=True)
            render_close_section(audit)
        st.markdown('</div>', unsafe_allow_html=True)


def main() -> None:
    inject_styles()
    init_state()
    audits = list_audits()
    render_sidebar(audits)
    render_header()
    st.write("")

    section = st.session_state["section"]
    if section == "Dashboard":
        render_dashboard(audits)
    elif section == "Nueva Auditoria":
        render_new_audit()
    elif section == "Configuracion":
        render_configuracion()
    elif section == "Auditorias":
        render_auditorias(audits)
    elif section == "Informes":
        render_informes()
    else:
        render_operacion(audits)


main()
