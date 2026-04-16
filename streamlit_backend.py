from __future__ import annotations

import io
import json
import os
import shutil
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd


MODULOS_ACTIVOS = [1, 2, 3, 4, 7, 8, 9]
MODULO_NOMBRES = {
    1: "1. Transf. Pend. de Recepcion",
    2: "2. Pendientes de Credito",
    3: "3. Remito de Compras",
    4: "4. Rdo. Inv. Rotativo",
    7: "5. Remitos Pend. de Facturacion",
    8: "6. Ventas Internas Directas",
    9: "7. Transf. Pend. De Entrega",
}
ETAPAS_POR_MODULO = {
    1: "Entradas",
    2: "Entradas",
    3: "Entradas",
    4: "Stock",
    7: "Salidas",
    8: "Salidas",
    9: "Salidas",
}
EMPRESAS_DEFAULT = ["Autosol", "Autolux", "Ciel", "Neumaticos Alte. Brown", "VOGE"]
SUCURSALES_POR_EMPRESA_DEFAULT = {
    "Autolux": [
        "Casa Central - Jujuy",
        "Suc. Salta PosVenta",
        "Suc. Tartagal",
        "Suc. Las Lajitas",
        "Chapa y Pintura Autolux Salta",
    ],
    "Autosol": [
        "Casa Central - Jujuy",
        "Suc. Salta Posventa",
        "Suc. Taller Express",
        "Suc. Tartagal",
    ],
    "Ciel": ["Casa Central Jujuy"],
    "Neumaticos Alte. Brown": ["SUC. LAS LOMAS", "SUC. ALTE. BROWN"],
    "VOGE": ["Voge Salta"],
}
AUDITORES_DEFAULT = [
    "Luis Palacios",
    "Gustavo Zambrano",
    "Nancy Fernandez",
    "Diego Guantay",
]
PONDERACION_EQUIVALENTE = 1 / len(MODULOS_ACTIVOS)


def _mysql_url_from_env() -> str:
    explicit_url = os.getenv("DATABASE_URL", "").strip()
    if explicit_url:
        return explicit_url

    host = os.getenv("MYSQL_HOST", "").strip()
    database = os.getenv("MYSQL_DATABASE", "").strip()
    user = os.getenv("MYSQL_USER", "").strip()
    password = os.getenv("MYSQL_PASSWORD", "").strip()
    port = os.getenv("MYSQL_PORT", "3306").strip() or "3306"

    if host and database and user:
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"

    return ""


DATABASE_URL = _mysql_url_from_env()
USE_MYSQL = bool(DATABASE_URL)
_SQLALCHEMY_CREATE_ENGINE = None
_SQLALCHEMY_TEXT = None


def _load_sqlalchemy() -> tuple[Any, Any]:
    global _SQLALCHEMY_CREATE_ENGINE, _SQLALCHEMY_TEXT
    if _SQLALCHEMY_CREATE_ENGINE is not None and _SQLALCHEMY_TEXT is not None:
        return _SQLALCHEMY_CREATE_ENGINE, _SQLALCHEMY_TEXT
    try:
        from sqlalchemy import create_engine, text  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "No se pudieron cargar las dependencias de base de datos. "
            "Verifica que `SQLAlchemy` este instalado correctamente."
        ) from exc
    _SQLALCHEMY_CREATE_ENGINE = create_engine
    _SQLALCHEMY_TEXT = text
    return create_engine, text


def default_db_path() -> Path:
    if USE_MYSQL:
        return Path("mysql")
    env_path = os.getenv("CONTROL_DEPOSITOS_DB", "").strip()
    if env_path:
        return Path(env_path)

    streamlit_db = Path("data/auditorias.db")
    if streamlit_db.exists():
        return streamlit_db

    legacy_db = Path("backend/db/auditorias.db")
    if legacy_db.exists():
        streamlit_db.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy_db, streamlit_db)
        return streamlit_db

    streamlit_db.parent.mkdir(parents=True, exist_ok=True)
    return streamlit_db


DB_PATH = default_db_path()
DB_DISPLAY = DATABASE_URL if USE_MYSQL else str(DB_PATH)


class QueryResult:
    def __init__(self, result: Any):
        if result is not None and getattr(result, "returns_rows", False):
            self._rows = [dict(row) for row in result.mappings().all()]
        else:
            self._rows = []

    def fetchall(self) -> list[dict[str, Any]]:
        return self._rows

    def fetchone(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None


def _compile_query(sql: str, params: tuple[Any, ...] | list[Any] | None = None) -> tuple[Any, dict[str, Any]]:
    _, sql_text = _load_sqlalchemy()
    if not params:
        return sql_text(sql), {}

    params = tuple(params)
    parts = sql.split("?")
    if len(parts) - 1 != len(params):
        raise ValueError("Cantidad de parametros no coincide con la consulta.")

    compiled = [parts[0]]
    values: dict[str, Any] = {}
    for index, value in enumerate(params):
        key = f"p{index}"
        compiled.append(f":{key}")
        compiled.append(parts[index + 1])
        values[key] = value

    return sql_text("".join(compiled)), values


class DBConnection:
    def __init__(self, engine: Any):
        self.engine = engine
        self._ctx = None
        self._conn = None

    def __enter__(self) -> "DBConnection":
        self._ctx = self.engine.begin()
        self._conn = self._ctx.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Any:
        return self._ctx.__exit__(exc_type, exc, tb)

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] | None = None) -> QueryResult:
        statement, values = _compile_query(sql, params)
        result = self._conn.execute(statement, values)
        return QueryResult(result)

    def executescript(self, sql_script: str) -> None:
        _, sql_text = _load_sqlalchemy()
        statements = [statement.strip() for statement in sql_script.split(";") if statement.strip()]
        for statement in statements:
            self._conn.execute(sql_text(statement))

    def commit(self) -> None:
        return None


def get_engine() -> Any:
    create_engine, _ = _load_sqlalchemy()
    if USE_MYSQL:
        return create_engine(DATABASE_URL, pool_pre_ping=True)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        f"sqlite:///{DB_PATH.as_posix()}",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )


ENGINE = get_engine()


def get_connection() -> DBConnection:
    return DBConnection(ENGINE)


def normalize_text(value: Any) -> str:
    import unicodedata

    text = str(value or "").strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return "".join(char.lower() if char.isalnum() else " " for char in text).strip()


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True)


def parse_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except Exception:
        return fallback


def calculate_calificacion(score: float) -> str:
    if score >= 0.94:
        return "SAT - Satisfactorio"
    if score >= 0.82:
        return "ADE - Adecuado"
    if score >= 0.65:
        return "SUJ - Sujeto a mejora"
    if score >= 0.35:
        return "NAD - No adecuado"
    return "INS - Insatisfactorio"


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS auditores (
              id VARCHAR(64) PRIMARY KEY,
              nombre VARCHAR(255) NOT NULL UNIQUE,
              email VARCHAR(255),
              activo INTEGER DEFAULT 1,
              fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS auditorias (
              id VARCHAR(64) PRIMARY KEY,
              codigo VARCHAR(255) NOT NULL UNIQUE,
              auditor_id VARCHAR(64) NOT NULL,
              empresa VARCHAR(255) DEFAULT 'Autosol',
              sucursal VARCHAR(255) NOT NULL,
              fecha_realizacion DATETIME NOT NULL,
              estado VARCHAR(50) DEFAULT 'en_progreso',
              score_final DOUBLE,
              calificacion VARCHAR(255),
              hallazgos LONGTEXT,
              recomendaciones LONGTEXT,
              activa INTEGER DEFAULT 1,
              fecha_cierre DATETIME,
              fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
              fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS controles (
              id VARCHAR(64) PRIMARY KEY,
              auditoria_id VARCHAR(64) NOT NULL,
              modulo_numero INTEGER,
              modulo_nombre VARCHAR(255),
              etapa VARCHAR(50),
              ponderacion DOUBLE,
              score_cumplimiento DOUBLE,
              resultado_final DOUBLE,
              total_items INTEGER,
              items_observacion INTEGER,
              observaciones LONGTEXT,
              fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS transferencias (
              id VARCHAR(64) PRIMARY KEY,
              auditoria_id VARCHAR(64) NOT NULL,
              control_id VARCHAR(64) NOT NULL,
              modulo_numero INTEGER NOT NULL,
              fecha_transferencia DATETIME,
              numero_comprobante VARCHAR(255),
              sucursal_origen VARCHAR(255),
              sucursal_destino VARCHAR(255),
              valorizacion_total DOUBLE,
              dias_habiles INTEGER DEFAULT 0,
              cumple_base INTEGER DEFAULT 1,
              justificado INTEGER DEFAULT 0,
              cumple_final INTEGER DEFAULT 1,
              observacion LONGTEXT,
              origen_archivo VARCHAR(255),
              raw_data LONGTEXT,
              fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
              fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS creditos_pendientes (
              id VARCHAR(64) PRIMARY KEY,
              auditoria_id VARCHAR(64) NOT NULL,
              control_id VARCHAR(64) NOT NULL,
              fecha DATETIME,
              articulo VARCHAR(255),
              numero_comprobante VARCHAR(255),
              sucursal_origen VARCHAR(255),
              sucursal_destino VARCHAR(255),
              cantidad DOUBLE,
              importe DOUBLE,
              tiene_reclamo INTEGER DEFAULT 0,
              cumple_final INTEGER DEFAULT 0,
              observacion LONGTEXT,
              origen_archivo VARCHAR(255),
              raw_data LONGTEXT,
              fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
              fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS ventas_internas (
              id VARCHAR(64) PRIMARY KEY,
              auditoria_id VARCHAR(64) NOT NULL,
              control_id VARCHAR(64) NOT NULL,
              fecha DATETIME,
              tipo_comprobante VARCHAR(255),
              talonario VARCHAR(255),
              numero_comprobante VARCHAR(255),
              articulo_codigo VARCHAR(255),
              articulo_descripcion VARCHAR(255),
              imputacion_contable VARCHAR(255),
              importe DOUBLE,
              en_muestra INTEGER DEFAULT 0,
              firma_responsable_deposito INTEGER DEFAULT 0,
              firma_gerente_sector INTEGER DEFAULT 0,
              justificado INTEGER DEFAULT 0,
              cumple_final INTEGER DEFAULT 0,
              observacion LONGTEXT,
              origen_archivo VARCHAR(255),
              raw_data LONGTEXT,
              fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
              fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS configuracion (
              id VARCHAR(64) PRIMARY KEY,
              nombre_config VARCHAR(255) UNIQUE,
              valor LONGTEXT,
              fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        for auditor in AUDITORES_DEFAULT:
            conn.execute(
                """
                INSERT INTO auditores (id, nombre)
                SELECT ?, ?
                WHERE NOT EXISTS (
                  SELECT 1 FROM auditores WHERE id = ?
                )
                """,
                (auditor, auditor, auditor),
            )

        defaults = {
            "empresas": EMPRESAS_DEFAULT,
            "empresa_default": "Autosol",
            "sucursales_por_empresa": SUCURSALES_POR_EMPRESA_DEFAULT,
            "ponderaciones": {str(modulo): PONDERACION_EQUIVALENTE for modulo in MODULOS_ACTIVOS},
        }
        for key, value in defaults.items():
            conn.execute(
                """
                INSERT INTO configuracion (id, nombre_config, valor)
                SELECT ?, ?, ?
                WHERE NOT EXISTS (
                  SELECT 1 FROM configuracion WHERE nombre_config = ?
                )
                """,
                (str(uuid.uuid4()), key, to_json(value), key),
            )
        conn.commit()


def get_config() -> dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute("SELECT nombre_config, valor FROM configuracion").fetchall()
    values = {row["nombre_config"]: parse_json(row["valor"], None) for row in rows}
    return {
        "empresas": values.get("empresas") or EMPRESAS_DEFAULT,
        "empresa_default": values.get("empresa_default") or "Autosol",
        "sucursales_por_empresa": values.get("sucursales_por_empresa") or SUCURSALES_POR_EMPRESA_DEFAULT,
        "ponderaciones": values.get("ponderaciones")
        or {str(modulo): PONDERACION_EQUIVALENTE for modulo in MODULOS_ACTIVOS},
    }


def save_config(
    empresas: list[str],
    empresa_default: str,
    sucursales_por_empresa: dict[str, list[str]],
    ponderaciones: dict[str, float],
) -> None:
    empresas = [str(item).strip() for item in empresas if str(item).strip()]
    if not empresas:
        raise ValueError("Debe existir al menos una empresa.")

    normalized_sucursales = {}
    for empresa in empresas:
        values = sucursales_por_empresa.get(empresa, [])
        normalized_sucursales[empresa] = sorted({str(item).strip() for item in values if str(item).strip()})

    if not any(normalized_sucursales.values()):
        raise ValueError("Debe existir al menos una sucursal configurada.")

    if empresa_default not in empresas:
        empresa_default = empresas[0]

    raw_weights = []
    for modulo in MODULOS_ACTIVOS:
        value = float(ponderaciones.get(str(modulo), 0) or 0)
        raw_weights.append(max(value, 0))
    total_weight = sum(raw_weights)
    if total_weight <= 0:
        normalized_weights = {str(modulo): PONDERACION_EQUIVALENTE for modulo in MODULOS_ACTIVOS}
    else:
        normalized_weights = {
            str(modulo): raw_weights[index] / total_weight
            for index, modulo in enumerate(MODULOS_ACTIVOS)
        }

    config_values = {
        "empresas": empresas,
        "empresa_default": empresa_default,
        "sucursales_por_empresa": normalized_sucursales,
        "ponderaciones": normalized_weights,
    }

    with get_connection() as conn:
        for key, value in config_values.items():
            conn.execute(
                """
                UPDATE configuracion
                SET valor = ?, fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE nombre_config = ?
                """,
                (to_json(value), key),
            )

        for modulo in MODULOS_ACTIVOS:
            ponderacion = float(normalized_weights[str(modulo)])
            conn.execute(
                """
                UPDATE controles
                SET ponderacion = ?, resultado_final = COALESCE(score_cumplimiento, 0) * ?
                WHERE modulo_numero = ?
                """,
                (ponderacion, ponderacion, modulo),
            )
        conn.commit()

    audits = list_audits()
    for audit in audits:
        recalculate_audit(audit["id"])


def list_reports() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT a.*, u.nombre AS auditor_nombre
            FROM auditorias a
            LEFT JOIN auditores u ON u.id = a.auditor_id
            WHERE a.activa = 1 AND a.estado = 'completada'
            ORDER BY COALESCE(a.fecha_cierre, a.fecha_actualizacion, a.fecha_realizacion) DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def list_audits() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT a.*, u.nombre AS auditor_nombre
            FROM auditorias a
            LEFT JOIN auditores u ON u.id = a.auditor_id
            WHERE a.activa = 1
            ORDER BY COALESCE(a.fecha_cierre, a.fecha_actualizacion, a.fecha_realizacion) DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_audit(auditoria_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        audit = conn.execute(
            """
            SELECT a.*, u.nombre AS auditor_nombre
            FROM auditorias a
            LEFT JOIN auditores u ON u.id = a.auditor_id
            WHERE a.id = ? AND a.activa = 1
            """,
            (auditoria_id,),
        ).fetchone()
        if not audit:
            return None
        controles = conn.execute(
            "SELECT * FROM controles WHERE auditoria_id = ? ORDER BY modulo_numero",
            (auditoria_id,),
        ).fetchall()
    payload = dict(audit)
    payload["controles"] = [dict(row) for row in controles]
    return payload


def create_audit(codigo: str, auditor_id: str, empresa: str, sucursal: str, fecha_realizacion: date) -> str:
    config = get_config()
    if sucursal not in config["sucursales_por_empresa"].get(empresa, []):
        raise ValueError("La sucursal no corresponde a la empresa seleccionada.")

    auditoria_id = str(uuid.uuid4())
    iso_date = datetime.combine(fecha_realizacion, datetime.min.time(), tzinfo=timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO auditorias (id, codigo, auditor_id, empresa, sucursal, fecha_realizacion, estado)
            VALUES (?, ?, ?, ?, ?, ?, 'en_progreso')
            """,
            (auditoria_id, codigo.strip(), auditor_id, empresa, sucursal, iso_date),
        )
        ponderaciones = config["ponderaciones"]
        for modulo in MODULOS_ACTIVOS:
            conn.execute(
                """
                INSERT INTO controles (
                  id, auditoria_id, modulo_numero, modulo_nombre, etapa, ponderacion,
                  score_cumplimiento, resultado_final, total_items, items_observacion, observaciones
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, 0, 0, '')
                """,
                (
                    str(uuid.uuid4()),
                    auditoria_id,
                    modulo,
                    MODULO_NOMBRES[modulo],
                    ETAPAS_POR_MODULO[modulo],
                    float(ponderaciones.get(str(modulo), PONDERACION_EQUIVALENTE)),
                ),
            )
        conn.commit()
    return auditoria_id


def recalculate_audit(auditoria_id: str) -> float:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT COALESCE(resultado_final, 0) AS resultado_final
            FROM controles
            WHERE auditoria_id = ? AND modulo_numero IN (1, 2, 3, 4, 7, 8, 9)
            """,
            (auditoria_id,),
        ).fetchall()
        score = sum(float(row["resultado_final"] or 0) for row in rows)
        conn.execute(
            """
            UPDATE auditorias
            SET score_final = ?, calificacion = ?, fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (score, calculate_calificacion(score), auditoria_id),
        )
        conn.commit()
    return score


def update_manual_control(control_id: str, score_percent: float) -> None:
    with get_connection() as conn:
        control = conn.execute("SELECT * FROM controles WHERE id = ?", (control_id,)).fetchone()
        if not control:
            raise ValueError("Control no encontrado.")
        score_percent = max(0.0, min(float(score_percent), 100.0))
        score = score_percent / 100
        resultado = score * float(control["ponderacion"] or 0)
        conn.execute(
            """
            UPDATE controles
            SET score_cumplimiento = ?, resultado_final = ?
            WHERE id = ?
            """,
            (score, resultado, control_id),
        )
        conn.commit()
    recalculate_audit(control["auditoria_id"])


def save_close_draft(auditoria_id: str, hallazgos: str, recomendaciones: str) -> None:
    hallazgos_data = parse_json(hallazgos or "[]", [])
    recomendaciones_data = parse_json(recomendaciones or "[]", [])
    if not isinstance(hallazgos_data, list) or not isinstance(recomendaciones_data, list):
        raise ValueError("El formato de hallazgos o recomendaciones no es valido.")
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE auditorias
            SET hallazgos = ?, recomendaciones = ?, fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (hallazgos.strip(), recomendaciones.strip(), auditoria_id),
        )
        conn.commit()


def close_audit(auditoria_id: str, hallazgos: str, recomendaciones: str) -> None:
    hallazgos = hallazgos.strip()
    recomendaciones = recomendaciones.strip()
    if not hallazgos or not recomendaciones:
        raise ValueError("Debes cargar hallazgos y recomendaciones antes del cierre.")

    hallazgos_data = parse_json(hallazgos, [])
    recomendaciones_data = parse_json(recomendaciones, [])
    if not isinstance(hallazgos_data, list) or not isinstance(recomendaciones_data, list):
        raise ValueError("El formato de hallazgos o recomendaciones no es valido.")
    hallazgos_validos = [
        item for item in hallazgos_data
        if str(item.get("id", "")).strip()
        and str(item.get("indicador", "")).strip()
        and str(item.get("gravedad", "")).strip().lower() in {"alta", "media", "baja"}
        and str(item.get("descripcion", "")).strip()
    ]
    hallazgo_ids = {str(item["id"]).strip() for item in hallazgos_validos}
    recomendaciones_validas = [
        item for item in recomendaciones_data
        if str(item.get("id", "")).strip()
        and str(item.get("hallazgoId", "")).strip() in hallazgo_ids
        and str(item.get("descripcion", "")).strip()
    ]
    if not hallazgos_validos:
        raise ValueError("Debes cargar al menos un hallazgo valido.")
    if not recomendaciones_validas:
        raise ValueError("Debes cargar al menos una recomendacion valida vinculada a un hallazgo.")

    audit = get_audit(auditoria_id)
    controles = audit["controles"] if audit else []
    faltantes = [c for c in controles if not pd.notna(c.get("score_cumplimiento"))]
    if faltantes:
        nombres = ", ".join(str(c.get("modulo_nombre") or c.get("modulo_numero")) for c in faltantes)
        raise ValueError(f"Faltan % de cumplimiento en: {nombres}")

    score = recalculate_audit(auditoria_id)
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE auditorias
            SET hallazgos = ?, recomendaciones = ?, estado = 'completada',
                score_final = ?, calificacion = ?, fecha_cierre = CURRENT_TIMESTAMP,
                fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (hallazgos, recomendaciones, score, calculate_calificacion(score), auditoria_id),
        )
        conn.commit()


def parse_excel_date(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, (int, float)):
        try:
            if value < 20000 or value > 80000:
                return None
        except Exception:
            return None
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit() and len(text) > 5:
        return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            parsed = datetime.strptime(text, fmt)
            if 2000 <= parsed.year <= 2100:
                return parsed
        except Exception:
            pass
    try:
        parsed = pd.to_datetime(text, errors="coerce")
    except Exception:
        return None
    if pd.isna(parsed):
        return None
    if not (2000 <= parsed.year <= 2100):
        return None
    return parsed.to_pydatetime()


def to_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and pd.notna(value):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = "".join(char for char in text if char.isdigit() or char in ",.-")
    if not text:
        return None
    has_comma = "," in text
    has_dot = "." in text
    if has_comma and has_dot:
        last_comma = text.rfind(",")
        last_dot = text.rfind(".")
        if last_comma > last_dot:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif has_comma:
        parts = text.split(",")
        text = text.replace(",", ".") if len(parts[-1]) <= 2 else text.replace(",", "")
    elif has_dot:
        parts = text.split(".")
        text = text if len(parts[-1]) <= 2 else text.replace(".", "")
    text = text[0] + text[1:].replace("-", "") if text.startswith("-") else text.replace("-", "")
    try:
        return float(text)
    except ValueError:
        return None


def business_days_between(start: datetime | None, end: datetime | None) -> int:
    if not start or not end:
        return 0
    current = start.date()
    target = end.date()
    days = 0
    while current < target:
        current += timedelta(days=1)
        if current.weekday() < 5:
            days += 1
    return days


def read_excel_matrix(uploaded_file: Any) -> list[list[Any]]:
    content = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
    matrix = pd.read_excel(io.BytesIO(content), header=None, dtype=object).fillna("").values.tolist()
    return matrix


def find_header_index(matrix: list[list[Any]], required_terms: list[str]) -> int:
    for index, row in enumerate(matrix):
        normalized = [normalize_text(cell) for cell in row]
        if all(any(term in cell for cell in normalized) for term in required_terms):
            return index
    raise ValueError("No se pudo detectar el encabezado del archivo.")


def map_headers(header_row: list[Any]) -> dict[str, int]:
    aliases = {
        "fecha": ["fecha", "fecha transferencia", "fecha comprobante", "fecha emision"],
        "numero_comprobante": ["nro cpbte", "nro comprobante", "numero comprobante", "comprobante"],
        "sucursal_origen": ["sucursal origen", "origen"],
        "sucursal_destino": ["sucursal destino", "destino"],
        "valorizacion_total": ["valoriz total", "valorizacion total", "importe", "total"],
        "articulo": ["articulo", "codigo", "cod articulo", "c o d i g o"],
        "cantidad": ["cantidad", "cant", "cantid total", "cantid"],
        "importe": ["importe", "total", "monto", "cto comp", "valoriz total"],
    }
    normalized = [normalize_text(cell) for cell in header_row]
    mapping: dict[str, int] = {}
    for key, values in aliases.items():
        matches: list[int] = []
        for idx, header in enumerate(normalized):
            if header in values:
                matches.append(idx)
        if not matches:
            continue
        mapping[key] = matches[-1] if key == "importe" and len(matches) > 1 else matches[0]
    return mapping


def _matches_sucursal(candidate: Any, sucursal: str) -> bool:
    left = normalize_text(candidate)
    right = normalize_text(sucursal)
    return bool(left and right and (left in right or right in left))


def _recalculate_transfer_module(conn: DBConnection, auditoria_id: str, modulo: int) -> None:
    control = conn.execute(
        "SELECT * FROM controles WHERE auditoria_id = ? AND modulo_numero = ?",
        (auditoria_id, modulo),
    ).fetchone()
    rows = conn.execute(
        "SELECT * FROM transferencias WHERE auditoria_id = ? AND modulo_numero = ?",
        (auditoria_id, modulo),
    ).fetchall()
    total = len(rows)
    cumplen = sum(1 for row in rows if row["cumple_final"] == 1)
    observadas = total - cumplen
    score = 1.0 if total == 0 else cumplen / total
    resultado = score * float(control["ponderacion"] or 0)
    conn.execute(
        """
        UPDATE controles
        SET total_items = ?, items_observacion = ?, score_cumplimiento = ?, resultado_final = ?
        WHERE id = ?
        """,
        (total, observadas, score, resultado, control["id"]),
    )


def import_transferencias(auditoria_id: str, sucursal: str, fecha_realizacion: str, uploaded_file: Any) -> None:
    matrix = read_excel_matrix(uploaded_file)
    header_index = find_header_index(matrix, ["sucursal origen", "sucursal destino"])
    header_map = map_headers(matrix[header_index])
    required = ["fecha", "sucursal_origen", "sucursal_destino"]
    if not all(key in header_map for key in required):
        raise ValueError("Faltan columnas obligatorias para importar transferencias.")

    fecha_auditoria = parse_excel_date(fecha_realizacion) or datetime.utcnow()

    with get_connection() as conn:
        controls = conn.execute(
            "SELECT id, modulo_numero FROM controles WHERE auditoria_id = ? AND modulo_numero IN (1, 9)",
            (auditoria_id,),
        ).fetchall()
        control_by_modulo = {row["modulo_numero"]: row["id"] for row in controls}
        conn.execute("DELETE FROM transferencias WHERE auditoria_id = ?", (auditoria_id,))

        for raw_row in matrix[header_index + 1 :]:
            if not any(str(cell).strip() for cell in raw_row):
                continue
            origen = raw_row[header_map["sucursal_origen"]]
            destino = raw_row[header_map["sucursal_destino"]]
            modulo = 1 if _matches_sucursal(destino, sucursal) else 9 if _matches_sucursal(origen, sucursal) else None
            if modulo not in (1, 9):
                continue
            fecha = parse_excel_date(raw_row[header_map["fecha"]])
            dias_habiles = business_days_between(fecha, fecha_auditoria)
            cumple_base = 1 if dias_habiles <= 2 else 0
            conn.execute(
                """
                INSERT INTO transferencias (
                  id, auditoria_id, control_id, modulo_numero, fecha_transferencia, numero_comprobante,
                  sucursal_origen, sucursal_destino, valorizacion_total, dias_habiles,
                  cumple_base, justificado, cumple_final, observacion, origen_archivo, raw_data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, '', ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    auditoria_id,
                    control_by_modulo[modulo],
                    modulo,
                    fecha.isoformat() if fecha else None,
                    raw_row[header_map.get("numero_comprobante", -1)] if "numero_comprobante" in header_map else None,
                    origen,
                    destino,
                    to_number(raw_row[header_map.get("valorizacion_total", -1)]) if "valorizacion_total" in header_map else None,
                    dias_habiles,
                    cumple_base,
                    uploaded_file.name,
                    to_json(raw_row),
                ),
            )

        _recalculate_transfer_module(conn, auditoria_id, 1)
        _recalculate_transfer_module(conn, auditoria_id, 9)
        conn.commit()
    recalculate_audit(auditoria_id)


def save_transferencias_edits(auditoria_id: str, modulo: int, edited_rows: pd.DataFrame) -> None:
    with get_connection() as conn:
        for _, row in edited_rows.iterrows():
            cumple_base = 1 if int(row.get("cumple_base", 0)) == 1 else 0
            justificado = 1 if bool(row.get("justificado")) else 0
            cumple_final = 1 if (cumple_base or justificado) else 0
            observacion = str(row.get("observacion", "") or "").strip()
            conn.execute(
                """
                UPDATE transferencias
                SET justificado = ?, observacion = ?, cumple_final = ?, fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE id = ? AND auditoria_id = ?
                """,
                (justificado, observacion, cumple_final, row["id"], auditoria_id),
            )
        _recalculate_transfer_module(conn, auditoria_id, modulo)
        conn.commit()
    recalculate_audit(auditoria_id)


def _recalculate_creditos_module(conn: DBConnection, auditoria_id: str) -> None:
    control = conn.execute(
        "SELECT * FROM controles WHERE auditoria_id = ? AND modulo_numero = 2",
        (auditoria_id,),
    ).fetchone()
    rows = conn.execute("SELECT * FROM creditos_pendientes WHERE auditoria_id = ?", (auditoria_id,)).fetchall()
    total = len(rows)
    cumplen = sum(1 for row in rows if row["cumple_final"] == 1)
    observadas = total - cumplen
    score = 1.0 if total == 0 else cumplen / total
    resultado = score * float(control["ponderacion"] or 0)
    conn.execute(
        """
        UPDATE controles
        SET total_items = ?, items_observacion = ?, score_cumplimiento = ?, resultado_final = ?
        WHERE id = ?
        """,
        (total, observadas, score, resultado, control["id"]),
    )


def import_creditos(auditoria_id: str, uploaded_file: Any) -> None:
    matrix = read_excel_matrix(uploaded_file)
    header_index = find_header_index(matrix, ["fecha", "cpbte"])
    header_map = map_headers(matrix[header_index])
    if "fecha" not in header_map or "numero_comprobante" not in header_map:
        raise ValueError("No se detectaron columnas obligatorias para Pendientes de Credito.")

    with get_connection() as conn:
        control = conn.execute(
            "SELECT id FROM controles WHERE auditoria_id = ? AND modulo_numero = 2",
            (auditoria_id,),
        ).fetchone()
        conn.execute("DELETE FROM creditos_pendientes WHERE auditoria_id = ?", (auditoria_id,))
        for raw_row in matrix[header_index + 1 :]:
            if not any(str(cell).strip() for cell in raw_row):
                continue
            fecha = parse_excel_date(raw_row[header_map["fecha"]])
            conn.execute(
                """
                INSERT INTO creditos_pendientes (
                  id, auditoria_id, control_id, fecha, articulo, numero_comprobante,
                  sucursal_origen, sucursal_destino, cantidad, importe, tiene_reclamo, cumple_final,
                  observacion, origen_archivo, raw_data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, '', ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    auditoria_id,
                    control["id"],
                    fecha.isoformat() if fecha else None,
                    raw_row[header_map.get("articulo", -1)] if "articulo" in header_map else None,
                    raw_row[header_map["numero_comprobante"]],
                    raw_row[header_map.get("sucursal_origen", -1)] if "sucursal_origen" in header_map else None,
                    raw_row[header_map.get("sucursal_destino", -1)] if "sucursal_destino" in header_map else None,
                    to_number(raw_row[header_map.get("cantidad", -1)]) if "cantidad" in header_map else None,
                    to_number(raw_row[header_map.get("importe", -1)]) if "importe" in header_map else None,
                    uploaded_file.name,
                    to_json(raw_row),
                ),
            )
        _recalculate_creditos_module(conn, auditoria_id)
        conn.commit()
    recalculate_audit(auditoria_id)


def save_creditos_edits(auditoria_id: str, edited_rows: pd.DataFrame) -> None:
    with get_connection() as conn:
        for _, row in edited_rows.iterrows():
            tiene_reclamo = 1 if bool(row.get("tiene_reclamo")) else 0
            cumple_final = 1 if tiene_reclamo else 0
            conn.execute(
                """
                UPDATE creditos_pendientes
                SET tiene_reclamo = ?, cumple_final = ?, observacion = ?, fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE id = ? AND auditoria_id = ?
                """,
                (tiene_reclamo, cumple_final, str(row.get("observacion", "") or ""), row["id"], auditoria_id),
            )
        _recalculate_creditos_module(conn, auditoria_id)
        conn.commit()
    recalculate_audit(auditoria_id)


def is_mostrador_sale(value: Any) -> bool:
    normalized = normalize_text(value)
    return "mostrador" in normalized and ("vta" in normalized or "venta" in normalized)


def _extract_ventas(matrix: list[list[Any]], header_index: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    added_detail = False

    def flush() -> None:
        nonlocal current, added_detail
        if current and not added_detail:
            rows.append({**current, "articulo_codigo": None, "articulo_descripcion": None})

    for raw_row in matrix[header_index + 1 :]:
        if not any(str(cell).strip() for cell in raw_row):
            continue
        fecha = parse_excel_date(raw_row[0])
        first_cell = normalize_text(raw_row[0])
        if fecha:
            flush()
            current = {
                "fecha": fecha.isoformat(),
                "tipo_comprobante": str(raw_row[1]).strip() or None,
                "talonario": str(raw_row[2]).strip() or None,
                "numero_comprobante": str(raw_row[3] or raw_row[4]).strip() or None,
                "imputacion_contable": str(raw_row[5]).strip() or None,
                "importe": to_number(raw_row[8] if len(raw_row) > 8 else None),
                "raw_data": raw_row,
            }
            added_detail = False
            continue
        if not current or first_cell in {"interno", "chasis", "articulo"}:
            continue
        articulo_codigo = str(raw_row[0]).strip() or None
        articulo_descripcion = str(raw_row[2]).strip() if len(raw_row) > 2 else None
        if not articulo_codigo and not articulo_descripcion:
            continue
        rows.append(
            {
                **current,
                "articulo_codigo": articulo_codigo,
                "articulo_descripcion": articulo_descripcion,
                "importe": to_number(raw_row[10] if len(raw_row) > 10 else None) or current["importe"],
                "raw_data": raw_row,
            }
        )
        added_detail = True
    flush()
    return rows


def _sample_ventas(rows: list[dict[str, Any]]) -> set[int]:
    grouped: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not is_mostrador_sale(row.get("tipo_comprobante")):
            continue
        key = str(row.get("numero_comprobante") or f"sin_comprobante_{index}")
        grouped.setdefault(key, {"indices": [], "total": 0.0})
        grouped[key]["indices"].append(index)
        grouped[key]["total"] += abs(float(row.get("importe") or 0))
    ordered = sorted(grouped.values(), key=lambda item: item["total"], reverse=True)
    total = len(ordered)
    if total == 0:
        return set()
    sample_count = total if total < 20 else min(total, max(int(total * 0.75 + 0.999), 20))
    selected: set[int] = set()
    for item in ordered[:sample_count]:
        selected.update(item["indices"])
    return selected


def _recalculate_ventas_module(conn: DBConnection, auditoria_id: str) -> None:
    control = conn.execute(
        "SELECT * FROM controles WHERE auditoria_id = ? AND modulo_numero = 8",
        (auditoria_id,),
    ).fetchone()
    rows = conn.execute(
        "SELECT * FROM ventas_internas WHERE auditoria_id = ? AND en_muestra = 1",
        (auditoria_id,),
    ).fetchall()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["numero_comprobante"] or row["id"]), []).append(row)
    total = len(grouped)
    cumplen = sum(1 for group in grouped.values() if any(row["cumple_final"] == 1 for row in group))
    observadas = total - cumplen
    score = 1.0 if total == 0 else cumplen / total
    resultado = score * float(control["ponderacion"] or 0)
    conn.execute(
        """
        UPDATE controles
        SET total_items = ?, items_observacion = ?, score_cumplimiento = ?, resultado_final = ?
        WHERE id = ?
        """,
        (total, observadas, score, resultado, control["id"]),
    )


def import_ventas_internas(auditoria_id: str, uploaded_file: Any) -> None:
    matrix = read_excel_matrix(uploaded_file)
    header_index = find_header_index(matrix, ["fecha", "interna", "comprobante"])
    rows = _extract_ventas(matrix, header_index)
    if not rows:
        raise ValueError("El archivo no contiene ventas internas validas para importar.")
    sample = _sample_ventas(rows)

    with get_connection() as conn:
        control = conn.execute(
            "SELECT id FROM controles WHERE auditoria_id = ? AND modulo_numero = 8",
            (auditoria_id,),
        ).fetchone()
        conn.execute("DELETE FROM ventas_internas WHERE auditoria_id = ?", (auditoria_id,))
        for index, row in enumerate(rows):
            en_muestra = 1 if index in sample else 0
            firma_deposito = 0 if en_muestra else 1
            firma_gerente = 0 if en_muestra else 1
            cumple_final = 0 if en_muestra else 1
            conn.execute(
                """
                INSERT INTO ventas_internas (
                  id, auditoria_id, control_id, fecha, tipo_comprobante, talonario,
                  numero_comprobante, articulo_codigo, articulo_descripcion, imputacion_contable, importe,
                  en_muestra, firma_responsable_deposito, firma_gerente_sector, justificado, cumple_final,
                  observacion, origen_archivo, raw_data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, '', ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    auditoria_id,
                    control["id"],
                    row["fecha"],
                    row["tipo_comprobante"],
                    row["talonario"],
                    row["numero_comprobante"],
                    row["articulo_codigo"],
                    row["articulo_descripcion"],
                    row["imputacion_contable"],
                    row["importe"],
                    en_muestra,
                    firma_deposito,
                    firma_gerente,
                    cumple_final,
                    uploaded_file.name,
                    to_json(row["raw_data"]),
                ),
            )
        _recalculate_ventas_module(conn, auditoria_id)
        conn.commit()
    recalculate_audit(auditoria_id)


def save_ventas_edits(auditoria_id: str, edited_rows: pd.DataFrame) -> None:
    with get_connection() as conn:
        for _, row in edited_rows.iterrows():
            firma_deposito = 1 if bool(row.get("firma_responsable_deposito")) else 0
            firma_gerente = 1 if bool(row.get("firma_gerente_sector")) else 0
            justificado = 1 if bool(row.get("justificado")) else 0
            cumple_final = 1 if ((firma_deposito and firma_gerente) or justificado) else 0
            numero_comprobante = str(row.get("numero_comprobante") or "").strip()
            if numero_comprobante:
                target_rows = conn.execute(
                    """
                    SELECT id FROM ventas_internas
                    WHERE auditoria_id = ? AND numero_comprobante = ? AND en_muestra = 1
                    """,
                    (auditoria_id, numero_comprobante),
                ).fetchall()
                ids = [item["id"] for item in target_rows]
            else:
                ids = [row["id"]]
            for venta_id in ids:
                conn.execute(
                    """
                    UPDATE ventas_internas
                    SET firma_responsable_deposito = ?, firma_gerente_sector = ?, justificado = ?,
                        cumple_final = ?, observacion = ?, fecha_actualizacion = CURRENT_TIMESTAMP
                    WHERE id = ? AND auditoria_id = ?
                    """,
                    (
                        firma_deposito,
                        firma_gerente,
                        justificado,
                        cumple_final,
                        str(row.get("observacion", "") or ""),
                        venta_id,
                        auditoria_id,
                    ),
                )
        _recalculate_ventas_module(conn, auditoria_id)
        conn.commit()
    recalculate_audit(auditoria_id)


def fetch_table(sql: str, params: tuple[Any, ...] = ()) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.DataFrame(conn.execute(sql, params).fetchall())
