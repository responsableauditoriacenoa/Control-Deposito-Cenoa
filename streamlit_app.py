from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from streamlit_backend import (
    AUDITORES_DEFAULT,
    DB_DISPLAY,
    ETAPAS_POR_MODULO,
    MODULO_NOMBRES,
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
    save_creditos_edits,
    save_transferencias_edits,
    save_ventas_edits,
    update_manual_control,
)


st.set_page_config(page_title="Control de Depositos", layout="wide")
init_db()


def _format_percent(value: float | None) -> str:
    return f"{(float(value or 0) * 100):.2f}%"


def _audit_selector(audits: list[dict]) -> str | None:
    if not audits:
        return None
    options = {f"{item['codigo']} | {item.get('empresa', '-') } | {item.get('sucursal', '-') }": item["id"] for item in audits}
    label = st.selectbox("Auditoria", list(options.keys()))
    return options[label]


def render_dashboard(audits: list[dict]) -> None:
    st.subheader("Dashboard")
    if not audits:
        st.info("Todavia no hay auditorias cargadas.")
        return

    df = pd.DataFrame(audits)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total auditorias", len(df))
    col2.metric("Completadas", int((df["estado"] == "completada").sum()))
    col3.metric("En progreso", int((df["estado"] == "en_progreso").sum()))
    promedio = df["score_final"].fillna(0).mean()
    col4.metric("Score promedio", _format_percent(promedio))

    visible = df[["codigo", "empresa", "sucursal", "auditor_nombre", "estado", "score_final", "calificacion", "fecha_realizacion"]].copy()
    visible["score_final"] = visible["score_final"].map(_format_percent)
    st.dataframe(visible, use_container_width=True, hide_index=True)


def render_new_audit() -> None:
    st.subheader("Nueva auditoria")
    config = get_config()
    empresa = st.selectbox("Empresa", config["empresas"], index=config["empresas"].index(config["empresa_default"]))
    sucursales = config["sucursales_por_empresa"].get(empresa, [])

    with st.form("crear_auditoria"):
        codigo = st.text_input("Codigo")
        auditor = st.selectbox("Auditor", AUDITORES_DEFAULT)
        sucursal = st.selectbox("Sucursal", sucursales)
        fecha_realizacion = st.date_input("Fecha de realizacion", value=date.today())
        submitted = st.form_submit_button("Crear auditoria", use_container_width=True)
        if submitted:
            try:
                create_audit(codigo, auditor, empresa, sucursal, fecha_realizacion)
                st.success("Auditoria creada correctamente.")
                st.rerun()
            except Exception as error:
                st.error(str(error))


def render_manual_modules(audit: dict) -> None:
    st.markdown("### Carga manual de modulos 3, 4 y 7")
    for control in audit["controles"]:
        if control["modulo_numero"] not in (3, 4, 7):
            continue
        with st.expander(f"{control['modulo_nombre']}"):
            col1, col2 = st.columns(2)
            total = col1.number_input(
                f"Total items #{control['modulo_numero']}",
                min_value=0,
                value=int(control.get("total_items") or 0),
                key=f"total_{control['id']}",
            )
            observados = col2.number_input(
                f"Observados #{control['modulo_numero']}",
                min_value=0,
                value=int(control.get("items_observacion") or 0),
                key=f"obs_{control['id']}",
            )
            observaciones = st.text_area(
                "Observaciones",
                value=control.get("observaciones") or "",
                key=f"txt_{control['id']}",
            )
            if st.button("Guardar modulo", key=f"save_{control['id']}"):
                try:
                    update_manual_control(control["id"], int(total), int(observados), observaciones)
                    st.success("Modulo actualizado.")
                    st.rerun()
                except Exception as error:
                    st.error(str(error))


def render_transfer_section(audit: dict, modulo: int) -> None:
    nombre = MODULO_NOMBRES[modulo]
    with st.expander(nombre, expanded=modulo == 1):
        uploader = st.file_uploader(
            f"Importar Excel para modulo {modulo}",
            type=["xlsx", "xls"],
            key=f"up_transfer_{modulo}",
        )
        if uploader and st.button("Procesar transferencias", key=f"process_transfer_{modulo}"):
            try:
                import_transferencias(audit["id"], audit["sucursal"], audit["fecha_realizacion"], uploader)
                st.success("Transferencias importadas.")
                st.rerun()
            except Exception as error:
                st.error(str(error))

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
        if st.button("Guardar cambios transferencias", key=f"save_transfer_{modulo}"):
            save_transferencias_edits(audit["id"], modulo, edited)
            st.success("Transferencias actualizadas.")
            st.rerun()


def render_creditos_section(audit: dict) -> None:
    with st.expander(MODULO_NOMBRES[2], expanded=True):
        uploader = st.file_uploader("Importar Excel de creditos", type=["xlsx", "xls"], key="up_creditos")
        if uploader and st.button("Procesar creditos"):
            try:
                import_creditos(audit["id"], uploader)
                st.success("Creditos importados.")
                st.rerun()
            except Exception as error:
                st.error(str(error))

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
            try:
                import_ventas_internas(audit["id"], uploader)
                st.success("Ventas internas importadas.")
                st.rerun()
            except Exception as error:
                st.error(str(error))

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
        try:
            close_audit(audit["id"], hallazgos, recomendaciones)
            st.success("Auditoria cerrada correctamente.")
            st.rerun()
        except Exception as error:
            st.error(str(error))


def render_audit_detail(audits: list[dict]) -> None:
    st.subheader("Detalle operativo")
    audit_id = _audit_selector(audits)
    if not audit_id:
        st.info("Crea una auditoria para empezar.")
        return

    audit = get_audit(audit_id)
    st.caption(f"Base activa: `{DB_DISPLAY}`")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Estado", audit["estado"])
    col2.metric("Score", _format_percent(audit.get("score_final")))
    col3.metric("Calificacion", audit.get("calificacion") or "-")
    col4.metric("Sucursal", audit.get("sucursal") or "-")

    controles_df = pd.DataFrame(audit["controles"])[["modulo_numero", "modulo_nombre", "etapa", "ponderacion", "score_cumplimiento", "resultado_final", "total_items", "items_observacion"]]
    controles_df["ponderacion"] = controles_df["ponderacion"].map(_format_percent)
    controles_df["score_cumplimiento"] = controles_df["score_cumplimiento"].map(_format_percent)
    controles_df["resultado_final"] = controles_df["resultado_final"].map(_format_percent)
    st.dataframe(controles_df, use_container_width=True, hide_index=True)

    render_transfer_section(audit, 1)
    render_creditos_section(audit)
    render_manual_modules(audit)
    render_ventas_section(audit)
    render_transfer_section(audit, 9)
    render_close_section(audit)


def render_deploy_notes() -> None:
    st.subheader("Despliegue")
    st.markdown(
        """
        - `Streamlit Cloud` puede correr esta version Python del sistema.
        - Para demo, la app puede usar `SQLite`.
        - Para produccion multiusuario, conviene migrar la persistencia a `PostgreSQL`.
        - Si queres conservar la base actual local, podes subir una copia y definir `CONTROL_DEPOSITOS_DB`.
        """
    )


st.title("Control Integral de Depositos")
audits = list_audits()
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Nueva auditoria", "Operacion", "Deploy"])
with tab1:
    render_dashboard(audits)
with tab2:
    render_new_audit()
with tab3:
    render_audit_detail(audits)
with tab4:
    render_deploy_notes()
