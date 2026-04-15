import XLSX from 'xlsx';
import { v4 as uuidv4 } from 'uuid';
import { allAsync, getAsync, runAsync } from '../db/database.js';

const HEADER_ALIASES = {
  fecha: ['fecha', 'fecha comprobante', 'fecha emision'],
  articulo: ['articulo', 'c o d i g o', 'codigo', 'cod articulo'],
  numeroComprobante: ['nro cpbte', 'nro. cpbte', 'comprobante', 'nro comprobante', 'numero comprobante'],
  sucursalOrigen: ['sucursal origen', 'origen'],
  sucursalDestino: ['sucursal destino', 'destino'],
  cantidad: ['cantidad', 'cant', 'cantid', 'cantid total', 'cantid. total'],
  importe: ['importe', 'total', 'valoriz total', 'valoriz. total', 'monto', 'cto comp', 'cto comp.']
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

  const text = String(value || '').trim();
  const ddmmyyyyMatch = text.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (ddmmyyyyMatch) {
    const day = Number(ddmmyyyyMatch[1]);
    const month = Number(ddmmyyyyMatch[2]);
    const year = Number(ddmmyyyyMatch[3]);
    if (day >= 1 && day <= 31 && month >= 1 && month <= 12) {
      return new Date(Date.UTC(year, month - 1, day));
    }
  }

  const parsed = new Date(text);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return new Date(Date.UTC(parsed.getFullYear(), parsed.getMonth(), parsed.getDate()));
}

function toNumber(value) {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  if (typeof value === 'number') {
    return value;
  }

  const text = String(value).trim().replace(/[^0-9,.-]/g, '');
  if (!text) {
    return null;
  }

  const hasComma = text.includes(',');
  const hasDot = text.includes('.');

  let normalized = text;

  if (hasComma && hasDot) {
    const lastComma = text.lastIndexOf(',');
    const lastDot = text.lastIndexOf('.');
    const decimalSeparator = lastComma > lastDot ? ',' : '.';
    const thousandSeparator = decimalSeparator === ',' ? '.' : ',';
    normalized = text.split(thousandSeparator).join('');
    if (decimalSeparator === ',') {
      normalized = normalized.replace(',', '.');
    }
  } else if (hasComma) {
    const commaParts = text.split(',');
    const decimalByLength = commaParts[commaParts.length - 1].length <= 2;
    normalized = decimalByLength
      ? text.replace(',', '.')
      : text.split(',').join('');
  } else if (hasDot) {
    const dotParts = text.split('.');
    const decimalByLength = dotParts[dotParts.length - 1].length <= 2;
    normalized = decimalByLength
      ? text
      : text.split('.').join('');
  }

  const parsed = Number(normalized);
  return Number.isNaN(parsed) ? null : parsed;
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
    const hasFecha = normalized.some((item) => item.includes('fecha'));
    const hasComprobante = normalized.some((item) => item.includes('cpbte') || item.includes('comprobante'));
    if (hasFecha && hasComprobante) {
      headerIndex = index;
      headerRow = row;
      break;
    }
  }

  if (headerIndex < 0) {
    throw new Error('No se pudo detectar la fila de encabezados para Pendientes de Crédito.');
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

  const findAliasMatches = (aliases) => normalizedEntries.filter((entry) => aliases.includes(entry.normalized));

  const result = {};
  for (const [target, aliases] of Object.entries(HEADER_ALIASES)) {
    const matches = findAliasMatches(aliases);
    if (!matches.length) {
      continue;
    }

    if (target === 'importe' && matches.length > 1) {
      result[target] = matches[matches.length - 1].key;
      continue;
    }

    result[target] = matches[0].key;
  }

  return result;
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

export async function recalculateCreditosModule(auditoriaId) {
  const control = await getAsync(
    `SELECT * FROM controles WHERE auditoria_id = ? AND modulo_numero = 2`,
    [auditoriaId]
  );

  if (!control) {
    throw new Error('No se encontró el control del módulo 2');
  }

  const rows = await allAsync(
    `SELECT * FROM creditos_pendientes WHERE auditoria_id = ? ORDER BY fecha ASC`,
    [auditoriaId]
  );

  const total = rows.length;
  const cumplen = rows.filter((row) => row.cumple_final === 1).length;
  const observadas = rows.filter((row) => row.cumple_final === 0).length;
  const scoreCumplimiento = total === 0 ? 1 : cumplen / total;
  const resultadoFinal = (control.ponderacion || 0) * scoreCumplimiento;

  await runAsync(
    `UPDATE controles
     SET total_items = ?, items_observacion = ?, score_cumplimiento = ?, resultado_final = ?
     WHERE id = ?`,
    [total, observadas, scoreCumplimiento, resultadoFinal, control.id]
  );

  const auditSummary = await recalculateAudit(auditoriaId);

  return {
    controlId: control.id,
    total,
    cumplen,
    observadas,
    scoreCumplimiento,
    resultadoFinal,
    auditSummary
  };
}

export async function importCreditosFromWorkbook({ auditoria, fileName, buffer }) {
  const workbook = XLSX.read(buffer, { type: 'buffer', cellDates: true });
  const firstSheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[firstSheetName];
  const { rows, headerIndex } = findHeadersAndData(worksheet);

  if (!rows.length) {
    throw new Error('El Excel no contiene filas para importar en Pendientes de Crédito');
  }

  const headerMap = getColumnKey(rows[0]);
  if (!headerMap.fecha || !headerMap.numeroComprobante) {
    throw new Error('No se detectaron columnas obligatorias (Fecha y Nro. Cpbte./Comprobante)');
  }

  const control = await getAsync(
    `SELECT id FROM controles WHERE auditoria_id = ? AND modulo_numero = 2`,
    [auditoria.id]
  );

  if (!control) {
    throw new Error('La auditoría no tiene creado el módulo 2');
  }

  await runAsync(`DELETE FROM creditos_pendientes WHERE auditoria_id = ?`, [auditoria.id]);

  const imported = [];
  for (const row of rows) {
    const recordId = uuidv4();
    const fecha = parseExcelDate(row[headerMap.fecha]);
    const numeroComprobante = row[headerMap.numeroComprobante] || null;
    const articulo = headerMap.articulo ? row[headerMap.articulo] : null;
    const sucursalOrigen = headerMap.sucursalOrigen ? row[headerMap.sucursalOrigen] : null;
    const sucursalDestino = headerMap.sucursalDestino ? row[headerMap.sucursalDestino] : null;
    const cantidad = headerMap.cantidad ? toNumber(row[headerMap.cantidad]) : null;
    const importe = headerMap.importe ? toNumber(row[headerMap.importe]) : null;

    await runAsync(
      `INSERT INTO creditos_pendientes (
        id, auditoria_id, control_id, fecha, articulo, numero_comprobante,
        sucursal_origen, sucursal_destino, cantidad, importe,
        tiene_reclamo, cumple_final, observacion, origen_archivo, raw_data
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        recordId,
        auditoria.id,
        control.id,
        fecha ? fecha.toISOString() : null,
        articulo || null,
        numeroComprobante || null,
        sucursalOrigen || null,
        sucursalDestino || null,
        cantidad,
        importe,
        0,
        0,
        '',
        fileName,
        JSON.stringify(row)
      ]
    );

    imported.push(recordId);
  }

  const resumen = await recalculateCreditosModule(auditoria.id);

  return {
    importedCount: imported.length,
    hoja: firstSheetName,
    encabezadoDetectadoEnFila: headerIndex,
    resumen
  };
}