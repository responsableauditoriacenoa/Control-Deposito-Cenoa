import express from 'express';
import multer from 'multer';
import { v4 as uuidv4 } from 'uuid';
import XLSX from 'xlsx';
import { runAsync, getAsync, allAsync } from '../db/database.js';
import { importTransferenciasFromWorkbook, recalculateTransferModule } from '../services/transferencias.js';
import { importCreditosFromWorkbook, recalculateCreditosModule } from '../services/creditos.js';
import { importVentasInternasFromWorkbook, recalculateVentasInternasModule } from '../services/ventasInternas.js';

const router = express.Router();
const upload = multer({ storage: multer.memoryStorage() });

const MODULO_NOMBRES = {
  1: '1. Transf. Pend. de Recepción',
  2: '2. Pendientes de Crédito',
  3: '3. Remito de Compras',
  4: '4. Rdo. Inv. Rotativo',
  7: '5. Remitos Pend. de Facturación',
  8: '6. Ventas Internas Directas',
  9: '7. Transf. Pend. De Entrega'
};

const MODULOS_ACTIVOS = [1, 2, 3, 4, 7, 8, 9];
const EMPRESAS_DEFAULT = ['Autosol', 'Autolux', 'Ciel', 'Neumaticos Alte. Brown', 'VOGE'];
const SUCURSALES_POR_EMPRESA_DEFAULT = {
  'Autolux': [
    'Casa Central - Jujuy',
    'Suc. Salta PosVenta',
    'Suc. Tartagal',
    'Suc. Las Lajitas',
    'Chapa y Pintura Autolux Salta'
  ],
  'Autosol': [
    'Casa Central - Jujuy',
    'Suc. Salta Posventa',
    'Suc. Taller Express',
    'Suc. Tartagal'
  ],
  'Ciel': ['Casa Central Jujuy'],
  'Neumaticos Alte. Brown': ['SUC. LAS LOMAS', 'SUC. ALTE. BROWN'],
  'VOGE': ['Voge Salta']
};
const ETAPAS_POR_MODULO = {
  1: 'Entradas',
  2: 'Entradas',
  3: 'Entradas',
  4: 'Stock',
  7: 'Salidas',
  8: 'Salidas',
  9: 'Salidas'
};

function normalizePonderaciones(input) {
  const raw = input || {};
  const values = MODULOS_ACTIVOS.map((modulo) => {
    const value = Number(raw[String(modulo)] ?? raw[modulo]);
    return Number.isFinite(value) && value > 0 ? value : 0;
  });

  const sum = values.reduce((accumulator, value) => accumulator + value, 0);
  if (sum <= 0) {
    const equal = 1 / MODULOS_ACTIVOS.length;
    return Object.fromEntries(MODULOS_ACTIVOS.map((modulo) => [String(modulo), equal]));
  }

  return Object.fromEntries(
    MODULOS_ACTIVOS.map((modulo, index) => [String(modulo), values[index] / sum])
  );
}

function normalizeSucursalesPorEmpresa(empresas, sucursalesPorEmpresaInput = {}) {
  const result = {};

  empresas.forEach((empresa) => {
    const rawList = Array.isArray(sucursalesPorEmpresaInput[empresa])
      ? sucursalesPorEmpresaInput[empresa]
      : [];

    result[empresa] = [...new Set(rawList.map((item) => String(item || '').trim()).filter(Boolean))];
  });

  return result;
}

async function getConfigValue(nombre, fallbackValue) {
  const row = await getAsync(
    `SELECT valor FROM configuracion WHERE nombre_config = ? ORDER BY fecha_actualizacion DESC LIMIT 1`,
    [nombre]
  );

  if (!row) return fallbackValue;

  try {
    return JSON.parse(row.valor);
  } catch {
    return fallbackValue;
  }
}

async function setConfigValue(nombre, value) {
  const serialized = JSON.stringify(value);
  const existing = await getAsync(
    `SELECT id FROM configuracion WHERE nombre_config = ? ORDER BY fecha_actualizacion DESC LIMIT 1`,
    [nombre]
  );

  if (existing?.id) {
    await runAsync(
      `UPDATE configuracion
       SET valor = ?, fecha_actualizacion = CURRENT_TIMESTAMP
       WHERE id = ?`,
      [serialized, existing.id]
    );
    return;
  }

  await runAsync(
    `INSERT INTO configuracion (id, nombre_config, valor)
     VALUES (?, ?, ?)`,
    [uuidv4(), nombre, serialized]
  );
}

async function recalculateAllAuditsScoreByActiveModules() {
  const auditorias = await allAsync(`SELECT id FROM auditorias WHERE activa = 1`);

  for (const auditoria of auditorias) {
    const controls = await allAsync(
      `SELECT resultado_final FROM controles
       WHERE auditoria_id = ? AND modulo_numero IN (1, 2, 3, 4, 7, 8, 9)`,
      [auditoria.id]
    );

    const scoreFinal = controls.reduce(
      (accumulator, control) => accumulator + Number(control.resultado_final || 0),
      0
    );

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
      [scoreFinal, calificacion, auditoria.id]
    );
  }
}

router.get('/configuracion', async (_req, res) => {
  try {
    const empresas = await getConfigValue('empresas', EMPRESAS_DEFAULT);
    const sucursalesPorEmpresaRaw = await getConfigValue('sucursales_por_empresa', SUCURSALES_POR_EMPRESA_DEFAULT);
    const sucursalesPorEmpresa = normalizeSucursalesPorEmpresa(empresas, sucursalesPorEmpresaRaw);
    const empresaDefault = await getConfigValue('empresa_default', EMPRESAS_DEFAULT[0]);
    const ponderaciones = normalizePonderaciones(await getConfigValue('ponderaciones', null));

    res.json({
      modulosActivos: MODULOS_ACTIVOS,
      empresas,
      empresaDefault,
      sucursalesPorEmpresa,
      sucursales: Object.values(sucursalesPorEmpresa).flat(),
      ponderaciones,
      nombresModulos: MODULO_NOMBRES,
      etapasPorModulo: ETAPAS_POR_MODULO
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.patch('/configuracion', async (req, res) => {
  try {
    const empresasRaw = Array.isArray(req.body.empresas) ? req.body.empresas : EMPRESAS_DEFAULT;
    const empresaDefaultRaw = req.body.empresa_default;
    const ponderaciones = normalizePonderaciones(req.body.ponderaciones || {});

    const empresas = [...new Set(empresasRaw.map((item) => String(item || '').trim()).filter(Boolean))];
    const sucursalesPorEmpresa = normalizeSucursalesPorEmpresa(empresas, req.body.sucursales_por_empresa || {});
    const sucursales = Object.values(sucursalesPorEmpresa).flat();
    const empresaDefault = empresas.includes(empresaDefaultRaw) ? empresaDefaultRaw : (empresas[0] || 'Autosol');

    if (!empresas.length) {
      return res.status(400).json({ error: 'Debe existir al menos una empresa en configuración' });
    }

    if (!sucursales.length) {
      return res.status(400).json({ error: 'Debe existir al menos una sucursal asociada a una empresa' });
    }

    await setConfigValue('empresas', empresas);
    await setConfigValue('sucursales', sucursales);
    await setConfigValue('sucursales_por_empresa', sucursalesPorEmpresa);
    await setConfigValue('empresa_default', empresaDefault);
    await setConfigValue('ponderaciones', ponderaciones);

    for (const modulo of MODULOS_ACTIVOS) {
      const ponderacion = Number(ponderaciones[String(modulo)] || 0);

      await runAsync(
        `UPDATE controles
         SET ponderacion = ?,
             resultado_final = COALESCE(score_cumplimiento, 0) * ?
         WHERE modulo_numero = ?`,
        [ponderacion, ponderacion, modulo]
      );
    }

    await runAsync(
      `UPDATE controles SET ponderacion = 0, resultado_final = 0 WHERE modulo_numero IN (5, 6)`
    );

    await recalculateAllAuditsScoreByActiveModules();

    res.json({
      mensaje: 'Configuración actualizada',
      configuracion: {
        modulosActivos: MODULOS_ACTIVOS,
        empresas,
        empresaDefault,
        sucursalesPorEmpresa,
        sucursales,
        ponderaciones,
        nombresModulos: MODULO_NOMBRES,
        etapasPorModulo: ETAPAS_POR_MODULO
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

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

// Crear nueva auditoría
router.post('/', async (req, res) => {
  try {
    const { codigo, auditor_id, sucursal, fecha_realizacion, empresa } = req.body;
    
    if (!codigo || !auditor_id || !sucursal || !fecha_realizacion) {
      return res.status(400).json({ error: 'Campos requeridos incompletos' });
    }

    const empresaConfigDefault = await getConfigValue('empresa_default', 'Autosol');
    const empresaFinal = String(empresa || empresaConfigDefault || 'Autosol').trim();
    const sucursalesPorEmpresa = await getConfigValue('sucursales_por_empresa', SUCURSALES_POR_EMPRESA_DEFAULT);
    const sucursalesEmpresaSeleccionada = Array.isArray(sucursalesPorEmpresa?.[empresaFinal])
      ? sucursalesPorEmpresa[empresaFinal]
      : [];

    if (!sucursalesEmpresaSeleccionada.includes(sucursal)) {
      return res.status(400).json({ error: 'La sucursal seleccionada no corresponde a la empresa elegida' });
    }

    const id = uuidv4();
    await runAsync(
      `INSERT INTO auditorias (id, codigo, auditor_id, empresa, sucursal, fecha_realizacion, estado)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [id, codigo, auditor_id, empresaFinal, sucursal, fecha_realizacion, 'en_progreso']
    );

    res.status(201).json({ id, codigo, mensaje: 'Auditoría creada' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Listar todas las auditorías
router.get('/', async (req, res) => {
  try {
    const auditorias = await allAsync(
      `SELECT a.*, u.nombre as auditor_nombre FROM auditorias a
       LEFT JOIN auditores u ON a.auditor_id = u.id
       WHERE a.activa = 1
       ORDER BY a.fecha_creacion DESC`
    );
    res.json(auditorias);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Listar informes (auditorías cerradas)
router.get('/informes', async (_req, res) => {
  try {
    const informes = await allAsync(
      `SELECT a.id, a.codigo, a.empresa, a.sucursal, a.fecha_realizacion, a.fecha_cierre,
              a.score_final, a.calificacion, a.hallazgos, a.recomendaciones,
              u.nombre as auditor_nombre
       FROM auditorias a
       LEFT JOIN auditores u ON a.auditor_id = u.id
       WHERE a.activa = 1 AND a.estado = 'completada'
       ORDER BY COALESCE(a.fecha_cierre, a.fecha_actualizacion, a.fecha_realizacion) DESC`
    );

    res.json(informes);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get detalle de una auditoría con sus controles
router.get('/:auditoria_id', async (req, res) => {
  try {
    const { auditoria_id } = req.params;
    
    const auditoria = await getAsync(
      `SELECT a.*, u.nombre as auditor_nombre FROM auditorias a
       LEFT JOIN auditores u ON a.auditor_id = u.id
       WHERE a.id = ? AND a.activa = 1`,
      [auditoria_id]
    );

    if (!auditoria) {
      return res.status(404).json({ error: 'Auditoría no encontrada' });
    }

    const controles = await allAsync(
      `SELECT * FROM controles WHERE auditoria_id = ? ORDER BY modulo_numero`,
      [auditoria_id]
    );

    res.json({ auditoria, controles });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/:auditoria_id/transferencias/import', upload.single('archivo'), async (req, res) => {
  try {
    const { auditoria_id } = req.params;
    const auditoria = await getAsync(
      `SELECT * FROM auditorias WHERE id = ? AND activa = 1`,
      [auditoria_id]
    );

    if (!auditoria) {
      return res.status(404).json({ error: 'Auditoría no encontrada' });
    }

    if (!req.file) {
      return res.status(400).json({ error: 'Debes adjuntar un archivo Excel' });
    }

    const resultado = await importTransferenciasFromWorkbook({
      auditoria,
      fileName: req.file.originalname,
      buffer: req.file.buffer
    });

    res.json(resultado);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/:auditoria_id/creditos/import', upload.single('archivo'), async (req, res) => {
  try {
    const { auditoria_id } = req.params;
    const auditoria = await getAsync(
      `SELECT * FROM auditorias WHERE id = ? AND activa = 1`,
      [auditoria_id]
    );

    if (!auditoria) {
      return res.status(404).json({ error: 'Auditoría no encontrada' });
    }

    if (!req.file) {
      return res.status(400).json({ error: 'Debes adjuntar un archivo Excel' });
    }

    const resultado = await importCreditosFromWorkbook({
      auditoria,
      fileName: req.file.originalname,
      buffer: req.file.buffer
    });

    res.json(resultado);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/:auditoria_id/ventas-internas/import', upload.single('archivo'), async (req, res) => {
  try {
    const { auditoria_id } = req.params;
    const auditoria = await getAsync(
      `SELECT * FROM auditorias WHERE id = ? AND activa = 1`,
      [auditoria_id]
    );

    if (!auditoria) {
      return res.status(404).json({ error: 'Auditoría no encontrada' });
    }

    if (!req.file) {
      return res.status(400).json({ error: 'Debes adjuntar un archivo Excel' });
    }

    const resultado = await importVentasInternasFromWorkbook({
      auditoria,
      fileName: req.file.originalname,
      buffer: req.file.buffer
    });

    res.json(resultado);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/:auditoria_id/creditos', async (req, res) => {
  try {
    const { auditoria_id } = req.params;
    const control = await getAsync(
      `SELECT * FROM controles WHERE auditoria_id = ? AND modulo_numero = 2`,
      [auditoria_id]
    );

    if (!control) {
      return res.status(404).json({ error: 'Control del módulo 2 no encontrado' });
    }

    const creditos = await allAsync(
      `SELECT * FROM creditos_pendientes WHERE auditoria_id = ? ORDER BY fecha ASC, numero_comprobante ASC`,
      [auditoria_id]
    );

    res.json({ control, creditos });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.patch('/:auditoria_id/creditos/:credito_id', async (req, res) => {
  try {
    const { auditoria_id, credito_id } = req.params;
    const { tiene_reclamo = false, observacion = '' } = req.body;

    const credito = await getAsync(
      `SELECT * FROM creditos_pendientes WHERE id = ? AND auditoria_id = ?`,
      [credito_id, auditoria_id]
    );

    if (!credito) {
      return res.status(404).json({ error: 'Registro de crédito no encontrado' });
    }

    const tieneReclamoInt = tiene_reclamo ? 1 : 0;
    const cumpleFinal = tieneReclamoInt === 1 ? 1 : 0;

    await runAsync(
      `UPDATE creditos_pendientes
       SET tiene_reclamo = ?, cumple_final = ?, observacion = ?, fecha_actualizacion = CURRENT_TIMESTAMP
       WHERE id = ? AND auditoria_id = ?`,
      [tieneReclamoInt, cumpleFinal, observacion, credito_id, auditoria_id]
    );

    const resumen = await recalculateCreditosModule(auditoria_id);
    res.json({ mensaje: 'Registro de crédito actualizado', resumen });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/:auditoria_id/ventas-internas', async (req, res) => {
  try {
    const { auditoria_id } = req.params;
    const control = await getAsync(
      `SELECT * FROM controles WHERE auditoria_id = ? AND modulo_numero = 8`,
      [auditoria_id]
    );

    if (!control) {
      return res.status(404).json({ error: 'Control del módulo 8 no encontrado' });
    }

    const ventasInternas = await allAsync(
      `SELECT * FROM ventas_internas
       WHERE auditoria_id = ?
       ORDER BY en_muestra DESC, fecha ASC, numero_comprobante ASC`,
      [auditoria_id]
    );

    const vtaMostradorRows = ventasInternas.filter((item) => isMostradorSale(item.tipo_comprobante));
    const totalComprobantesVtaMostrador = new Set(
      vtaMostradorRows.map((item) => String(item.numero_comprobante || item.id))
    ).size;
    const totalComprobantesMuestra = new Set(
      vtaMostradorRows
        .filter((item) => item.en_muestra === 1)
        .map((item) => String(item.numero_comprobante || item.id))
    ).size;
    const totalMuestra = totalComprobantesMuestra;

    res.json({
      control,
      totalMuestra,
      totalComprobantesVtaMostrador,
      totalComprobantesMuestra,
      ventasInternas
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/:auditoria_id/ventas-internas/export', async (req, res) => {
  try {
    const { auditoria_id } = req.params;

    const auditoria = await getAsync(
      `SELECT * FROM auditorias WHERE id = ? AND activa = 1`,
      [auditoria_id]
    );

    if (!auditoria) {
      return res.status(404).json({ error: 'Auditoría no encontrada' });
    }

    const rows = await allAsync(
      `SELECT * FROM ventas_internas
       WHERE auditoria_id = ? AND en_muestra = 1
       ORDER BY fecha ASC, numero_comprobante ASC`,
      [auditoria_id]
    );

    if (!rows.length) {
      return res.status(400).json({ error: 'No hay muestra generada para exportar' });
    }

    const groupedByComprobante = new Map();
    rows.forEach((row) => {
      const key = String(row.numero_comprobante || row.id);
      if (!groupedByComprobante.has(key)) {
        groupedByComprobante.set(key, []);
      }
      groupedByComprobante.get(key).push(row);
    });

    const exportRows = Array.from(groupedByComprobante.values()).map((items) => {
      const first = items[0];
      const articulos = items
        .map((item) => `${item.articulo_codigo || '-'} / ${item.articulo_descripcion || '-'}`)
        .join(' | ');
      const importeTotal = items.reduce((acc, item) => acc + Number(item.importe || 0), 0);
      const cumpleComprobante = items.some((item) => item.cumple_final === 1) ? 'Si cumple' : 'No cumple';

      return {
        Fecha: first.fecha ? new Date(first.fecha).toLocaleDateString('es-AR') : '',
        Comprobante: first.tipo_comprobante || '',
        NumeroComprobante: first.numero_comprobante || '',
        Articulos: articulos,
        CantidadLineas: items.length,
        ImputacionContable: first.imputacion_contable || '',
        ImporteTotalComprobante: Number(importeTotal.toFixed(2)),
        FirmaDeposito: first.firma_responsable_deposito === 1 ? 'Si' : 'No',
        FirmaGerenteJefe: first.firma_gerente_sector === 1 ? 'Si' : 'No',
        Justificado: first.justificado === 1 ? 'Si' : 'No',
        Cumple: cumpleComprobante,
        Observacion: first.observacion || ''
      };
    });

    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.json_to_sheet(exportRows);
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Muestra Ventas Internas');

    const fileBuffer = XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' });
    const timeStamp = new Date().toISOString().slice(0, 10);
    const fileName = `muestra_ventas_internas_${auditoria.codigo || auditoria_id}_${timeStamp}.xlsx`;

    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', `attachment; filename="${fileName}"`);
    res.send(fileBuffer);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.patch('/:auditoria_id/ventas-internas/:venta_id', async (req, res) => {
  try {
    const { auditoria_id, venta_id } = req.params;
    const {
      firma_responsable_deposito = false,
      firma_gerente_sector = false,
      justificado = false,
      observacion = ''
    } = req.body;

    const venta = await getAsync(
      `SELECT * FROM ventas_internas WHERE id = ? AND auditoria_id = ?`,
      [venta_id, auditoria_id]
    );

    if (!venta) {
      return res.status(404).json({ error: 'Venta interna no encontrada' });
    }

    const firmaDepositoInt = firma_responsable_deposito ? 1 : 0;
    const firmaGerenteInt = firma_gerente_sector ? 1 : 0;
    const justificadoInt = justificado ? 1 : 0;
    const cumpleFinal = (firmaDepositoInt === 1 && firmaGerenteInt === 1) || justificadoInt === 1 ? 1 : 0;

    await runAsync(
      `UPDATE ventas_internas
       SET firma_responsable_deposito = ?,
           firma_gerente_sector = ?,
           justificado = ?,
           cumple_final = ?,
           observacion = ?,
           fecha_actualizacion = CURRENT_TIMESTAMP
       WHERE id = ? AND auditoria_id = ?`,
      [
        firmaDepositoInt,
        firmaGerenteInt,
        justificadoInt,
        cumpleFinal,
        observacion,
        venta_id,
        auditoria_id
      ]
    );

    const resumen = await recalculateVentasInternasModule(auditoria_id);
    res.json({ mensaje: 'Venta interna actualizada', resumen });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/:auditoria_id/transferencias/:modulo_numero', async (req, res) => {
  try {
    const { auditoria_id, modulo_numero } = req.params;
    const modulo = Number(modulo_numero);

    if (![1, 9].includes(modulo)) {
      return res.status(400).json({ error: 'Solo están habilitados los módulos 1 y 9' });
    }

    const control = await getAsync(
      `SELECT * FROM controles WHERE auditoria_id = ? AND modulo_numero = ?`,
      [auditoria_id, modulo]
    );

    if (!control) {
      return res.status(404).json({ error: 'Control no encontrado' });
    }

    const transferencias = await allAsync(
      `SELECT * FROM transferencias WHERE auditoria_id = ? AND modulo_numero = ? ORDER BY dias_habiles DESC, fecha_transferencia ASC`,
      [auditoria_id, modulo]
    );

    res.json({ control, transferencias });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.patch('/:auditoria_id/transferencias/:transferencia_id', async (req, res) => {
  try {
    const { auditoria_id, transferencia_id } = req.params;
    const { observacion = '', justificado = false } = req.body;

    const transferencia = await getAsync(
      `SELECT * FROM transferencias WHERE id = ? AND auditoria_id = ?`,
      [transferencia_id, auditoria_id]
    );

    if (!transferencia) {
      return res.status(404).json({ error: 'Transferencia no encontrada' });
    }

    const cumpleFinal = transferencia.cumple_base === 1 || justificado ? 1 : 0;

    await runAsync(
      `UPDATE transferencias
       SET observacion = ?, justificado = ?, cumple_final = ?, fecha_actualizacion = CURRENT_TIMESTAMP
       WHERE id = ? AND auditoria_id = ?`,
      [observacion, justificado ? 1 : 0, cumpleFinal, transferencia_id, auditoria_id]
    );

    const resumen = await recalculateTransferModule(auditoria_id, transferencia.modulo_numero);

    res.json({ mensaje: 'Transferencia actualizada', resumen });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Actualizar score y calificación de auditoría
router.patch('/:auditoria_id/resultado', async (req, res) => {
  try {
    const { auditoria_id } = req.params;
    const { score_final, calificacion, estado } = req.body;

    await runAsync(
      `UPDATE auditorias 
       SET score_final = ?, calificacion = ?, estado = ?, fecha_actualizacion = CURRENT_TIMESTAMP
       WHERE id = ?`,
      [score_final, calificacion, estado || 'completada', auditoria_id]
    );

    res.json({ mensaje: 'Auditoría actualizada', auditoria_id });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Crear control dentro de una auditoría
router.post('/:auditoria_id/controles', async (req, res) => {
  try {
    const { auditoria_id } = req.params;
    const { modulo_numero, modulo_nombre, etapa, ponderacion } = req.body;
    const moduloNumero = Number(modulo_numero);

    if (!MODULOS_ACTIVOS.includes(moduloNumero)) {
      return res.status(400).json({ error: 'Ese indicador no está habilitado en la configuración actual' });
    }

    const nombreCanonico = MODULO_NOMBRES[Number(modulo_numero)] || modulo_nombre;

    const id = uuidv4();
    await runAsync(
      `INSERT INTO controles (id, auditoria_id, modulo_numero, modulo_nombre, etapa, ponderacion)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [id, auditoria_id, moduloNumero, nombreCanonico, etapa, ponderacion]
    );

    res.status(201).json({ id, mensaje: 'Control creado' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Actualizar control (score y observaciones)
router.patch('/:auditoria_id/controles/:control_id', async (req, res) => {
  try {
    const { auditoria_id, control_id } = req.params;
    const { score_cumplimiento, resultado_final, total_items, items_observacion, observaciones } = req.body;

    await runAsync(
      `UPDATE controles 
       SET score_cumplimiento = ?, resultado_final = ?, total_items = ?, items_observacion = ?, observaciones = ?
       WHERE id = ? AND auditoria_id = ?`,
      [score_cumplimiento, resultado_final, total_items, items_observacion, observaciones, control_id, auditoria_id]
    );

    res.json({ mensaje: 'Control actualizado', control_id });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.patch('/:auditoria_id/cierre', async (req, res) => {
  try {
    const { auditoria_id } = req.params;
    const hallazgos = String(req.body.hallazgos || '').trim();
    const recomendaciones = String(req.body.recomendaciones || '').trim();

    const auditoria = await getAsync(
      `SELECT * FROM auditorias WHERE id = ? AND activa = 1`,
      [auditoria_id]
    );

    if (!auditoria) {
      return res.status(404).json({ error: 'Auditoría no encontrada' });
    }

    if (!hallazgos || !recomendaciones) {
      return res.status(400).json({ error: 'Debes cargar hallazgos y recomendaciones para cerrar la auditoría' });
    }

    const controles = await allAsync(
      `SELECT * FROM controles WHERE auditoria_id = ? AND modulo_numero IN (1, 2, 3, 4, 7, 8, 9) ORDER BY modulo_numero`,
      [auditoria_id]
    );

    if (!controles.length) {
      return res.status(400).json({ error: 'No hay indicadores cargados para cerrar la auditoría' });
    }

    const faltantes = controles
      .filter((control) => !Number.isFinite(Number(control.score_cumplimiento)))
      .map((control) => control.modulo_nombre || `Módulo ${control.modulo_numero}`);

    if (faltantes.length) {
      return res.status(400).json({
        error: 'Todos los indicadores deben tener % de cumplimiento antes del cierre',
        faltantes
      });
    }

    const scoreFinal = controles.reduce(
      (accumulator, control) => accumulator + Number(control.resultado_final || 0),
      0
    );

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
       SET hallazgos = ?,
           recomendaciones = ?,
           estado = 'completada',
           score_final = ?,
           calificacion = ?,
           fecha_cierre = CURRENT_TIMESTAMP,
           fecha_actualizacion = CURRENT_TIMESTAMP
       WHERE id = ?`,
      [hallazgos, recomendaciones, scoreFinal, calificacion, auditoria_id]
    );

    const auditoriaActualizada = await getAsync(
      `SELECT a.*, u.nombre as auditor_nombre FROM auditorias a
       LEFT JOIN auditores u ON a.auditor_id = u.id
       WHERE a.id = ? AND a.activa = 1`,
      [auditoria_id]
    );

    res.json({ mensaje: 'Auditoría cerrada correctamente', auditoria: auditoriaActualizada });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.patch('/:auditoria_id/cierre-borrador', async (req, res) => {
  try {
    const { auditoria_id } = req.params;
    const hallazgos = String(req.body.hallazgos || '').trim();
    const recomendaciones = String(req.body.recomendaciones || '').trim();

    const auditoria = await getAsync(
      `SELECT * FROM auditorias WHERE id = ? AND activa = 1`,
      [auditoria_id]
    );

    if (!auditoria) {
      return res.status(404).json({ error: 'Auditoría no encontrada' });
    }

    await runAsync(
      `UPDATE auditorias
       SET hallazgos = ?, recomendaciones = ?, fecha_actualizacion = CURRENT_TIMESTAMP
       WHERE id = ?`,
      [hallazgos, recomendaciones, auditoria_id]
    );

    const auditoriaActualizada = await getAsync(
      `SELECT a.*, u.nombre as auditor_nombre FROM auditorias a
       LEFT JOIN auditores u ON a.auditor_id = u.id
       WHERE a.id = ? AND a.activa = 1`,
      [auditoria_id]
    );

    res.json({ mensaje: 'Borrador de cierre guardado', auditoria: auditoriaActualizada });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Agregar desvío a un control
router.post('/:auditoria_id/desvios', async (req, res) => {
  try {
    const { auditoria_id } = req.params;
    const { control_id, fecha, numero_comprobante, descripcion, impacto_monetary, dias_demora, observacion } = req.body;

    const id = uuidv4();
    await runAsync(
      `INSERT INTO desvios (id, control_id, auditoria_id, fecha, numero_comprobante, descripcion, impacto_monetary, dias_demora, observacion)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [id, control_id, auditoria_id, fecha, numero_comprobante, descripcion, impacto_monetary, dias_demora, observacion]
    );

    res.status(201).json({ id, mensaje: 'Desvío registrado' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Listar desvíos de un control
router.get('/:auditoria_id/desvios/:control_id', async (req, res) => {
  try {
    const { control_id, auditoria_id } = req.params;
    const desvios = await allAsync(
      `SELECT * FROM desvios WHERE control_id = ? AND auditoria_id = ? ORDER BY fecha DESC`,
      [control_id, auditoria_id]
    );
    res.json(desvios);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
