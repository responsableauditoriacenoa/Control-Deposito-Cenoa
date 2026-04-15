# Control Integral de Depósitos - Sistema de Auditoría

Sistema web multiusuario con datos persistentes en SQLite para auditoría de depósitos con layout tipo "Salta-Jujuy".

## 📊 Estructura del Proyecto

```
Control-Depósitos/
├── backend/              # Node.js + Express API
│   ├── server.js         # Punto de entrada
│   ├── package.json      # Dependencias
│   ├── db/
│   │   └── database.js   # SQLite setup + helpers async
│   └── routes/
│       └── auditorias.js # CRUD de auditorías y controles
├── frontend/             # HTML + CSS + JS vanilla
│   ├── index.html        # UI principal
│   ├── app.js            # Lógica del cliente
│   └── styles.css        # Estilos
└── db/                   # Base de datos SQLite (se crea al iniciar)
    └── auditorias.db
```

## 🚀 Instalación y Ejecución

### Backend

```bash
cd backend
npm install
npm start
```

El servidor correrá en `http://localhost:5000`

### Frontend

Abre `frontend/index.html` en tu navegador o sírvelo con:

```bash
cd frontend
python -m http.server 3000
# o con Node.js:
npx http-server -p 3000
```

Accede a `http://localhost:3000`

## 📋 Funcionalidades Principales

### ✅ Crear Auditoría
- Código único de auditoría
- Auditor, sucursal, fecha de realización
- Genera 9 módulos de control automáticamente

### 📊 Registrar Resultados
- 9 módulos de control: 3 Entradas, 3 Stock, 3 Salidas
- Ingresar % de cumplimiento por módulo
- Cálculo automático de resultado ponderado

### 📈 Score Ponderado
- Fórmula: Suma de (ponderación × % cumplimiento)
- Calificación automática: SAT, ADE, SUJ, NAD, INS

### 🔍 Detalle de Desvíos
- Registrar observaciones por módulo
- Listar desvíos con fecha, comprobante, descripción

### 📄 Informe HTML
- Descarga estado actual como archivo HTML
- Formato tipo "Salta-Jujuy"

## 🗄️ Modelo de Datos

### Tabla `auditorias`
- `id` (UUID)
- `codigo` (string, único)
- `auditor_id` (FK) → auditores
- `sucursal` (string)
- `fecha_realizacion` (datetime)
- `estado` (en_progreso, completada)
- `score_final` (decimal)
- `calificacion` (SAT/ADE/SUJ/NAD/INS)

### Tabla `controles`
- `id` (UUID)
- `auditoria_id` (FK) → auditorias
- `modulo_numero` (1-9)
- `modulo_nombre` (string)
- `etapa` (Entradas, Stock, Salidas)
- `ponderacion` (decimal)
- `score_cumplimiento` (0-1)
- `resultado_final` (decimal)
- `total_items` (int)
- `items_observacion` (int)
- `observaciones` (text)

### Tabla `desvios`
- `id` (UUID)
- `control_id` (FK) → controles
- `auditoria_id` (FK) → auditorias
- `fecha`, `numero_comprobante`, `descripcion`
- `impacto_monetary`, `dias_demora`
- `observacion`, `estado`

## 📌 Próximos Pasos

1. **Autenticación**: Login de auditores con JWT
2. **Validaciones avanzadas**: Reglas de negocio por módulo
3. **Reportes PDF**: Exportación con gráficos tipo velocímetro
4. **Base de datos en producción**: PostgreSQL + backup
5. **Multi-sucursal**: Dashboards por sucursal
6. **Historial**: Versionado de auditorías

## 🛠️ Stack Tecnológico

- **Backend**: Node.js 18+, Express 4.x, SQLite3
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Base de datos**: SQLite (desarrollo)
- **API**: REST con JSON

## 📝 Notas Técnicas

- Todas las fórmulas se recalculan en backend para evitar desincronización
- UUIDs para IDs de recursos
- Timestamps automáticos (creación, actualización)
- Transacciones para integridad de datos

---

**Autor**: Sistema de Auditoría Grupo Cenoa  
**Versión**: 1.0.0  
**Fecha**: 2026-03-20
