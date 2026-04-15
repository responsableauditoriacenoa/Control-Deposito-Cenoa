import XLSX from 'xlsx';
import { v4 as uuidv4 } from 'uuid';
import { allAsync, getAsync, runAsync } from '../db/database.js';

const HEADER_ALIASES = {
  fecha: ['fecha', 'fecha transferencia', 'fecha transf', 'fecha comprobante'],
  numeroComprobante: ['nro cpbte', 'nro. cpbte', 'comprobante', 'numero comprobante', 'nro comprobante'],
  sucursalOrigen: ['sucursal origen', 'origen'],
  sucursalDestino: ['sucursal destino', 'destino'],
  valorizacionTotal: ['valoriz total', 'valoriz. total', 'valorizacion total', 'total', 'importe', 'cantid total', 'cantid. total']
};

function normalizeText(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

function normalizeHeader(value) {
  return normalizeText(value).replace(/\s+/g, ' ');
}

function findHeadersAndData(worksheet) {
  const matrix = XLSX.utils.sheet_to_json(worksheet, {
    header: 1,
    defval: null,
    raw: false,
    blankrows: false
  });

  let headerIndex = -1;
  let headerRow = [];

  for (let index = 0; index < matrix.length; index += 1) {
    const row = matrix[index] || [];
    const normalized = row.map((cell) => normalizeHeader(cell));
    const hasOrigen = normalized.some((item) => item.includes('sucursal origen'));
    const hasDestino = normalized.some((item) => item.includes('sucursal destino'));
    if (hasOrigen && hasDestino) {
      headerIndex = index;
      headerRow = row;
      break;
    }
  }

  if (headerIndex < 0) {
    throw new Error('No se pudo detectar la fila de encabezados (Sucursal Origen / Sucursal Destino).');
  }

  const headers = headerRow.map((cell, index) => {
    const normalized = normalizeHeader(cell);
    return normalized || `col_${index + 1}`;
  });

  const rows = [];
  for (let index = headerIndex + 1; index < matrix.length; index += 1) {
    const row = matrix[index] || [];
    const obj = {};
    let hasValues = false;

    for (let col = 0; col < headers.length; col += 1) {
      const key = headers[col];
      const value = row[col] ?? null;
      obj[key] = value;
      if (value !== null && value !== '') {
        hasValues = true;
      }
    }

    if (hasValues) {
      rows.push(obj);
    }
  }

  return { rows, headerIndex: headerIndex + 1 };
}

function getColumnKey(row) {
  const entries = Object.keys(row || {});
  const normalizedEntries = entries.map((key) => ({ key, normalized: normalizeText(key) }));

  const result = {};
  for (const [target, aliases] of Object.entries(HEADER_ALIASES)) {
    const match = normalizedEntries.find((entry) => aliases.includes(entry.normalized));
    if (match) {
      result[target] = match.key;
    }
  }

  return result;
}

function parseExcelDate(value) {
  if (!value) {
    return null;
  }

  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    return new Date(Date.UTC(value.getFullYear(), value.getMonth(), value.getDate()));
  }

  if (typeof value === 'number') {
    const parsed = XLSX.SSF.parse_date_code(value);
    if (!parsed) {
      return null;
    }

    return new Date(Date.UTC(parsed.y, parsed.m - 1, parsed.d));
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return new Date(Date.UTC(parsed.getFullYear(), parsed.getMonth(), parsed.getDate()));
}

function businessDaysBetween(startDate, endDate) {
  if (!startDate || !endDate) {
    return 0;
  }

  const start = new Date(Date.UTC(startDate.getUTCFullYear(), startDate.getUTCMonth(), startDate.getUTCDate()));
  const end = new Date(Date.UTC(endDate.getUTCFullYear(), endDate.getUTCMonth(), endDate.getUTCDate()));

  if (start > end) {
    return 0;
  }

  let count = 0;
  const current = new Date(start);
  while (current < end) {
    current.setUTCDate(current.getUTCDate() + 1);
    const day = current.getUTCDay();
    if (day !== 0 && day !== 6) {
      count += 1;
    }
  }

  return count;
}

function matchesSucursal(candidate, sucursalAudit) {
  const left = normalizeText(candidate);
  const right = normalizeText(sucursalAudit);
  return Boolean(left) && Boolean(right) && (left.includes(right) || right.includes(left));
}

function toNumber(value) {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  if (typeof value === 'number') {
    return value;
  }

  const sanitized = String(value).replace(/\./g, '').replace(',', '.').replace(/[^0-9.-]/g, '');
  const parsed = Number(sanitized);
  return Number.isNaN(parsed) ? null : parsed;
}

function resolveModulo(row, sucursal) {
  if (matchesSucursal(row.sucursalDestino, sucursal)) {
    return 1;
  }

  if (matchesSucursal(row.sucursalOrigen, sucursal)) {
    return 9;
  }

  return null;
}

async function recalculateAudit(auditoriaId) {
  const controles = await allAsync(
    `SELECT * FROM controles
     WHERE auditoria_id = ? AND modulo_numero IN (1, 2, 3, 4, 7, 8, 9)
     ORDER BY modulo_numero`,
    [auditoriaId]
  );

  const scoreFinal = controles.reduce((accumulator, control) => accumulator + (control.resultado_final || 0), 0);

  let calificacion = 'INS - Insatisfactorio';
  if (scoreFinal >= 0.94) {
    calificacion = 'SAT - Satisfactorio';
  } else if (scoreFinal >= 0.82) {
    calificacion = 'ADE - Adecuado';
  } else if (scoreFinal >= 0.65) {
    calificacion = 'SUJ - Sujeto a mejora';
  } else if (scoreFinal >= 0.35) {
    calificacion = 'NAD - No adecuado';
  }

  await runAsync(
    `UPDATE auditorias
     SET score_final = ?, calificacion = ?, fecha_actualizacion = CURRENT_TIMESTAMP
     WHERE id = ?`,
    [scoreFinal, calificacion, auditoriaId]
  );

  return { scoreFinal, calificacion };
}

export async function recalculateTransferModule(auditoriaId, moduloNumero) {
  const control = await getAsync(
    `SELECT * FROM controles WHERE auditoria_id = ? AND modulo_numero = ?`,
    [auditoriaId, moduloNumero]
  );

  if (!control) {
    throw new Error(`No se encontró el control del módulo ${moduloNumero}`);
  }

  const transferencias = await allAsync(
    `SELECT * FROM transferencias WHERE auditoria_id = ? AND modulo_numero = ? ORDER BY fecha_transferencia ASC`,
    [auditoriaId, moduloNumero]
  );

  const total = transferencias.length;
  const cumplen = transferencias.filter((transferencia) => transferencia.cumple_final === 1).length;
  const observadas = transferencias.filter((transferencia) => transferencia.cumple_final === 0).length;
  const scoreCumplimiento = total === 0 ? 1 : cumplen / total;
  const resultadoFinal = (control.ponderacion || 0) * scoreCumplimiento;

  await runAsync(
    `UPDATE controles
     SET total_items = ?, items_observacion = ?, score_cumplimiento = ?, resultado_final = ?, fecha_creacion = fecha_creacion
     WHERE id = ?`,
    [total, observadas, scoreCumplimiento, resultadoFinal, control.id]
  );

  const auditSummary = await recalculateAudit(auditoriaId);

  return {
    controlId: control.id,
    moduloNumero,
    total,
    cumplen,
    observadas,
    scoreCumplimiento,
    resultadoFinal,
    auditSummary
  };
}

export async function importTransferenciasFromWorkbook({ auditoria, fileName, buffer }) {
  const workbook = XLSX.read(buffer, { type: 'buffer', cellDates: true });
  const firstSheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[firstSheetName];
  const { rows, headerIndex } = findHeadersAndData(worksheet);

  if (!rows.length) {
    throw new Error('El Excel no contiene filas de datos');
  }

  const headerMap = getColumnKey(rows[0]);
  if (!headerMap.sucursalOrigen || !headerMap.sucursalDestino) {
    throw new Error('No se encontraron las columnas Sucursal Origen y Sucursal Destino en el Excel');
  }

  if (!headerMap.fecha) {
    throw new Error('No se encontró una columna de Fecha para calcular antigüedad');
  }

  const controls = await allAsync(
    `SELECT id, modulo_numero FROM controles WHERE auditoria_id = ? AND modulo_numero IN (1, 9)`,
    [auditoria.id]
  );

  const controlsByModulo = Object.fromEntries(controls.map((control) => [control.modulo_numero, control]));
  if (!controlsByModulo[1] || !controlsByModulo[9]) {
    throw new Error('La auditoría no tiene creados los módulos 1 y 9');
  }

  await runAsync(
    `DELETE FROM transferencias WHERE auditoria_id = ? AND modulo_numero IN (1, 9)`,
    [auditoria.id]
  );

  const fechaAuditoria = parseExcelDate(auditoria.fecha_realizacion) || new Date();
  const imported = [];

  for (const row of rows) {
    const normalizedRow = {
      fecha: row[headerMap.fecha],
      numeroComprobante: headerMap.numeroComprobante ? row[headerMap.numeroComprobante] : null,
      sucursalOrigen: row[headerMap.sucursalOrigen],
      sucursalDestino: row[headerMap.sucursalDestino],
      valorizacionTotal: headerMap.valorizacionTotal ? row[headerMap.valorizacionTotal] : null
    };

    const moduloNumero = resolveModulo(normalizedRow, auditoria.sucursal);
    if (![1, 9].includes(moduloNumero)) {
      continue;
    }

    const fechaTransferencia = parseExcelDate(normalizedRow.fecha);
    const diasHabiles = businessDaysBetween(fechaTransferencia, fechaAuditoria);
    const cumpleBase = diasHabiles <= 2 ? 1 : 0;
    const transferId = uuidv4();
    const controlId = controlsByModulo[moduloNumero].id;

    await runAsync(
      `INSERT INTO transferencias (
        id, auditoria_id, control_id, modulo_numero, fecha_transferencia, numero_comprobante,
        sucursal_origen, sucursal_destino, valorizacion_total, dias_habiles,
        cumple_base, justificado, cumple_final, observacion, origen_archivo, raw_data
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        transferId,
        auditoria.id,
        controlId,
        moduloNumero,
        fechaTransferencia ? fechaTransferencia.toISOString() : null,
        normalizedRow.numeroComprobante || null,
        normalizedRow.sucursalOrigen || null,
        normalizedRow.sucursalDestino || null,
        toNumber(normalizedRow.valorizacionTotal),
        diasHabiles,
        cumpleBase,
        0,
        cumpleBase,
        '',
        fileName,
        JSON.stringify(row)
      ]
    );

    imported.push({ id: transferId, moduloNumero, cumpleBase });
  }

  const resumen1 = await recalculateTransferModule(auditoria.id, 1);
  const resumen9 = await recalculateTransferModule(auditoria.id, 9);

  return {
    importedCount: imported.length,
    modulo1: resumen1,
    modulo9: resumen9,
    hoja: firstSheetName,
    encabezadoDetectadoEnFila: headerIndex
  };
}