import sqlite3 from 'sqlite3';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const dbPath = join(__dirname, 'auditorias.db');

export const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Error abriendo base de datos:', err);
  } else {
    console.log('Conectado a SQLite3 en:', dbPath);
    // Espera hasta 5 s si la BD está ocupada (acceso concurrente multi-usuario)
    db.run('PRAGMA busy_timeout=5000');
  }
});

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
const PONDERACION_EQUIVALENTE = 1 / MODULOS_ACTIVOS.length;
const PONDERACIONES_DEFAULT = Object.fromEntries(
  MODULOS_ACTIVOS.map((modulo) => [String(modulo), PONDERACION_EQUIVALENTE])
);
const EMPRESAS_DEFAULT = [
  'Autosol',
  'Autolux',
  'Ciel',
  'Neumaticos Alte. Brown',
  'VOGE'
];
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
  'Ciel': [
    'Casa Central Jujuy'
  ],
  'Neumaticos Alte. Brown': [
    'SUC. LAS LOMAS',
    'SUC. ALTE. BROWN'
  ],
  'VOGE': [
    'Voge Salta'
  ]
};

const SUCURSALES_LEGACY = ['Casa Central Jujuy', 'Sucursal Salta', 'Tartagal'];

function normalizeList(list) {
  return [...new Set((list || []).map((item) => String(item || '').trim()).filter(Boolean))].sort();
}

function isLegacySucursalesPorEmpresaMapping(mapping) {
  const expected = normalizeList(SUCURSALES_LEGACY);
  return EMPRESAS_DEFAULT.every((empresa) => {
    const list = Array.isArray(mapping?.[empresa]) ? mapping[empresa] : [];
    const normalized = normalizeList(list);
    return normalized.length === expected.length
      && normalized.every((item, index) => item === expected[index]);
  });
}

export function initDb() {
  // WAL mode: permite lecturas concurrentes mientras hay una escritura (multi-usuario)
  db.run('PRAGMA journal_mode=WAL', (err) => {
    if (err) console.warn('WAL mode no disponible:', err.message);
  });

  // Tabla de auditores
  db.run(`
    CREATE TABLE IF NOT EXISTS auditores (
      id TEXT PRIMARY KEY,
      nombre TEXT NOT NULL UNIQUE,
      email TEXT,
      activo INTEGER DEFAULT 1,
      fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Tabla de auditorías
  db.run(`
    CREATE TABLE IF NOT EXISTS auditorias (
      id TEXT PRIMARY KEY,
      codigo TEXT NOT NULL UNIQUE,
      auditor_id TEXT NOT NULL,
      empresa TEXT DEFAULT 'Autosol',
      sucursal TEXT NOT NULL,
      fecha_realizacion TEXT NOT NULL,
      estado TEXT DEFAULT 'en_progreso',
      score_final REAL,
      calificacion TEXT,
      activa INTEGER DEFAULT 1,
      fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
      fecha_actualizacion TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(auditor_id) REFERENCES auditores(id)
    )
  `);

  db.run(`ALTER TABLE auditorias ADD COLUMN empresa TEXT DEFAULT 'Autosol'`, (err) => {
    if (err && !String(err.message || '').includes('duplicate column name')) {
      console.error('Error agregando empresa en auditorias:', err.message);
    }
  });

  db.run(`ALTER TABLE auditorias ADD COLUMN hallazgos TEXT DEFAULT ''`, (err) => {
    if (err && !String(err.message || '').includes('duplicate column name')) {
      console.error('Error agregando hallazgos en auditorias:', err.message);
    }
  });

  db.run(`ALTER TABLE auditorias ADD COLUMN recomendaciones TEXT DEFAULT ''`, (err) => {
    if (err && !String(err.message || '').includes('duplicate column name')) {
      console.error('Error agregando recomendaciones en auditorias:', err.message);
    }
  });

  db.run(`ALTER TABLE auditorias ADD COLUMN fecha_cierre TEXT`, (err) => {
    if (err && !String(err.message || '').includes('duplicate column name')) {
      console.error('Error agregando fecha_cierre en auditorias:', err.message);
    }
  });

  // Tabla de controles (9 módulos)
  db.run(`
    CREATE TABLE IF NOT EXISTS controles (
      id TEXT PRIMARY KEY,
      auditoria_id TEXT NOT NULL,
      modulo_numero INTEGER,
      modulo_nombre TEXT,
      etapa TEXT,
      ponderacion REAL,
      score_cumplimiento REAL,
      resultado_final REAL,
      total_items INTEGER,
      items_observacion INTEGER,
      observaciones TEXT,
      fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(auditoria_id) REFERENCES auditorias(id)
    )
  `);

  // Tabla de desvíos (detalle de observaciones)
  db.run(`
    CREATE TABLE IF NOT EXISTS desvios (
      id TEXT PRIMARY KEY,
      control_id TEXT NOT NULL,
      auditoria_id TEXT NOT NULL,
      fecha TEXT,
      numero_comprobante TEXT,
      descripcion TEXT,
      impacto_monetary REAL,
      dias_demora INTEGER,
      observacion TEXT,
      estado TEXT DEFAULT 'registrado',
      fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(control_id) REFERENCES controles(id),
      FOREIGN KEY(auditoria_id) REFERENCES auditorias(id)
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS transferencias (
      id TEXT PRIMARY KEY,
      auditoria_id TEXT NOT NULL,
      control_id TEXT NOT NULL,
      modulo_numero INTEGER NOT NULL,
      fecha_transferencia TEXT,
      numero_comprobante TEXT,
      sucursal_origen TEXT,
      sucursal_destino TEXT,
      valorizacion_total REAL,
      dias_habiles INTEGER DEFAULT 0,
      cumple_base INTEGER DEFAULT 1,
      justificado INTEGER DEFAULT 0,
      cumple_final INTEGER DEFAULT 1,
      observacion TEXT,
      origen_archivo TEXT,
      raw_data TEXT,
      fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
      fecha_actualizacion TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(auditoria_id) REFERENCES auditorias(id),
      FOREIGN KEY(control_id) REFERENCES controles(id)
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS creditos_pendientes (
      id TEXT PRIMARY KEY,
      auditoria_id TEXT NOT NULL,
      control_id TEXT NOT NULL,
      fecha TEXT,
      articulo TEXT,
      numero_comprobante TEXT,
      sucursal_origen TEXT,
      sucursal_destino TEXT,
      cantidad REAL,
      importe REAL,
      tiene_reclamo INTEGER DEFAULT 0,
      cumple_final INTEGER DEFAULT 1,
      observacion TEXT,
      origen_archivo TEXT,
      raw_data TEXT,
      fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
      fecha_actualizacion TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(auditoria_id) REFERENCES auditorias(id),
      FOREIGN KEY(control_id) REFERENCES controles(id)
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS ventas_internas (
      id TEXT PRIMARY KEY,
      auditoria_id TEXT NOT NULL,
      control_id TEXT NOT NULL,
      fecha TEXT,
      tipo_comprobante TEXT,
      talonario TEXT,
      numero_comprobante TEXT,
      articulo_codigo TEXT,
      articulo_descripcion TEXT,
      imputacion_contable TEXT,
      importe REAL,
      en_muestra INTEGER DEFAULT 0,
      firma_responsable_deposito INTEGER DEFAULT 0,
      firma_gerente_sector INTEGER DEFAULT 0,
      justificado INTEGER DEFAULT 0,
      cumple_final INTEGER DEFAULT 0,
      observacion TEXT,
      origen_archivo TEXT,
      raw_data TEXT,
      fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
      fecha_actualizacion TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(auditoria_id) REFERENCES auditorias(id),
      FOREIGN KEY(control_id) REFERENCES controles(id)
    )
  `);

  db.run(`ALTER TABLE ventas_internas ADD COLUMN articulo_codigo TEXT`, (err) => {
    if (err && !String(err.message || '').includes('duplicate column name')) {
      console.error('Error agregando articulo_codigo en ventas_internas:', err.message);
    }
  });

  db.run(`ALTER TABLE ventas_internas ADD COLUMN articulo_descripcion TEXT`, (err) => {
    if (err && !String(err.message || '').includes('duplicate column name')) {
      console.error('Error agregando articulo_descripcion en ventas_internas:', err.message);
    }
  });

  // Tabla de configuración de sede/sucursal
  db.run(`
    CREATE TABLE IF NOT EXISTS configuracion (
      id TEXT PRIMARY KEY,
      nombre_config TEXT,
      valor TEXT,
      fecha_actualizacion TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `);

  db.run(
    `INSERT INTO configuracion (id, nombre_config, valor)
     SELECT 'cfg_modulos_activos', 'modulos_activos', ?
     WHERE NOT EXISTS (
       SELECT 1 FROM configuracion WHERE nombre_config = 'modulos_activos'
     )`,
    [JSON.stringify(MODULOS_ACTIVOS)]
  );

  db.run(
    `INSERT INTO configuracion (id, nombre_config, valor)
     SELECT 'cfg_ponderaciones', 'ponderaciones', ?
     WHERE NOT EXISTS (
       SELECT 1 FROM configuracion WHERE nombre_config = 'ponderaciones'
     )`,
    [JSON.stringify(PONDERACIONES_DEFAULT)]
  );

  db.run(
    `INSERT INTO configuracion (id, nombre_config, valor)
     SELECT 'cfg_empresas', 'empresas', ?
     WHERE NOT EXISTS (
       SELECT 1 FROM configuracion WHERE nombre_config = 'empresas'
     )`,
    [JSON.stringify(EMPRESAS_DEFAULT)]
  );

  db.run(
    `INSERT INTO configuracion (id, nombre_config, valor)
     SELECT 'cfg_empresa_default', 'empresa_default', ?
     WHERE NOT EXISTS (
       SELECT 1 FROM configuracion WHERE nombre_config = 'empresa_default'
     )`,
    [JSON.stringify('Autosol')]
  );

  db.run(
    `INSERT INTO configuracion (id, nombre_config, valor)
     SELECT 'cfg_sucursales', 'sucursales', ?
     WHERE NOT EXISTS (
       SELECT 1 FROM configuracion WHERE nombre_config = 'sucursales'
     )`,
    [JSON.stringify(Object.values(SUCURSALES_POR_EMPRESA_DEFAULT).flat())]
  );

  db.run(
    `INSERT INTO configuracion (id, nombre_config, valor)
     SELECT 'cfg_sucursales_por_empresa', 'sucursales_por_empresa', ?
     WHERE NOT EXISTS (
       SELECT 1 FROM configuracion WHERE nombre_config = 'sucursales_por_empresa'
     )`,
    [JSON.stringify(SUCURSALES_POR_EMPRESA_DEFAULT)]
  );

  db.get(
    `SELECT id, valor FROM configuracion WHERE nombre_config = 'sucursales_por_empresa' ORDER BY fecha_actualizacion DESC LIMIT 1`,
    [],
    (err, row) => {
      if (err || !row) return;

      let parsed = null;
      try {
        parsed = JSON.parse(row.valor);
      } catch {
        parsed = null;
      }

      if (!parsed || isLegacySucursalesPorEmpresaMapping(parsed)) {
        db.run(
          `UPDATE configuracion
           SET valor = ?, fecha_actualizacion = CURRENT_TIMESTAMP
           WHERE id = ?`,
          [JSON.stringify(SUCURSALES_POR_EMPRESA_DEFAULT), row.id]
        );

        db.run(
          `UPDATE configuracion
           SET valor = ?, fecha_actualizacion = CURRENT_TIMESTAMP
           WHERE nombre_config = 'sucursales'`,
          [JSON.stringify(Object.values(SUCURSALES_POR_EMPRESA_DEFAULT).flat())]
        );
      }
    }
  );

  Object.entries(MODULO_NOMBRES).forEach(([moduloNumero, nombre]) => {
    db.run(
      `UPDATE controles SET modulo_nombre = ? WHERE modulo_numero = ?`,
      [nombre, Number(moduloNumero)]
    );
  });

  console.log('Tablas de base de datos inicializadas');
}

export function runAsync(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function(err) {
      if (err) reject(err);
      else resolve({ id: this.lastID, changes: this.changes });
    });
  });
}

export function getAsync(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => {
      if (err) reject(err);
      else resolve(row);
    });
  });
}

export function allAsync(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) reject(err);
      else resolve(rows || []);
    });
  });
}

export function execAsync(sql) {
  return new Promise((resolve, reject) => {
    db.exec(sql, (err) => {
      if (err) reject(err);
      else resolve();
    });
  });
}
