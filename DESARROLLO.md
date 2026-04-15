# Guía de Desarrollo - Sistema de Auditoría

## 🚀 Quick Start

### 1. Iniciar Backend

```bash
cd backend
npm install  # Solo la primera vez
npm start    # O: node server.js
```

Backend disponible en: **http://localhost:5000**

### 2. Iniciar Frontend

Opción A - Con Python:
```bash
cd frontend
python -m http.server 3000
```

Opción B - Con Node.js:
```bash
cd frontend
npx http-server -p 3000
```

Frontend disponible en: **http://localhost:3000**

---

## 📡 API REST - Endpoints Disponibles

### Auditorías

#### Crear auditoría
```
POST /api/auditorias
Body: {
  "codigo": "PROG-858",
  "auditor_id": "AUD_GUSTAVO_ZAMBRANO",
  "sucursal": "Casa Central Jujuy",
  "fecha_realizacion": "2026-03-20T14:53:00Z"
}
```

#### Listar todas
```
GET /api/auditorias
```

#### Obtener detalle (con controles)
```
GET /api/auditorias/:auditoria_id
```

#### Actualizar resultado final
```
PATCH /api/auditorias/:auditoria_id/resultado
Body: {
  "score_final": 0.9816,
  "calificacion": "SAT - Satisfactorio",
  "estado": "completada"
}
```

### Controles

#### Crear control dentro de auditoría
```
POST /api/auditorias/:auditoria_id/controles
Body: {
  "modulo_numero": 1,
  "modulo_nombre": "1. Transf. Pend. de Recepción",
  "etapa": "Entradas",
  "ponderacion": 0.1
}
```

#### Actualizar control
```
PATCH /api/auditorias/:auditoria_id/controles/:control_id
Body: {
  "score_cumplimiento": 0.95,
  "resultado_final": 0.095,
  "total_items": 3,
  "items_observacion": 0,
  "observaciones": "Sin desviaciones"
}
```

### Desvíos

#### Registrar desvío
```
POST /api/auditorias/:auditoria_id/desvios
Body: {
  "control_id": "uuid-aqui",
  "fecha": "2026-03-20",
  "numero_comprobante": "T-0005-00004364",
  "descripcion": "Transferencia pendiente de recepción",
  "impacto_monetary": 50000,
  "dias_demora": 5,
  "observacion": "Documentación incompleta"
}
```

#### Listar desvíos de un control
```
GET /api/auditorias/:auditoria_id/desvios/:control_id
```

---

## 🗄️ Estructura de Base de Datos

### Tabla: auditores
```sql
CREATE TABLE auditores (
  id TEXT PRIMARY KEY,
  nombre TEXT NOT NULL UNIQUE,
  email TEXT,
  activo INTEGER DEFAULT 1,
  fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Tabla: auditorias
```sql
CREATE TABLE auditorias (
  id TEXT PRIMARY KEY,
  codigo TEXT NOT NULL UNIQUE,
  auditor_id TEXT NOT NULL,
  sucursal TEXT NOT NULL,
  fecha_realizacion TEXT NOT NULL,
  estado TEXT DEFAULT 'en_progreso',
  score_final REAL,
  calificacion TEXT,
  activa INTEGER DEFAULT 1,
  fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
  fecha_actualizacion TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(auditor_id) REFERENCES auditores(id)
);
```

### Tabla: controles
```sql
CREATE TABLE controles (
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
);
```

### Tabla: desvios
```sql
CREATE TABLE desvios (
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
);
```

---

## 🔧 Desarrollo

### Agregar nuevo endpoint

1. En `backend/routes/auditorias.js`:
```javascript
router.get('/custom', async (req, res) => {
  try {
    // Lógica aquí
    res.json({ dato: 'valor' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

2. Reinicia el servidor (`Ctrl+C` → `node server.js`)

### Modificar frontend

1. Edita `frontend/index.html`, `frontend/styles.css` o `frontend/app.js`
2. Recarga el navegador (F5)

### Consultar BD directamente

```bash
# Abrir SQLite interactivamente
sqlite3 backend/db/auditorias.db

# Ver tabla auditorias
SELECT * FROM auditorias;

# Ver tabla controles
SELECT * FROM controles WHERE auditoria_id = 'ID_AQUI';
```

---

## 📊 Lógica de Cálculo

### Score Ponderado
```
Resultado Final = Ponderación × % Cumplimiento

Score Global = Suma de (Resultado Final) / Suma de (Ponderación)
             = Suma de (Resultado Final)  [porque suma de ponderación = 1.0]
```

### Calificación (según Config S-J)
| Score | Abrev | Calificación |
|-------|-------|--------------|
| ≥ 0.94 | SAT | Satisfactorio |
| ≥ 0.82 | ADE | Adecuado |
| ≥ 0.65 | SUJ | Sujeto a mejora |
| ≥ 0.35 | NAD | No adecuado |
| < 0.35 | INS | Insatisfactorio |

---

## 🐛 Troubleshooting

### "Cannot find module 'express'"
```bash
cd backend && npm install
```

### "CORS error en frontend"
- Asegúrate que el servidor (5000) está corriendo
- Verifica que la URL sea `http://localhost:5000` (sin HTTPS)

### "Database locked"
- Solo una instancia del servidor debe acceder a `auditorias.db`
- Si hay dos procesos, mata uno: `taskkill /IM node.exe /F`

---

## 📈 Próximas Mejoras

1. **Validaciones**
   - Score debe estar entre 0-100%
   - Código de auditoría único
   - Email válido para auditores

2. **Autenticación**
   - JWT para login de auditores
   - Roles (auditor, revisor, admin)

3. **Reportes avanzados**
   - Exportar PDF con gráficos
   - Comparar auditorías históricas
   - Alertas de desvíos críticos

4. **Base de datos en producción**
   - Migrar de SQLite a PostgreSQL
   - Conexión pooled
   - Backups automáticos

---

**Última actualización**: 2026-03-20  
**Stack**: Node.js + Express + SQLite + Vanilla JS
