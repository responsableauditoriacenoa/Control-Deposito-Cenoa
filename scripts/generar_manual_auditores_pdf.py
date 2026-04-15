from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, ListFlowable, ListItem
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from pathlib import Path
import datetime

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Manual_Auditores_Control_Depositos.pdf"

# Registrar fuente unicode si está disponible (mejor soporte tildes en algunos viewers)
try:
    pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))
    BASE_FONT = "DejaVu"
except Exception:
    BASE_FONT = "Helvetica"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="TitleCustom",
    parent=styles["Title"],
    fontName=BASE_FONT,
    fontSize=24,
    leading=30,
    textColor=colors.HexColor("#C62828"),
    spaceAfter=16
))
styles.add(ParagraphStyle(
    name="H1",
    parent=styles["Heading1"],
    fontName=BASE_FONT,
    fontSize=16,
    leading=22,
    textColor=colors.HexColor("#1F2937"),
    spaceBefore=8,
    spaceAfter=8
))
styles.add(ParagraphStyle(
    name="H2",
    parent=styles["Heading2"],
    fontName=BASE_FONT,
    fontSize=13,
    leading=18,
    textColor=colors.HexColor("#111827"),
    spaceBefore=6,
    spaceAfter=6
))
styles.add(ParagraphStyle(
    name="Body",
    parent=styles["BodyText"],
    fontName=BASE_FONT,
    fontSize=10.5,
    leading=15,
    textColor=colors.HexColor("#111827"),
    spaceAfter=6
))
styles.add(ParagraphStyle(
    name="Small",
    parent=styles["BodyText"],
    fontName=BASE_FONT,
    fontSize=9,
    leading=12,
    textColor=colors.HexColor("#4B5563"),
    spaceAfter=5
))
styles.add(ParagraphStyle(
    name="BoxTitle",
    parent=styles["BodyText"],
    fontName=BASE_FONT,
    fontSize=11,
    leading=14,
    textColor=colors.white,
    alignment=0,
))


def page_footer(canv: canvas.Canvas, doc):
    canv.saveState()
    canv.setFont(BASE_FONT, 8)
    canv.setFillColor(colors.HexColor("#6B7280"))
    text = f"Manual de Uso - Control Integral de Depósitos | Grupo Cenoa | Página {doc.page}"
    canv.drawRightString(A4[0] - 1.8 * cm, 1.1 * cm, text)
    canv.restoreState()


def section_title(text: str):
    return Paragraph(text, styles["H1"])


def subsection_title(text: str):
    return Paragraph(text, styles["H2"])


def p(text: str):
    return Paragraph(text, styles["Body"])


def small(text: str):
    return Paragraph(text, styles["Small"])


def bullet_list(items):
    flow = []
    list_items = []
    for item in items:
        list_items.append(ListItem(Paragraph(item, styles["Body"]), leftIndent=8))
    flow.append(ListFlowable(list_items, bulletType="bullet", start="circle", leftIndent=16))
    return flow


def build_manual():
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="Manual de Auditores - Control Integral de Depósitos",
        author="Grupo Cenoa"
    )

    story = []

    # Portada
    story.append(Spacer(1, 2.0 * cm))
    story.append(Paragraph("Manual de Uso para Auditores", styles["TitleCustom"]))
    story.append(Paragraph("Control Integral de Depósitos", styles["H1"]))
    story.append(Paragraph("Grupo Cenoa", styles["H2"]))
    story.append(Spacer(1, 0.6 * cm))
    story.append(p("Este documento describe el uso operativo de la aplicación para auditorías multiusuario, incluyendo carga de datos, cierre, generación de reportes y consulta de historial."))
    story.append(p(f"Versión del manual: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"))
    story.append(Spacer(1, 0.8 * cm))

    portada_table = Table([
        [Paragraph("Objetivo", styles["BoxTitle"])],
        [p("Estandarizar la operatoria de todos los auditores para asegurar trazabilidad, consistencia y disponibilidad de información histórica compartida.")],
    ], colWidths=[16.5 * cm])
    portada_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C62828")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#D1D5DB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(portada_table)
    story.append(PageBreak())

    # Índice
    story.append(section_title("1. Alcance y roles"))
    story.append(p("Este sistema permite que varios auditores trabajen desde distintas computadoras sobre una única base compartida. Toda acción queda registrada en el historial de auditorías."))
    story.extend(bullet_list([
        "Auditor: crea auditorías, carga indicadores, registra hallazgos/recomendaciones y cierra auditorías.",
        "Supervisor/Consulta: revisa dashboard, historial de auditorías e informes cerrados.",
        "Administrador técnico: mantiene el servidor encendido y conectado en red."
    ]))

    story.append(subsection_title("Navegación principal"))
    nav_table = Table([
        ["Sección", "Uso"],
        ["Dashboard", "Indicadores globales, semáforo ejecutivo y gráficos comparativos."],
        ["Nueva Auditoría", "Alta de una auditoría con código, auditor, empresa, sucursal y fecha."],
        ["Configuración", "Empresas, sucursales y ponderaciones por módulo."],
        ["Auditorías", "Historial general (en progreso + completadas) con filtros y acceso directo."],
        ["Informes", "Historial de auditorías cerradas con filtros y descarga de PDF."],
        ["Indicadores", "Carga/edición de resultados por módulo activo."],
        ["Resumen", "Checklist de cierre, hallazgos, recomendaciones y cierre final."],
    ], colWidths=[4.2 * cm, 12.3 * cm])
    nav_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ("FONTNAME", (0, 0), (-1, -1), BASE_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(nav_table)

    story.append(PageBreak())

    # Conexión multiusuario
    story.append(section_title("2. Conexión multiusuario"))
    story.append(p("La aplicación funciona con un servidor central. Los auditores ingresan desde navegador web en sus PCs y todos guardan en la misma base de datos."))
    story.extend(bullet_list([
        "PC servidor: debe estar encendida y conectada a la red corporativa.",
        "URL local en servidor: http://localhost:5000",
        "URL para otros equipos: http://IP_DEL_SERVIDOR:5000",
        "No se requiere instalación cliente en las PCs auditoras; solo navegador."
    ]))

    story.append(subsection_title("Ingreso de auditor"))
    story.extend(bullet_list([
        "Al abrir la app aparece un modal de identificación.",
        "Ingresar Nombre y Apellido reales.",
        "Ese nombre queda asociado a las auditorías creadas o editadas en la sesión.",
        "Si se necesita cambiar de auditor, usar el botón de recambio en barra lateral."
    ]))

    story.append(subsection_title("Buenas prácticas de operación simultánea"))
    story.extend(bullet_list([
        "Evitar que dos personas editen la misma auditoría en paralelo.",
        "Si una auditoría ya está abierta por otro auditor, coordinar antes de cargar cambios.",
        "Guardar borrador de cierre antes de cambiar de sección o finalizar la jornada.",
        "Al cerrar una auditoría, validar que score/calificación/hallazgos queden reflejados en Informes."
    ]))

    # Crear y trabajar auditoría
    story.append(PageBreak())
    story.append(section_title("3. Flujo operativo completo"))

    story.append(subsection_title("Paso 1: Crear auditoría"))
    story.extend(bullet_list([
        "Ir a 'Nueva Auditoría'.",
        "Completar: Código, Auditor, Empresa, Sucursal y Fecha de realización.",
        "La sucursal solo se habilita si corresponde a la empresa seleccionada.",
        "Presionar 'Crear Auditoría'."
    ]))
    story.append(p("Resultado esperado: la auditoría aparece en la sección 'Auditorías' con estado En progreso."))

    story.append(subsection_title("Paso 2: Cargar indicadores"))
    story.extend(bullet_list([
        "Abrir la auditoría desde sección Auditorías (botón Abrir).",
        "Completar cada módulo activo (1, 2, 3, 4, 7, 8, 9).",
        "En módulos con importación, cargar archivo Excel cuando aplique.",
        "Registrar observaciones y justificaciones según desvíos detectados."
    ]))

    story.append(subsection_title("Paso 3: Revisar resumen y checklist"))
    story.extend(bullet_list([
        "Ir a 'Resumen'.",
        "Verificar checklist de cierre (indicadores completos + hallazgos + recomendaciones).",
        "Si hay bloqueos, la pantalla muestra motivos específicos.",
        "Usar 'Guardar borrador' para conservar hallazgos/recomendaciones sin cerrar."
    ]))

    story.append(subsection_title("Paso 4: Cerrar auditoría y emitir informe"))
    story.extend(bullet_list([
        "Completar todos los hallazgos (ID, indicador, gravedad, descripción).",
        "Completar recomendaciones asociadas a hallazgos.",
        "Presionar 'Cerrar auditoría y exportar PDF'.",
        "El sistema calcula score final, calificación y estado completada.",
        "Se descarga automáticamente el informe PDF corporativo."
    ]))

    # Reportes
    story.append(PageBreak())
    story.append(section_title("4. Reportes y consulta histórica"))

    story.append(subsection_title("Sección Auditorías (historial general)"))
    story.extend(bullet_list([
        "Incluye auditorías en progreso y completadas.",
        "Filtros disponibles: texto libre, empresa, estado, fecha desde/hasta.",
        "Columnas clave: Código, Empresa, Sucursal, Auditor, Fecha, Estado, Score, Calificación.",
        "Acción 'Abrir' permite continuar carga o revisión."
    ]))

    story.append(subsection_title("Sección Informes (solo cerradas)"))
    story.extend(bullet_list([
        "Muestra únicamente auditorías completadas.",
        "Filtros: código/empresa/sucursal, empresa, calificación, rango de fecha.",
        "Mide cantidad de hallazgos y recomendaciones cargadas por informe.",
        "Botón 'PDF' regenera el informe descargable de la auditoría seleccionada."
    ]))

    story.append(subsection_title("Tipos de exportación disponibles"))
    exports_table = Table([
        ["Exportación", "Dónde", "Uso"],
        ["PDF ejecutivo", "Resumen / Informes", "Documento formal para comunicar resultados de auditoría."],
        ["HTML", "Pantallas por Indicador", "Versión liviana para consulta rápida."],
        ["JSON", "Resumen", "Respaldo estructurado de auditoría y controles."],
        ["XLSX muestra Ventas Internas", "Módulo 8", "Extracción de comprobantes en muestra para revisión externa."],
        ["Correo Outlook (mailto)", "Resumen", "Prearmado de correo para compartir hallazgos/recomendaciones."],
    ], colWidths=[4.6 * cm, 4.2 * cm, 7.7 * cm])
    exports_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C62828")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ("FONTNAME", (0, 0), (-1, -1), BASE_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9.2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FEF2F2")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(exports_table)

    # Dashboard
    story.append(PageBreak())
    story.append(section_title("5. Lectura del dashboard"))
    story.append(p("El dashboard sintetiza estado operativo, nivel de cumplimiento y exposición a riesgo de toda la base histórica."))
    story.extend(bullet_list([
        "Semáforo Ejecutivo: cierre operativo, rendimiento global, riesgo, cobertura, backlog crítico y calidad de información.",
        "KPIs de volumen: auditorías totales y últimos 30 días.",
        "KPIs de performance: score promedio, mediana, desviación, brecha mejor/peor.",
        "KPIs de gestión: porcentaje de cierre, cobertura de empresas, completitud de score.",
        "Gráficos: tendencia temporal, benchmark por empresa y distribución de estados."
    ]))

    story.append(subsection_title("Interpretación sugerida para líderes"))
    story.extend(bullet_list([
        "Si sube backlog crítico, revisar auditorías en progreso antiguas con score bajo.",
        "Si baja cobertura de empresas, priorizar planificación por compañía rezagada.",
        "Si cae completitud de score, reforzar disciplina de carga de indicadores.",
        "Usar score promedio + desviación para detectar estabilidad o dispersión operativa."
    ]))

    # Configuración
    story.append(PageBreak())
    story.append(section_title("6. Configuración funcional"))
    story.extend(bullet_list([
        "Ponderaciones: define el peso de cada módulo en el score final.",
        "Empresa por defecto: valor inicial sugerido en alta de auditoría.",
        "Sucursales por empresa: controla consistencia y evita combinaciones inválidas.",
        "Guardar configuración aplica cambios para futuras operaciones y recálculos necesarios."
    ]))

    story.append(subsection_title("Regla importante"))
    story.append(p("Toda sucursal debe estar asociada a una empresa válida. Si la sucursal no corresponde a la empresa elegida, la creación de auditoría será rechazada por validación."))

    # Troubleshooting
    story.append(PageBreak())
    story.append(section_title("7. Resolución de problemas frecuentes"))

    issues = [
        ["Problema", "Causa probable", "Acción recomendada"],
        ["No abre la aplicación en otra PC", "URL incorrecta o red distinta", "Verificar IP del servidor y que ambos equipos estén en la misma red."],
        ["No guarda al cerrar auditoría", "Faltan campos o indicadores incompletos", "Revisar checklist de cierre y completar motivos de bloqueo mostrados."],
        ["No aparecen auditorías en Informes", "Auditoría aún en progreso", "Cerrar auditoría desde Resumen y volver a cargar sección Informes."],
        ["PDF no se descarga", "Bloqueo de navegador o sesión sin auditoría activa", "Habilitar descargas del navegador y verificar que la auditoría esté abierta/completada."],
        ["Datos inconsistentes entre auditores", "Edición simultánea del mismo registro", "Definir responsable único por auditoría durante la carga."],
    ]
    issues_table = Table(issues, colWidths=[4.4 * cm, 5.1 * cm, 7.0 * cm])
    issues_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ("FONTNAME", (0, 0), (-1, -1), BASE_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(issues_table)

    story.append(Spacer(1, 0.4 * cm))
    story.append(subsection_title("Checklist diario recomendado para auditores"))
    story.extend(bullet_list([
        "Confirmar identidad de auditor al iniciar sesión.",
        "Trabajar sobre auditorías asignadas para evitar solapamientos.",
        "Guardar borrador cuando quede trabajo pendiente.",
        "Cerrar auditorías completas y validar aparición en Informes.",
        "Compartir PDF final por circuito definido con jefatura."
    ]))

    # Cierre
    story.append(PageBreak())
    story.append(section_title("8. Anexo rápido (guía de 2 minutos)"))
    story.append(p("1) Abrir URL del sistema -> 2) Identificarse -> 3) Crear/Abrir auditoría -> 4) Cargar indicadores -> 5) Completar hallazgos/recomendaciones -> 6) Cerrar y exportar PDF -> 7) Consultar Informes."))
    story.append(Spacer(1, 0.3 * cm))
    story.append(small("Nota: Este manual refleja la versión actual del sistema en fecha de emisión. Si se agregan módulos o pantallas nuevas, actualizar este documento."))

    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    build_manual()
    print(f"Manual generado en: {OUTPUT}")
