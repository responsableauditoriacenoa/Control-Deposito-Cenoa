from __future__ import annotations

from datetime import date

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
        .stApp { background: linear-gradient(180deg,#eef3fb 0%,#f7f9fc 100%); }
        [data-testid="stSidebar"] { background: linear-gradient(180deg,#0c1739 0%,#13275f 100%); }
        [data-testid="stSidebar"] * { color: #eef4ff; }
        .hero-card, .metric-card, .table-card {
            background: white; border: 1px solid #dbe4f2; border-radius: 18px; padding: 18px 20px;
            box-shadow: 0 10px 24px rgba(15,23,42,.06);
        }
        .hero-card { background: linear-gradient(135deg,#182968 0%,#3048a4 100%); color: white; border: none; }
        .hero-card h1, .hero-card p { color: white; margin: 0; }
        .metric-label { font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: .08em; }
        .metric-value { font-size: 32px; font-weight: 800; color: #0f172a; margin-top: 8px; }
        .metric-sub { font-size: 13px; color: #64748b; margin-top: 6px; }
        .section-title { font-size: 26px; font-weight: 800; color: #0f172a; margin-bottom: 8px; }
        .section-copy { color: #475569; margin-bottom: 14px; }
        .audit-chip {
            display:inline-block; padding:8px 12px; border-radius:999px; background:#e8eefb; color:#29417f;
            font-weight:600; font-size:13px; margin-right:10px; margin-bottom:8px;
        }
        .status-ok, .status-warn, .status-bad {
            display:inline-block; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:700;
        }
        .status-ok { background:#dcfce7; color:#166534; }
        .status-warn { background:#fef3c7; color:#92400e; }
        .status-bad { background:#fee2e2; color:#991b1b; }
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


def metric_card(label: str, value: str, sub: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def compute_dashboard_metrics(audits: list[dict]) -> dict[str, str]:
    if not audits:
        return {
            "total": "0",
            "cierre": "-",
            "promedio": "-",
            "empresas": "-",
            "riesgo": "0",
            "backlog": "0",
        }
    df = pd.DataFrame(audits)
    total = len(df)
    cierre = f"{((df['estado'] == 'completada').sum() / total) * 100:.1f}%"
    promedio = fmt_percent(df["score_final"].fillna(0).mean())
    empresas = str(df["empresa"].fillna("-").nunique())
    riesgo = str((df["score_final"].fillna(0) < 0.65).sum())
    backlog = str(((df["estado"] == "en_progreso") & (df["score_final"].fillna(0) < 0.65)).sum())
    return {
        "total": str(total),
        "cierre": cierre,
        "promedio": promedio,
        "empresas": empresas,
        "riesgo": riesgo,
        "backlog": backlog,
    }


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
    cols = st.columns(3)
    with cols[0]:
        metric_card("Auditorias Totales", metrics["total"], "Base historica del tablero")
    with cols[1]:
        metric_card("% Cierre", metrics["cierre"], "Completadas sobre total")
    with cols[2]:
        metric_card("Score Promedio", metrics["promedio"], "Rendimiento global ponderado")
    cols = st.columns(3)
    with cols[0]:
        metric_card("Cobertura de Empresas", metrics["empresas"], "Empresas auditadas")
    with cols[1]:
        metric_card("Riesgo Alto", metrics["riesgo"], "Score menor a 65%")
    with cols[2]:
        metric_card("Backlog Critico", metrics["backlog"], "En progreso con bajo score")

    if audits:
        df = pd.DataFrame(audits)
        visible = df[["codigo", "empresa", "sucursal", "auditor_nombre", "estado", "score_final", "calificacion"]].copy()
        visible["score_final"] = visible["score_final"].map(fmt_percent)
        st.dataframe(visible, use_container_width=True, hide_index=True)


def render_new_audit() -> None:
    st.markdown('<div class="section-title">Crear Nueva Auditoria</div>', unsafe_allow_html=True)
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
    config = get_config()
    empresas_text = st.text_area("Empresas", value="\n".join(config["empresas"]), height=120)
    empresas = [item.strip() for item in empresas_text.splitlines() if item.strip()]
    empresa_default = st.selectbox(
        "Empresa por defecto",
        empresas or config["empresas"],
        index=0 if not empresas else max(0, empresas.index(config["empresa_default"]) if config["empresa_default"] in empresas else 0),
    )

    st.markdown("#### Sucursales por empresa")
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

    st.markdown("#### Ponderaciones")
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
    if not audits:
        st.info("Todavia no hay auditorias.")
        return
    df = pd.DataFrame(audits)
    visible = df[["codigo", "empresa", "sucursal", "auditor_nombre", "estado", "score_final", "calificacion", "fecha_realizacion"]].copy()
    visible["score_final"] = visible["score_final"].map(fmt_percent)
    st.dataframe(visible, use_container_width=True, hide_index=True)


def render_informes() -> None:
    st.markdown('<div class="section-title">Informes</div>', unsafe_allow_html=True)
    reports = list_reports()
    if not reports:
        st.info("No hay auditorias cerradas todavia.")
        return
    df = pd.DataFrame(reports)
    visible = df[["codigo", "empresa", "sucursal", "auditor_nombre", "fecha_cierre", "score_final", "calificacion"]].copy()
    visible["score_final"] = visible["score_final"].map(fmt_percent)
    st.dataframe(visible, use_container_width=True, hide_index=True)


def render_manual_modules(audit: dict) -> None:
    st.markdown("### Indicadores manuales")
    for control in audit["controles"]:
        if control["modulo_numero"] not in (3, 4, 7):
            continue
        with st.expander(control["modulo_nombre"]):
            col1, col2 = st.columns(2)
            total = col1.number_input("Total items", min_value=0, value=int(control.get("total_items") or 0), key=f"total_{control['id']}")
            observados = col2.number_input("Items con observacion", min_value=0, value=int(control.get("items_observacion") or 0), key=f"obs_{control['id']}")
            observaciones = st.text_area("Observaciones", value=control.get("observaciones") or "", key=f"txt_{control['id']}")
            if st.button("Guardar modulo", key=f"save_{control['id']}"):
                update_manual_control(control["id"], int(total), int(observados), observaciones)
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
        edited = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            disabled=["id", "fecha_transferencia", "numero_comprobante", "sucursal_origen", "sucursal_destino", "dias_habiles", "cumple_base", "cumple_final"],
            key=f"transfer_editor_{modulo}",
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
        edited = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            disabled=["id", "fecha", "articulo", "numero_comprobante", "sucursal_origen", "sucursal_destino", "cantidad", "importe", "cumple_final"],
            key="creditos_editor",
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
        edited = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            disabled=["id", "fecha", "tipo_comprobante", "numero_comprobante", "articulo_codigo", "articulo_descripcion", "importe", "en_muestra", "cumple_final"],
            key="ventas_editor",
        )
        if st.button("Guardar cambios ventas internas"):
            save_ventas_edits(audit["id"], edited)
            st.success("Ventas internas actualizadas.")
            st.rerun()


def render_close_section(audit: dict) -> None:
    st.markdown("### Cierre de auditoria")
    hallazgos = st.text_area("Hallazgos", value=audit.get("hallazgos") or "", height=140)
    recomendaciones = st.text_area("Recomendaciones", value=audit.get("recomendaciones") or "", height=140)
    if st.button("Cerrar auditoria", type="primary", use_container_width=True):
        close_audit(audit["id"], hallazgos, recomendaciones)
        st.success("Auditoria cerrada correctamente.")
        st.rerun()


def render_operacion(audits: list[dict]) -> None:
    st.markdown('<div class="section-title">Operacion</div>', unsafe_allow_html=True)
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

    controles_df = pd.DataFrame(audit["controles"])[
        ["modulo_numero", "modulo_nombre", "etapa", "ponderacion", "score_cumplimiento", "resultado_final", "total_items", "items_observacion"]
    ].copy()
    controles_df["ponderacion"] = controles_df["ponderacion"].map(fmt_percent)
    controles_df["score_cumplimiento"] = controles_df["score_cumplimiento"].map(fmt_percent)
    controles_df["resultado_final"] = controles_df["resultado_final"].map(fmt_percent)
    st.dataframe(controles_df, use_container_width=True, hide_index=True)

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
