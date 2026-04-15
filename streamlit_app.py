from __future__ import annotations

from datetime import date, datetime

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
        [data-testid="stSidebar"] * { color: #eef4ff; }
        [data-testid="stSidebar"] .stRadio > label,
        [data-testid="stSidebar"] .stSelectbox > label {
            color: #c7d3f8 !important;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: .08em;
            font-weight: 700;
        }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
            border: 1px solid rgba(255,255,255,0.18);
            background: rgba(255,255,255,0.05);
            padding: 8px 10px;
            border-radius: 10px;
            margin-bottom: 8px;
        }
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(199, 210, 254, 0.35);
            border-radius: 10px;
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
        .mini-kpi-grid {
            display:grid;
            grid-template-columns: repeat(auto-fit,minmax(160px,1fr));
            gap:12px;
            margin-bottom:12px;
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
        .stButton > button, .stDownloadButton > button {
            border-radius: 11px !important;
            font-weight: 700 !important;
            border: 1px solid transparent !important;
        }
        .stButton > button[kind="primary"], .stDownloadButton > button {
            background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
            color: white !important;
            box-shadow: 0 8px 20px rgba(79,70,229,.22);
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
    cards = "".join(
        f"""
        <div class="mini-kpi">
            <div class="mini-kpi-label">{label}</div>
            <div class="mini-kpi-value">{value}</div>
        </div>
        """
        for label, value in items
    )
    st.markdown(f'<div class="mini-kpi-grid">{cards}</div>', unsafe_allow_html=True)


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
        st.markdown("## Control Integral")
        st.caption("Grupo Cenoa")
        st.selectbox("Auditor activo", AUDITORES_DEFAULT, key="auditor_nombre")
        st.session_state["section"] = st.radio(
            "Secciones",
            ["Dashboard", "Nueva Auditoria", "Configuracion", "Auditorias", "Informes", "Operacion"],
            index=["Dashboard", "Nueva Auditoria", "Configuracion", "Auditorias", "Informes", "Operacion"].index(
                st.session_state["section"]
            ),
        )
        if audits:
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
        st.markdown(
            f"""
            <div class="surface-card" style="background:rgba(255,255,255,.08); border-color:rgba(255,255,255,.14); padding:12px 14px;">
                <div style="font-size:12px; color:#c7d3f8; text-transform:uppercase; letter-spacing:.08em; font-weight:700;">Sesion</div>
                <div style="font-size:14px; color:#fff; font-weight:700; margin-top:6px;">{st.session_state['auditor_nombre']}</div>
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
        visible = df[["codigo", "empresa", "sucursal", "auditor_nombre", "estado", "score_final", "calificacion"]].copy()
        visible["score_final"] = visible["score_final"].map(fmt_percent)
        st.dataframe(visible, use_container_width=True, hide_index=True)


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
    visible = df[["codigo", "empresa", "sucursal", "auditor_nombre", "estado", "score_final", "calificacion", "fecha_realizacion"]].copy()
    visible["score_final"] = visible["score_final"].map(fmt_percent)
    st.markdown('<div class="table-shell">', unsafe_allow_html=True)
    st.dataframe(
        visible,
        use_container_width=True,
        hide_index=True,
        column_config={
            "codigo": st.column_config.TextColumn("Codigo", width="small"),
            "empresa": st.column_config.TextColumn("Empresa", width="medium"),
            "sucursal": st.column_config.TextColumn("Sucursal", width="medium"),
            "auditor_nombre": st.column_config.TextColumn("Auditor", width="medium"),
            "estado": st.column_config.TextColumn("Estado", width="small"),
            "score_final": st.column_config.TextColumn("Score", width="small"),
            "calificacion": st.column_config.TextColumn("Calificacion", width="medium"),
            "fecha_realizacion": st.column_config.TextColumn("Fecha", width="small"),
        },
    )
    st.markdown('</div>', unsafe_allow_html=True)


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
    visible = df[["codigo", "empresa", "sucursal", "auditor_nombre", "fecha_cierre", "score_final", "calificacion"]].copy()
    visible["score_final"] = visible["score_final"].map(fmt_percent)
    st.markdown('<div class="table-shell">', unsafe_allow_html=True)
    st.dataframe(
        visible,
        use_container_width=True,
        hide_index=True,
        column_config={
            "codigo": st.column_config.TextColumn("Codigo", width="small"),
            "empresa": st.column_config.TextColumn("Empresa", width="medium"),
            "sucursal": st.column_config.TextColumn("Sucursal", width="medium"),
            "auditor_nombre": st.column_config.TextColumn("Auditor", width="medium"),
            "fecha_cierre": st.column_config.TextColumn("Cierre", width="small"),
            "score_final": st.column_config.TextColumn("Score", width="small"),
            "calificacion": st.column_config.TextColumn("Calificacion", width="medium"),
        },
    )
    st.markdown('</div>', unsafe_allow_html=True)

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
    with st.expander(MODULO_NOMBRES[modulo], expanded=modulo == 1):
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
    with st.expander(MODULO_NOMBRES[2], expanded=True):
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
    with st.expander(MODULO_NOMBRES[8], expanded=True):
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
        grouped = (
            df.groupby("numero_comprobante", dropna=False)
            .agg(
                id=("id", "first"),
                fecha=("fecha", "first"),
                tipo_comprobante=("tipo_comprobante", "first"),
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
            ("Cumplen", str(cumplen)),
            ("No cumplen", str(observadas)),
            ("% Cumplimiento", fmt_percent(cumplen / total if total else 0)),
        ])
        edited = st.data_editor(
            grouped,
            use_container_width=True,
            hide_index=True,
            disabled=["id", "fecha", "tipo_comprobante", "numero_comprobante", "articulo_codigo", "articulo_descripcion", "importe", "cumple_final"],
            key="ventas_editor",
            column_config={
                "fecha": st.column_config.TextColumn("Fecha", width="small"),
                "tipo_comprobante": st.column_config.TextColumn("Comprobante", width="small"),
                "numero_comprobante": st.column_config.TextColumn("Numero", width="small"),
                "articulo_codigo": st.column_config.TextColumn("Codigos", width="medium"),
                "articulo_descripcion": st.column_config.TextColumn("Articulos", width="large"),
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
    st.markdown('<div class="subsection-title">Resumen y Cierre</div>', unsafe_allow_html=True)
    controles = [item for item in audit["controles"] if item["modulo_numero"] in MODULOS_ACTIVOS]
    faltantes = [item["modulo_nombre"] for item in controles if pd.isna(item.get("score_cumplimiento"))]
    hallazgos_prev = parse_json_list(audit.get("hallazgos"))
    recomendaciones_prev = parse_json_list(audit.get("recomendaciones"))
    hallazgo_default = hallazgos_prev[0] if hallazgos_prev else {"id": "H1", "indicador": str(controles[0]["modulo_numero"]) if controles else "", "gravedad": "media", "descripcion": ""}
    recomendacion_default = recomendaciones_prev[0] if recomendaciones_prev else {"id": "R1", "hallazgoId": hallazgo_default["id"], "descripcion": ""}

    if faltantes:
        st.warning(f"Faltan % de cumplimiento en: {', '.join(faltantes)}")

    st.markdown("#### Hallazgo")
    h1, h2 = st.columns(2)
    hallazgo_id = h1.text_input("ID hallazgo", value=str(hallazgo_default.get("id", "H1")))
    indicador = h2.selectbox(
        "Indicador de referencia",
        [str(item["modulo_numero"]) for item in controles],
        index=max(0, [str(item["modulo_numero"]) for item in controles].index(str(hallazgo_default.get("indicador"))) if controles and str(hallazgo_default.get("indicador")) in [str(item["modulo_numero"]) for item in controles] else 0),
    ) if controles else ""
    gravedad = st.selectbox("Gravedad", ["alta", "media", "baja"], index=["alta", "media", "baja"].index(str(hallazgo_default.get("gravedad", "media")).lower()) if str(hallazgo_default.get("gravedad", "media")).lower() in ["alta", "media", "baja"] else 1)
    hallazgo_desc = st.text_area("Descripcion del hallazgo", value=str(hallazgo_default.get("descripcion", "")), height=120)

    st.markdown("#### Recomendacion")
    r1, r2 = st.columns(2)
    recomendacion_id = r1.text_input("ID recomendacion", value=str(recomendacion_default.get("id", "R1")))
    hallazgo_ref = r2.text_input("Hallazgo de referencia", value=str(recomendacion_default.get("hallazgoId", hallazgo_id or "H1")))
    recomendacion_desc = st.text_area("Descripcion de la recomendacion", value=str(recomendacion_default.get("descripcion", "")), height=120)

    hallazgos_payload = [
        {
            "id": hallazgo_id.strip(),
            "indicador": str(indicador).strip(),
            "gravedad": str(gravedad).strip().lower(),
            "descripcion": hallazgo_desc.strip(),
        }
    ]
    recomendaciones_payload = [
        {
            "id": recomendacion_id.strip(),
            "hallazgoId": hallazgo_ref.strip(),
            "descripcion": recomendacion_desc.strip(),
        }
    ]
    hallazgo_ok = all(hallazgos_payload[0].values())
    recomendacion_ok = all(recomendaciones_payload[0].values()) and recomendaciones_payload[0]["hallazgoId"] == hallazgos_payload[0]["id"]
    checklist_cols = st.columns(3)
    checklist_cols[0].markdown("`OK` Indicadores completos" if not faltantes else "`Pendiente` Indicadores completos")
    checklist_cols[1].markdown("`OK` Hallazgo completo" if hallazgo_ok else "`Pendiente` Hallazgo completo")
    checklist_cols[2].markdown("`OK` Recomendacion completa" if recomendacion_ok else "`Pendiente` Recomendacion completa")

    if st.button("Cerrar auditoria", type="primary", use_container_width=True):
        import json

        close_audit(
            audit["id"],
            json.dumps(hallazgos_payload, ensure_ascii=True),
            json.dumps(recomendaciones_payload, ensure_ascii=True),
        )
        st.success("Auditoria cerrada correctamente.")
        st.rerun()


def render_operacion(audits: list[dict]) -> None:
    st.markdown('<div class="section-title">Operacion</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Carga de indicadores, seguimiento y cierre de la auditoria activa.</div>', unsafe_allow_html=True)
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
        <span class="audit-chip">{audit['codigo']}</span>
        <span class="audit-chip">{audit.get('empresa', '-')}</span>
        <span class="audit-chip">{audit.get('sucursal', '-')}</span>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Estado", audit["estado"])
    col2.metric("Score", fmt_percent(audit.get("score_final")))
    col3.metric("Calificacion", audit.get("calificacion") or "-")
    col4.metric("Auditor", audit.get("auditor_nombre") or audit.get("auditor_id") or "-")

    mini_kpi_row([
        ("Empresa", str(audit.get("empresa") or "-")),
        ("Sucursal", str(audit.get("sucursal") or "-")),
        ("Fecha", str(audit.get("fecha_realizacion") or "-")[:10]),
        ("Modulos", str(len([item for item in audit["controles"] if item["modulo_numero"] in MODULOS_ACTIVOS]))),
    ])

    controles_df = pd.DataFrame(audit["controles"])[
        ["modulo_numero", "modulo_nombre", "etapa", "ponderacion", "score_cumplimiento", "resultado_final", "total_items", "items_observacion"]
    ].copy()
    controles_df["ponderacion"] = controles_df["ponderacion"].map(fmt_percent)
    controles_df["score_cumplimiento"] = controles_df["score_cumplimiento"].map(fmt_percent)
    controles_df["resultado_final"] = controles_df["resultado_final"].map(fmt_percent)
    st.markdown('<div class="subsection-title">Tablero de Resultados</div>', unsafe_allow_html=True)
    st.markdown('<div class="table-shell">', unsafe_allow_html=True)
    st.dataframe(
        controles_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "modulo_numero": st.column_config.NumberColumn("#", width="small"),
            "modulo_nombre": st.column_config.TextColumn("Modulo", width="medium"),
            "etapa": st.column_config.TextColumn("Etapa", width="small"),
            "ponderacion": st.column_config.TextColumn("Ponderacion", width="small"),
            "score_cumplimiento": st.column_config.TextColumn("% Cumplimiento", width="small"),
            "resultado_final": st.column_config.TextColumn("Resultado", width="small"),
            "total_items": st.column_config.NumberColumn("Total", width="small"),
            "items_observacion": st.column_config.NumberColumn("Observados", width="small"),
        },
    )
    st.markdown('</div>', unsafe_allow_html=True)

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

    render_transfer_section(audit, 1)
    render_creditos_section(audit)
    render_manual_modules(audit)
    render_ventas_section(audit)
    render_transfer_section(audit, 9)
    render_close_section(audit)


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
