import XLSX from 'xlsx';
import { v4 as uuidv4 } from 'uuid';
import { allAsync, getAsync, runAsync } from '../db/database.js';

function normalizeText(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

function isMostradorSale(value) {
  const tipo = normalizeText(value);
  return tipo.includes('mostrador') && (tipo.includes('vta') || tipo.includes('venta'));
}

function parseExcelDate(value) {
  if (!value) {
    return null;
  }

  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    return new Date(Date.UTC(value.getFullYear(), value.getMonth(), value.getDate()));
  }

  if (typeof value === 'number') {
    if (value < 20000 || value > 80000) {
      return null;
    }

    const parsed = XLSX.SSF.parse_date_code(value);
    if (!parsed) {
      return null;
    }

    if (parsed.y < 2000 || parsed.y > 2100) {
      return null;
    }

    return new Date(Date.UTC(parsed.y, parsed.m - 1, parsed.d));
  }

  const text = String(value).trim();
  if (!text || /^\d+$/.test(text)) {
    return null;
  }

  const longDateMatch = text.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (longDateMatch) {
    const day = Number(longDateMatch[1]);
    const month = Number(longDateMatch[2]);
    const year = Number(longDateMatch[3]);
    if (year < 2000 || year > 2100) {
      return null;
    }
    return new Date(Date.UTC(year, month - 1, day));
  }

  const shortDateMatch = text.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2})$/);
  if (shortDateMatch) {
    const day = Number(shortDateMatch[1]);
    const month = Number(shortDateMatch[2]);
    const year = 2000 + Number(shortDateMatch[3]);
    return new Date(Date.UTC(year, month - 1, day));
  }

  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    const parsed = new Date(text);
    if (!Number.isNaN(parsed.getTime()) && parsed.getFullYear() >= 2000 && parsed.getFullYear() <= 2100) {
      return new Date(Date.UTC(parsed.getFullYear(), parsed.getMonth(), parsed.getDate()));
    }
  }

  return null;
}

function toNumber(value) {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null;
  }

  let normalized = String(value).trim().replace(/[^0-9.,-]/g, '');
  if (!normalized) {
    return null;
  }

  const lastDot = normalized.lastIndexOf('.');
  const lastComma = normalized.lastIndexOf(',');

  if (lastDot >= 0 && lastComma >= 0) {
    if (lastComma > lastDot) {
      normalized = normalized.replace(/\./g, '').replace(',', '.');
    } else {
      normalized = normalized.replace(/,/g, '');
    }
  } else if (lastComma >= 0) {
    const decimals = normalized.length - lastComma - 1;
    if (decimals <= 2) {
      normalized = normalized.replace(',', '.');
    } else {
      normalized = normalized.replace(/,/g, '');
    }
  }

  normalized = normalized.replace(/(?!^)-/g, '');

  const parsed = Number(normalized);
  return Number.isNaN(parsed) ? null : parsed;
}

function findHeaderIndex(matrix) {
  for (let index = 0; index < matrix.length; index += 1) {
    const row = matrix[index] || [];
    const normalizedCells = row.map((cell) => normalizeText(cell));
    const hasFecha = normalizedCells.some((cell) => cell === 'fecha');
    const hasInterna = normalizedCells.some((cell) => cell.includes('interna'));
    const hasComprobante = normalizedCells.some((cell) => cell.includes('cpbte') || cell.includes('comprobante'));

    if (hasFecha && hasInterna && hasComprobante) {
      return index;
    }
  }

  return -1;
}

function extractVentasFromMatrix(matrix, headerIndex) {
  const rows = [];
  let currentVenta = null;
  let addedDetailForCurrent = false;

  const flushCurrentVentaWithoutDetail = () => {
    if (currentVenta && !addedDetailForCurrent) {
      rows.push({
        ...currentVenta,
        articulo_codigo: null,
        articulo_descripcion: null,
        raw_data: currentVenta.raw_data
      });
    }
  };

  for (let index = headerIndex + 1; index < matrix.length; index += 1) {
    const row = matrix[index] || [];
    const firstCellNormalized = normalizeText(row[0]);
    const fecha = parseExcelDate(row[0]);

    if (fecha) {
      flushCurrentVentaWithoutDetail();

      const tipoComprobante = row[1] ? String(row[1]).trim() : null;
      const talonario = row[2] ? String(row[2]).trim() : null;
      const numeroComprobante = row[3] || row[4] ? String(row[3] || row[4]).trim() : null;
      const imputacionContable = row[5] ? String(row[5]).trim() : null;
      const importeCabecera = toNumber(row[8] ?? row[9]);

      currentVenta = {
        fecha: fecha.toISOString(),
        tipo_comprobante: tipoComprobante,
        talonario,
        numero_comprobante: numeroComprobante,
        imputacion_contable: imputacionContable,
        importe: importeCabecera,
        raw_data: row
      };
      addedDetailForCurrent = false;
      continue;
    }

    if (!currentVenta) {
      continue;
    }

    if (firstCellNormalized === 'interno' || firstCellNormalized === 'chasis' || firstCellNormalized === 'articulo') {
      continue;
    }

    const articuloCodigo = row[0] ? String(row[0]).trim() : null;
    const articuloDescripcion = row[2] ? String(row[2]).trim() : null;
    const importeDetalle = toNumber(row[10] ?? row[8]);
    const hasArticulo = Boolean(articuloCodigo) && articuloCodigo.length >= 3;
    const hasDescripcion = Boolean(articuloDescripcion);

    if (!hasArticulo && !hasDescripcion) {
      continue;
    }

    rows.push({
      ...currentVenta,
      articulo_codigo: articuloCodigo,
      articulo_descripcion: articuloDescripcion,
      importe: importeDetalle ?? currentVenta.importe,
      raw_data: row
    });

    addedDetailForCurrent = true;
  }

  flushCurrentVentaWithoutDetail();
  return rows;
}

function buildSampleVtaMostrador(rows) {
  const groupedByComprobante = new Map();

  rows.forEach((row, index) => {
    if (!isMostradorSale(row.tipo_comprobante)) {
      return;
    }

    const comprobanteKey = String(row.numero_comprobante || `sin_comprobante_${index}`);
    if (!groupedByComprobante.has(comprobanteKey)) {
      groupedByComprobante.set(comprobanteKey, {
        comprobante: comprobanteKey,
        totalImporteAbs: 0,
        indices: []
      });
    }

    const item = groupedByComprobante.get(comprobanteKey);
    item.indices.push(index);
    item.totalImporteAbs += Math.abs(row.importe || 0);
  });

  const comprobantes = [...groupedByComprobante.values()].sort(
    (left, right) => right.totalImporteAbs - left.totalImporteAbs
  );

  const totalComprobantes = comprobantes.length;
  if (totalComprobantes === 0) {
    return {
      sampledRows: new Set(),
      totalComprobantes,
      totalComprobantesMuestra: 0
    };
  }

  const sampleByPercent = Math.ceil(totalComprobantes * 0.75);
  const totalComprobantesMuestra = totalComprobantes < 20
    ? totalComprobantes
    : Math.min(totalComprobantes, Math.max(sampleByPercent, 20));

  const sampledRows = new Set();
  for (let index = 0; index < totalComprobantesMuestra; index += 1) {
    const comprobante = comprobantes[index];
    comprobante.indices.forEach((rowIndex) => sampledRows.add(rowIndex));
  }

  return {
    sampledRows,
    totalComprobantes,
    totalComprobantesMuestra
  };
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

export async function recalculateVentasInternasModule(auditoriaId) {
  const control = await getAsync(
    `SELECT * FROM controles WHERE auditoria_id = ? AND modulo_numero = 8`,
    [auditoriaId]
  );

  if (!control) {
    throw new Error('No se encontró el control del módulo 8');
  }

  const rows = await allAsync(
    `SELECT * FROM ventas_internas WHERE auditoria_id = ? ORDER BY fecha ASC, numero_comprobante ASC`,
    [auditoriaId]
  );

  const sampledRows = rows.filter((row) => row.en_muestra === 1);
  const comprobanteMap = new Map();

  sampledRows.forEach((row) => {
    const key = String(row.numero_comprobante || 'sin_comprobante');
    if (!comprobanteMap.has(key)) {
      comprobanteMap.set(key, []);
    }
    comprobanteMap.get(key).push(row);
  });

  const totalComprobantes = comprobanteMap.size;
  let comprobantesQueCumplen = 0;

  comprobanteMap.forEach((filasDelComprobante) => {
    const algunaCumple = filasDelComprobante.some((fila) => fila.cumple_final === 1);
    if (algunaCumple) {
      comprobantesQueCumplen += 1;
    }
  });

  const comprobantesNoCumplen = totalComprobantes - comprobantesQueCumplen;
  const scoreCumplimiento = totalComprobantes === 0 ? 1 : comprobantesQueCumplen / totalComprobantes;
  const resultadoFinal = (control.ponderacion || 0) * scoreCumplimiento;

  await runAsync(
    `UPDATE controles
     SET total_items = ?, items_observacion = ?, score_cumplimiento = ?, resultado_final = ?
     WHERE id = ?`,
    [totalComprobantes, comprobantesNoCumplen, scoreCumplimiento, resultadoFinal, control.id]
  );

  const auditSummary = await recalculateAudit(auditoriaId);

  return {
    controlId: control.id,
    total: totalComprobantes,
    totalMuestra: totalComprobantes,
    cumplen: comprobantesQueCumplen,
    observadas: comprobantesNoCumplen,
    scoreCumplimiento,
    resultadoFinal,
    auditSummary
  };
}

export async function importVentasInternasFromWorkbook({ auditoria, fileName, buffer }) {
  const workbook = XLSX.read(buffer, { type: 'buffer', cellDates: true });
  const firstSheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[firstSheetName];
  const matrix = XLSX.utils.sheet_to_json(worksheet, {
    header: 1,
    defval: null,
    raw: false,
    blankrows: false
  });

  const headerIndex = findHeaderIndex(matrix);
  if (headerIndex < 0) {
    throw new Error('No se pudo detectar el encabezado del reporte de ventas internas');
  }

  const rows = extractVentasFromMatrix(matrix, headerIndex);
  if (!rows.length) {
    throw new Error('El reporte no contiene ventas internas válidas para importar');
  }

  const control = await getAsync(
    `SELECT id FROM controles WHERE auditoria_id = ? AND modulo_numero = 8`,
    [auditoria.id]
  );

  if (!control) {
    throw new Error('La auditoría no tiene creado el módulo 8');
  }

  const sampleData = buildSampleVtaMostrador(rows);
  const sampleSet = sampleData.sampledRows;

  await runAsync(`DELETE FROM ventas_internas WHERE auditoria_id = ?`, [auditoria.id]);

  for (let index = 0; index < rows.length; index += 1) {
    const row = rows[index];
    const enMuestra = sampleSet.has(index) ? 1 : 0;
    const firmaDeposito = enMuestra ? 0 : 1;
    const firmaGerente = enMuestra ? 0 : 1;
    const justificado = 0;
    const cumpleFinal = enMuestra ? 0 : 1;

    await runAsync(
      `INSERT INTO ventas_internas (
        id, auditoria_id, control_id, fecha, tipo_comprobante, talonario,
        numero_comprobante, articulo_codigo, articulo_descripcion, imputacion_contable, importe, en_muestra,
        firma_responsable_deposito, firma_gerente_sector, justificado, cumple_final,
        observacion, origen_archivo, raw_data
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)` ,
      [
        uuidv4(),
        auditoria.id,
        control.id,
        row.fecha,
        row.tipo_comprobante || null,
        row.talonario || null,
        row.numero_comprobante || null,
        row.articulo_codigo || null,
        row.articulo_descripcion || null,
        row.imputacion_contable || null,
        row.importe,
        enMuestra,
        firmaDeposito,
        firmaGerente,
        justificado,
        cumpleFinal,
        '',
        fileName,
        JSON.stringify(row.raw_data)
      ]
    );
  }

  const resumen = await recalculateVentasInternasModule(auditoria.id);

  return {
    importedCount: rows.length,
    hoja: firstSheetName,
    encabezadoDetectadoEnFila: headerIndex + 1,
    totalMuestra: sampleData.totalComprobantesMuestra,
    totalComprobantesVtaMostrador: sampleData.totalComprobantes,
    totalComprobantesMuestra: sampleData.totalComprobantesMuestra,
    resumen
  };
}
