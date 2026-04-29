const API_BASE = '/api';
const MODULOS_ACTIVOS = [1, 2, 3, 4, 7, 8, 9];
const MODULO_META = {
  1: { nombre: '1. Transf. Pend. de Recepción', etapa: 'Entradas' },
  2: { nombre: '2. Pendientes de Crédito', etapa: 'Entradas' },
  3: { nombre: '3. Remito de Compras', etapa: 'Entradas' },
  4: { nombre: '4. Rdo. Inv. Rotativo', etapa: 'Stock' },
  7: { nombre: '5. Remitos Pend. de Facturación', etapa: 'Salidas' },
  8: { nombre: '6. Ventas Internas Directas', etapa: 'Salidas' },
  9: { nombre: '7. Transf. Pend. De Entrega', etapa: 'Salidas' }
};
const PONDERACION_EQUIVALENTE = 1 / MODULOS_ACTIVOS.length;
const SUCURSALES_POR_EMPRESA_DEFAULT = {
  Autolux: [
    'Casa Central - Jujuy',
    'Suc. Salta PosVenta',
    'Suc. Tartagal',
    'Suc. Las Lajitas',
    'Chapa y Pintura Autolux Salta'
  ],
  Autosol: [
    'Casa Central - Jujuy',
    'Suc. Salta Posventa',
    'Suc. Taller Express',
    'Suc. Tartagal'
  ],
  Ciel: ['Casa Central Jujuy'],
  'Neumaticos Alte. Brown': ['SUC. LAS LOMAS', 'SUC. ALTE. BROWN'],
  VOGE: ['Voge Salta']
};

let appConfig = {
  empresas: ['Autosol', 'Autolux', 'Ciel', 'Neumaticos Alte. Brown', 'VOGE'],
  empresaDefault: 'Autosol',
  sucursales: Object.values(SUCURSALES_POR_EMPRESA_DEFAULT).flat(),
  sucursalesPorEmpresa: SUCURSALES_POR_EMPRESA_DEFAULT,
  ponderaciones: Object.fromEntries(MODULOS_ACTIVOS.map((modulo) => [String(modulo), PONDERACION_EQUIVALENTE]))
};

let auditoriaActual = null;
let activeIndicator = 1;
const dashboardCharts = {
  scoreTrend: null,
  empresa: null,
  estado: null
};
const THEME_STORAGE_KEY = 'control-depositos-theme';
const AUDITORES_DISPONIBLES = [
  'Luis Palacios',
  'Gustavo Zambrano',
  'Nancy Fernandez',
  'Diego Guantay'
];

const moduleState = {
  1: { control: null, transferencias: [] },
  2: { control: null, creditos: [] },
  8: { control: null, ventasInternas: [], totalMuestra: 0 },
  9: { control: null, transferencias: [] }
};

let resumenCierreState = {
  hallazgos: [],
  recomendaciones: []
};

function setTextIfExists(id, value) {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = value;
  }
}

function applyTheme(theme) {
  const resolvedTheme = theme === 'dark' ? 'dark' : 'light';
  document.body.setAttribute('data-theme', resolvedTheme);

  const toggleBtn = document.getElementById('theme-toggle-btn');
  if (toggleBtn) {
    toggleBtn.textContent = resolvedTheme === 'dark' ? '☀️ Modo claro' : '🌙 Modo oscuro';
  }
}

function initTheme() {
  const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = storedTheme || (prefersDark ? 'dark' : 'light');
  applyTheme(theme);
}

function toggleTheme() {
  const currentTheme = document.body.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
  localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
  applyTheme(nextTheme);
}

function destroyDashboardCharts() {
  Object.keys(dashboardCharts).forEach((key) => {
    if (dashboardCharts[key]) {
      dashboardCharts[key].destroy();
      dashboardCharts[key] = null;
    }
  });
}

function renderDashboardCharts(auditorias) {
  if (typeof Chart === 'undefined') return;

  const trendCanvas = document.getElementById('chart-score-trend');
  const empresaCanvas = document.getElementById('chart-score-empresa');
  const estadoCanvas = document.getElementById('chart-estado');
  if (!trendCanvas || !empresaCanvas || !estadoCanvas) return;

  destroyDashboardCharts();

  const ordered = [...auditorias]
    .filter((item) => item.fecha_realizacion)
    .sort((left, right) => new Date(left.fecha_realizacion) - new Date(right.fecha_realizacion));
  const orderedLast = ordered.slice(-12);

  const trendLabels = orderedLast.map((item) => {
    const date = new Date(item.fecha_realizacion);
    const formattedDate = Number.isNaN(date.getTime()) ? '-' : date.toLocaleDateString('es-AR');
    return `${item.codigo} (${formattedDate})`;
  });
  const trendValues = orderedLast.map((item) => {
    const score = Number(item.score_final);
    return Number.isFinite(score) ? Number((score * 100).toFixed(2)) : 0;
  });

  const empresaStats = new Map();
  auditorias.forEach((item) => {
    const empresa = String(item.empresa || 'Sin empresa');
    if (!empresaStats.has(empresa)) {
      empresaStats.set(empresa, { total: 0, conScore: 0, suma: 0 });
    }
    const stat = empresaStats.get(empresa);
    stat.total += 1;
    const score = Number(item.score_final);
    if (Number.isFinite(score)) {
      stat.conScore += 1;
      stat.suma += score;
    }
  });

  const empresas = [...empresaStats.keys()];
  const empresaPromedios = empresas.map((empresa) => {
    const stat = empresaStats.get(empresa);
    if (!stat.conScore) return 0;
    return Number(((stat.suma / stat.conScore) * 100).toFixed(2));
  });

  const estados = ['en_progreso', 'completada'];
  const estadoValores = estados.map((estado) => auditorias.filter((item) => item.estado === estado).length);

  dashboardCharts.scoreTrend = new Chart(trendCanvas, {
    type: 'line',
    data: {
      labels: trendLabels,
      datasets: [{
        label: 'Score %',
        data: trendValues,
        borderColor: '#4f46e5',
        backgroundColor: 'rgba(79, 70, 229, 0.16)',
        fill: true,
        tension: 0.28,
        pointRadius: 3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true }
      },
      scales: {
        y: { beginAtZero: true, max: 100 }
      }
    }
  });

  dashboardCharts.empresa = new Chart(empresaCanvas, {
    type: 'bar',
    data: {
      labels: empresas,
      datasets: [{
        label: 'Promedio Score %',
        data: empresaPromedios,
        backgroundColor: '#22c55e'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true }
      },
      scales: {
        y: { beginAtZero: true, max: 100 }
      }
    }
  });

  dashboardCharts.estado = new Chart(estadoCanvas, {
    type: 'doughnut',
    data: {
      labels: ['En progreso', 'Completadas'],
      datasets: [{
        data: estadoValores,
        backgroundColor: ['#f59e0b', '#22c55e']
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' }
      }
    }
  });
}

function formatDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString();
}

function formatPercent(value) {
  return `${((value || 0) * 100).toFixed(2)}%`;
}

function formatNumber(value) {
  if (value === null || value === undefined || value === '') return '-';
  const parsed = Number(value);
  if (Number.isNaN(parsed)) return String(value);
  return parsed.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

function formatMoney(value) {
  if (value === null || value === undefined || value === '') return '-';
  const parsed = Number(value);
  if (Number.isNaN(parsed)) return String(value);
  return parsed.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatAuditorDisplay(value) {
  const raw = String(value || '').trim();
  if (!raw) return '-';
  if (raw.startsWith('AUD_')) {
    return raw.slice(4).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }
  return raw;
}

function getControlByModule(moduleNumber) {
  return auditoriaActual?.controles?.find((control) => control.modulo_numero === moduleNumber) || null;
}

function updateControlCache(control) {
  if (!auditoriaActual || !control) return;
  const index = auditoriaActual.controles.findIndex((item) => item.id === control.id);
  if (index >= 0) auditoriaActual.controles[index] = control;
}

function showSection(sectionId, triggerButton = null) {
  document.querySelectorAll('.section').forEach((section) => section.classList.remove('active'));
  document.getElementById(sectionId).classList.add('active');

  document.querySelectorAll('.side-btn').forEach((button) => button.classList.remove('active'));
  if (triggerButton) triggerButton.classList.add('active');

  if (sectionId === 'dashboard') cargarDashboard();
  if (sectionId === 'configuracion') cargarConfiguracion();
  if (sectionId === 'auditorias') cargarAuditorias();
  if (sectionId === 'informes') cargarInformes();
  if (sectionId === 'resumen-auditoria') mostrarResumenAuditoria();

  // Pre-rellenar auditor al abrir el formulario
  if (sectionId === 'nueva-auditoria') {
    const auditorInput = document.getElementById('auditor');
    const nombre = localStorage.getItem('auditor_nombre');
    if (auditorInput && nombre && !auditorInput.value) auditorInput.value = nombre;
  }
}

function setIndicatorScreen(moduleNumber, triggerButton = null) {
  activeIndicator = moduleNumber;
  document.querySelectorAll('.indicator-screen').forEach((screen) => screen.classList.remove('active'));
  const target = document.getElementById(`indicator-screen-${moduleNumber}`);
  if (target) target.classList.add('active');

  document.querySelectorAll('.indicator-btn').forEach((button) => button.classList.remove('active'));
  if (triggerButton) triggerButton.classList.add('active');

  if (moduleNumber === 8) {
    renderVentasInternasTable();
  }

  if ([3, 4, 7].includes(moduleNumber)) renderGenericSummary(moduleNumber);
}

function getControlesActivos(controles) {
  return (controles || [])
    .filter((control) => MODULOS_ACTIVOS.includes(control.modulo_numero))
    .sort((left, right) => left.modulo_numero - right.modulo_numero);
}

function renderSelectOptions(selectId, values, selectedValue = '') {
  const select = document.getElementById(selectId);
  if (!select) return;

  const safeValues = [...new Set((values || []).map((item) => String(item || '').trim()).filter(Boolean))];
  const options = ['<option value="">-- Seleccionar --</option>']
    .concat(safeValues.map((value) => `<option value="${value}" ${value === selectedValue ? 'selected' : ''}>${value}</option>`));

  select.innerHTML = options.join('');
}

function normalizeSucursalesPorEmpresa(empresas, sucursalesPorEmpresaInput = {}, sucursalesFallback = []) {
  const fallback = [...new Set((sucursalesFallback || []).map((item) => String(item || '').trim()).filter(Boolean))];
  const result = {};

  (empresas || []).forEach((empresa) => {
    const fallbackEmpresa = Array.isArray(SUCURSALES_POR_EMPRESA_DEFAULT[empresa])
      ? SUCURSALES_POR_EMPRESA_DEFAULT[empresa]
      : fallback;
    const raw = Array.isArray(sucursalesPorEmpresaInput?.[empresa])
      ? sucursalesPorEmpresaInput[empresa]
      : fallbackEmpresa;
    result[empresa] = [...new Set(raw.map((item) => String(item || '').trim()).filter(Boolean))];
  });

  return result;
}

function flattenSucursales(sucursalesPorEmpresa = {}) {
  return [...new Set(
    Object.values(sucursalesPorEmpresa)
      .flat()
      .map((item) => String(item || '').trim())
      .filter(Boolean)
  )];
}

function getSucursalesEmpresa(empresa) {
  return appConfig.sucursalesPorEmpresa?.[empresa] || [];
}

function syncSucursalSelectForEmpresa() {
  const empresaSelect = document.getElementById('empresa');
  const sucursalSelect = document.getElementById('sucursal');
  if (!empresaSelect || !sucursalSelect) return;

  const empresaSeleccionada = empresaSelect.value;
  const sucursales = getSucursalesEmpresa(empresaSeleccionada);
  const previousSucursal = sucursalSelect.value;
  const selectedSucursal = sucursales.includes(previousSucursal) ? previousSucursal : '';
  renderSelectOptions('sucursal', sucursales, selectedSucursal);
}

function syncNuevaAuditoriaSelects() {
  const empresaSelect = document.getElementById('empresa');
  const previousEmpresa = empresaSelect?.value || '';
  const empresaSeleccionada = appConfig.empresas.includes(previousEmpresa)
    ? previousEmpresa
    : (appConfig.empresaDefault || appConfig.empresas[0] || '');

  renderSelectOptions('empresa', appConfig.empresas, empresaSeleccionada);

  const updatedEmpresaSelect = document.getElementById('empresa');
  if (updatedEmpresaSelect) {
    updatedEmpresaSelect.onchange = syncSucursalSelectForEmpresa;
  }

  syncSucursalSelectForEmpresa();
}

function renderConfigPonderaciones() {
  const tbody = document.getElementById('config-ponderaciones-tabla');
  if (!tbody) return;

  tbody.innerHTML = [...MODULOS_ACTIVOS].sort((left, right) => left - right).map((modulo, index) => {
    const meta = MODULO_META[modulo];
    const ponderacion = Number(appConfig.ponderaciones[String(modulo)] || PONDERACION_EQUIVALENTE) * 100;
    return `
      <tr>
        <td>
          <div class="config-indicator-cell">
            <span class="config-indicator-badge">${index + 1}</span>
            <span>${meta.nombre}</span>
          </div>
        </td>
        <td>
          <input class="config-ponder-input" type="number" min="0" max="100" step="0.01" id="config-ponderacion-${modulo}" value="${ponderacion.toFixed(2)}">
        </td>
      </tr>
    `;
  }).join('');
}

function renderConfigSucursales() {
  const empresaSelect = document.getElementById('config-empresa-sucursales');
  const container = document.getElementById('config-sucursales-lista');
  if (!container || !empresaSelect) return;

  const empresa = empresaSelect.value;
  const sucursales = getSucursalesEmpresa(empresa);

  container.innerHTML = sucursales.map((sucursal) => `
    <span class="config-chip">
      ${sucursal}
      <button type="button" onclick="quitarSucursalConfig('${sucursal.replace(/'/g, "\\'")}')">×</button>
    </span>
  `).join('');
}

function renderConfigEmpresaSucursalesSelector() {
  const select = document.getElementById('config-empresa-sucursales');
  if (!select) return;

  const currentValue = select.value;
  const selected = appConfig.empresas.includes(currentValue)
    ? currentValue
    : (appConfig.empresaDefault || appConfig.empresas[0] || '');

  select.innerHTML = (appConfig.empresas || [])
    .map((empresa) => `<option value="${empresa}" ${empresa === selected ? 'selected' : ''}>${empresa}</option>`)
    .join('');
}

function renderConfigEmpresaDefault() {
  const select = document.getElementById('config-empresa-default');
  if (!select) return;

  select.innerHTML = (appConfig.empresas || [])
    .map((empresa) => `<option value="${empresa}" ${empresa === appConfig.empresaDefault ? 'selected' : ''}>${empresa}</option>`)
    .join('');
}

function renderConfiguracionUI() {
  renderConfigPonderaciones();
  renderConfigEmpresaDefault();
  renderConfigEmpresaSucursalesSelector();
  renderConfigSucursales();
  syncNuevaAuditoriaSelects();
}

async function cargarConfiguracion() {
  try {
    const response = await fetch(`${API_BASE}/auditorias/configuracion`);
    if (!response.ok) throw new Error('No se pudo cargar la configuración');

    const config = await response.json();
    const empresas = config.empresas || appConfig.empresas;
    const sucursalesPorEmpresa = normalizeSucursalesPorEmpresa(
      empresas,
      config.sucursalesPorEmpresa || {},
      config.sucursales || appConfig.sucursales
    );
    appConfig = {
      empresas,
      empresaDefault: config.empresaDefault || appConfig.empresaDefault,
      sucursalesPorEmpresa,
      sucursales: flattenSucursales(sucursalesPorEmpresa),
      ponderaciones: config.ponderaciones || appConfig.ponderaciones
    };

    renderConfiguracionUI();
  } catch (error) {
    console.error(error);
  }
}

function agregarSucursalConfig() {
  const input = document.getElementById('config-nueva-sucursal');
  const empresaSelect = document.getElementById('config-empresa-sucursales');
  if (!input || !empresaSelect) return;

  const value = String(input.value || '').trim();
  const empresa = empresaSelect.value;
  if (!value) return;
  if (!empresa) return;

  const sucursalesEmpresa = getSucursalesEmpresa(empresa);
  if (sucursalesEmpresa.includes(value)) {
    input.value = '';
    return;
  }

  appConfig.sucursalesPorEmpresa = {
    ...(appConfig.sucursalesPorEmpresa || {}),
    [empresa]: [...sucursalesEmpresa, value]
  };
  appConfig.sucursales = flattenSucursales(appConfig.sucursalesPorEmpresa);
  input.value = '';
  renderConfigSucursales();
  syncNuevaAuditoriaSelects();
}

function quitarSucursalConfig(sucursal) {
  const empresaSelect = document.getElementById('config-empresa-sucursales');
  const empresa = empresaSelect?.value;
  if (!empresa) return;

  const sucursalesEmpresa = getSucursalesEmpresa(empresa).filter((item) => item !== sucursal);
  appConfig.sucursalesPorEmpresa = {
    ...(appConfig.sucursalesPorEmpresa || {}),
    [empresa]: sucursalesEmpresa
  };
  appConfig.sucursales = flattenSucursales(appConfig.sucursalesPorEmpresa);
  renderConfigSucursales();
  syncNuevaAuditoriaSelects();
}

async function guardarConfiguracion() {
  try {
    const ponderaciones = Object.fromEntries(
      MODULOS_ACTIVOS.map((modulo) => {
        const input = document.getElementById(`config-ponderacion-${modulo}`);
        const percent = Number(input?.value || 0);
        const normalized = Number.isFinite(percent) && percent > 0 ? percent / 100 : 0;
        return [String(modulo), normalized];
      })
    );

    const empresaDefaultSelect = document.getElementById('config-empresa-default');
    const empresaDefault = empresaDefaultSelect?.value || appConfig.empresaDefault;

    const response = await fetch(`${API_BASE}/auditorias/configuracion`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        empresas: appConfig.empresas,
        sucursales_por_empresa: appConfig.sucursalesPorEmpresa,
        empresa_default: empresaDefault,
        ponderaciones
      })
    });

    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'No se pudo guardar la configuración');

    const config = payload.configuracion;
    const sucursalesPorEmpresa = normalizeSucursalesPorEmpresa(
      config.empresas,
      config.sucursalesPorEmpresa || {},
      config.sucursales || []
    );
    appConfig = {
      empresas: config.empresas,
      empresaDefault: config.empresaDefault,
      sucursalesPorEmpresa,
      sucursales: flattenSucursales(sucursalesPorEmpresa),
      ponderaciones: config.ponderaciones
    };

    renderConfiguracionUI();

    if (auditoriaActual?.id) {
      await abrirIndicadores(auditoriaActual.id);
    }

    alert('Configuración guardada correctamente');
  } catch (error) {
    console.error(error);
    alert(error.message);
  }
}

async function cargarDashboard() {
  try {
    const response = await fetch(`${API_BASE}/auditorias`);
    const auditorias = await response.json();

    const setSemaforo = (key, valueLabel, state) => {
      const valueElement = document.getElementById(`semaforo-${key}-valor`);
      const statusElement = document.getElementById(`semaforo-${key}-estado`);
      if (!valueElement || !statusElement) return;

      valueElement.textContent = valueLabel;
      statusElement.classList.remove('ok', 'neutral', 'fail');

      if (state === 'ok') {
        statusElement.classList.add('ok');
        statusElement.textContent = 'Verde';
        return;
      }

      if (state === 'neutral') {
        statusElement.classList.add('neutral');
        statusElement.textContent = 'Amarillo';
        return;
      }

      statusElement.classList.add('fail');
      statusElement.textContent = 'Rojo';
    };

    const now = new Date();
    const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000;

    const toDate = (value) => {
      const parsed = new Date(value);
      return Number.isNaN(parsed.getTime()) ? null : parsed;
    };

    const total = auditorias.length;
    const enProgreso = auditorias.filter((item) => item.estado === 'en_progreso');
    const completadas = auditorias.filter((item) => item.estado === 'completada').length;
    const conScore = auditorias.filter((item) => item.score_final !== null);
    const sinScore = total - conScore.length;

    const auditoriasUltimos30d = auditorias.filter((item) => {
      const date = toDate(item.fecha_realizacion);
      if (!date) return false;
      return (now.getTime() - date.getTime()) <= THIRTY_DAYS_MS;
    }).length;

    const promedio = conScore.length
      ? (conScore.reduce((sum, item) => sum + item.score_final, 0) / conScore.length) * 100
      : null;

    const tasaCierre = total > 0 ? (completadas / total) * 100 : null;

    const riesgoAlto = auditorias.filter((item) => {
      const calif = String(item.calificacion || '').toUpperCase();
      if (calif.includes('INS') || calif.includes('NAD')) return true;
      const score = Number(item.score_final);
      return Number.isFinite(score) && score < 0.65;
    }).length;
    const riesgoAltoPorcentaje = total > 0 ? (riesgoAlto / total) * 100 : null;

    const backlogCritico = enProgreso.filter((item) => {
      const date = toDate(item.fecha_realizacion);
      const ageMs = date ? now.getTime() - date.getTime() : THIRTY_DAYS_MS + 1;
      const score = Number(item.score_final);
      return ageMs > THIRTY_DAYS_MS && (!Number.isFinite(score) || score < 0.65);
    }).length;

    const empresasAuditadas = new Set(
      auditorias
        .map((item) => String(item.empresa || '').trim())
        .filter(Boolean)
    ).size;
    const empresasConfiguradas = (appConfig.empresas || []).length;
    const coberturaEmpresas = empresasConfiguradas > 0
      ? (empresasAuditadas / empresasConfiguradas) * 100
      : null;

    const scores = conScore
      .map((item) => Number(item.score_final))
      .filter((value) => Number.isFinite(value));

    const sortedScores = [...scores].sort((left, right) => left - right);
    const medianaScore = sortedScores.length
      ? (sortedScores.length % 2
        ? sortedScores[(sortedScores.length - 1) / 2]
        : (sortedScores[(sortedScores.length / 2) - 1] + sortedScores[sortedScores.length / 2]) / 2) * 100
      : null;

    const meanScore = scores.length
      ? scores.reduce((sum, value) => sum + value, 0) / scores.length
      : null;
    const desviacionScore = meanScore === null
      ? null
      : Math.sqrt(scores.reduce((sum, value) => sum + ((value - meanScore) ** 2), 0) / scores.length) * 100;

    const mejorScore = scores.length ? Math.max(...scores) * 100 : null;
    const peorScore = scores.length ? Math.min(...scores) * 100 : null;
    const brechaScore = (mejorScore !== null && peorScore !== null) ? (mejorScore - peorScore) : null;

    const empresaCounts = new Map();
    auditorias.forEach((item) => {
      const empresa = String(item.empresa || 'Sin empresa').trim() || 'Sin empresa';
      empresaCounts.set(empresa, (empresaCounts.get(empresa) || 0) + 1);
    });
    const topEmpresaEntry = [...empresaCounts.entries()].sort((left, right) => right[1] - left[1])[0] || null;
    const concentracionEmpresa = topEmpresaEntry && total > 0
      ? (topEmpresaEntry[1] / total) * 100
      : null;

    const completitudScore = total > 0 ? (conScore.length / total) * 100 : null;

    document.getElementById('total-auditorias').textContent = total;
    document.getElementById('auditorias-30d').textContent = auditoriasUltimos30d;
    document.getElementById('tasa-cierre').textContent = tasaCierre === null ? '-' : `${tasaCierre.toFixed(1)}%`;
    document.getElementById('cobertura-empresas').textContent = coberturaEmpresas === null ? '-' : `${coberturaEmpresas.toFixed(1)}%`;
    document.getElementById('score-promedio').textContent = promedio === null ? '-' : `${promedio.toFixed(2)}%`;
    document.getElementById('mediana-score').textContent = medianaScore === null ? '-' : `${medianaScore.toFixed(2)}%`;
    document.getElementById('desviacion-score').textContent = desviacionScore === null ? '-' : `${desviacionScore.toFixed(2)} pp`;
    document.getElementById('brecha-score').textContent = brechaScore === null ? '-' : `${brechaScore.toFixed(2)} pp`;
    document.getElementById('riesgo-alto').textContent = riesgoAlto;
    document.getElementById('riesgo-alto-meta').textContent = riesgoAltoPorcentaje === null ? '0.0% del total' : `${riesgoAltoPorcentaje.toFixed(1)}% del total`;
    document.getElementById('backlog-critico').textContent = backlogCritico;
    document.getElementById('completitud-score').textContent = completitudScore === null ? '-' : `${completitudScore.toFixed(1)}%`;
    document.getElementById('concentracion-empresa').textContent = concentracionEmpresa === null ? '-' : `${concentracionEmpresa.toFixed(1)}%`;
    document.getElementById('top-empresa-label').textContent = topEmpresaEntry
      ? `Mayor participación: ${topEmpresaEntry[0]} (${topEmpresaEntry[1]} auditorías)`
      : 'Mayor participación por empresa';

    const cierreState = tasaCierre === null
      ? 'neutral'
      : (tasaCierre >= 70 ? 'ok' : (tasaCierre >= 40 ? 'neutral' : 'fail'));
    const scoreState = promedio === null
      ? 'neutral'
      : (promedio >= 85 ? 'ok' : (promedio >= 70 ? 'neutral' : 'fail'));
    const riesgoState = riesgoAltoPorcentaje === null
      ? 'neutral'
      : (riesgoAltoPorcentaje <= 10 ? 'ok' : (riesgoAltoPorcentaje <= 25 ? 'neutral' : 'fail'));
    const coberturaState = coberturaEmpresas === null
      ? 'neutral'
      : (coberturaEmpresas >= 90 ? 'ok' : (coberturaEmpresas >= 70 ? 'neutral' : 'fail'));
    const backlogRatio = total > 0 ? (backlogCritico / total) * 100 : null;
    const backlogState = backlogRatio === null
      ? 'neutral'
      : (backlogRatio <= 5 ? 'ok' : (backlogRatio <= 12 ? 'neutral' : 'fail'));
    const completitudState = completitudScore === null
      ? 'neutral'
      : (completitudScore >= 98 ? 'ok' : (completitudScore >= 90 ? 'neutral' : 'fail'));

    setSemaforo('cierre', tasaCierre === null ? '-' : `${tasaCierre.toFixed(1)}%`, cierreState);
    setSemaforo('score', promedio === null ? '-' : `${promedio.toFixed(2)}%`, scoreState);
    setSemaforo('riesgo', riesgoAltoPorcentaje === null ? '-' : `${riesgoAltoPorcentaje.toFixed(1)}%`, riesgoState);
    setSemaforo('cobertura', coberturaEmpresas === null ? '-' : `${coberturaEmpresas.toFixed(1)}%`, coberturaState);
    setSemaforo('backlog', backlogRatio === null ? '-' : `${backlogRatio.toFixed(1)}%`, backlogState);
    setSemaforo('completitud', completitudScore === null ? '-' : `${completitudScore.toFixed(1)}%`, completitudState);

    renderDashboardCharts(auditorias);
  } catch (error) {
    console.error(error);
  }
}

let auditoriasCache = [];

async function cargarAuditorias() {
  const tbody = document.getElementById('lista-auditorias');
  if (!tbody) return;
  try {
    const response = await fetch(`${API_BASE}/auditorias`);
    auditoriasCache = await response.json();

    // Poblar selector empresa dinámicamente
    const empresas = [...new Set(auditoriasCache.map(a => a.empresa).filter(Boolean))].sort();
    const sel = document.getElementById('aud-filtro-empresa');
    if (sel) {
      sel.innerHTML = '<option value="">Todas las empresas</option>' +
        empresas.map(e => `<option value="${e}">${e}</option>`).join('');
    }

    filtrarAuditorias();
  } catch (error) {
    console.error(error);
    if (tbody) tbody.innerHTML = '<tr><td colspan="9">Error al cargar auditorías.</td></tr>';
  }
}

function filtrarAuditorias() {
  const tbody = document.getElementById('lista-auditorias');
  if (!tbody) return;

  const texto = (document.getElementById('aud-filtro-texto')?.value || '').toLowerCase();
  const empresa = document.getElementById('aud-filtro-empresa')?.value || '';
  const estado = document.getElementById('aud-filtro-estado')?.value || '';
  const desde = document.getElementById('aud-filtro-desde')?.value || '';
  const hasta = document.getElementById('aud-filtro-hasta')?.value || '';

  const filtradas = auditoriasCache.filter(a => {
    const auditor = a.auditor_nombre || formatAuditorDisplay(a.auditor_id) || '';
    if (texto && !`${a.codigo} ${a.empresa} ${a.sucursal} ${auditor}`.toLowerCase().includes(texto)) return false;
    if (empresa && a.empresa !== empresa) return false;
    if (estado && a.estado !== estado) return false;
    const fechaStr = (a.fecha_realizacion || '').substring(0, 10);
    if (desde && fechaStr < desde) return false;
    if (hasta && fechaStr > hasta) return false;
    return true;
  });

  const conteo = document.getElementById('aud-conteo');
  if (conteo) conteo.textContent = `${filtradas.length} de ${auditoriasCache.length} auditorías`;

  if (!filtradas.length) {
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px;">No se encontraron auditorías con los filtros aplicados.</td></tr>';
    return;
  }

  const CALIFICACIONES = {
    satisfactorio: { label: 'Satisfactorio', cls: 'calificacion-sat' },
    adecuado: { label: 'Adecuado', cls: 'calificacion-ade' },
    sujeto_mejora: { label: 'Sujeto a mejora', cls: 'calificacion-suj' },
    necesita_atencion: { label: 'Necesita atención', cls: 'calificacion-nad' },
    insatisfactorio: { label: 'Insatisfactorio', cls: 'calificacion-ins' }
  };

  tbody.innerHTML = filtradas.map(a => {
    const auditor = a.auditor_nombre || formatAuditorDisplay(a.auditor_id) || '—';
    const fecha = a.fecha_realizacion ? new Date(a.fecha_realizacion).toLocaleDateString('es-AR') : '—';
    const score = a.score_final !== null && a.score_final !== undefined
      ? `${(a.score_final * 100).toFixed(1)}%` : '—';
    const estadoBadge = `<span class="badge ${a.estado || 'en_progreso'}">${(a.estado || 'en_progreso').replace('_', ' ')}</span>`;
    const calif = a.calificacion_global ? (CALIFICACIONES[a.calificacion_global] || { label: a.calificacion_global, cls: '' }) : null;
    const califChip = calif
      ? `<span class="calificacion-chip ${calif.cls}">${calif.label}</span>`
      : '—';
    return `<tr>
      <td><code>${a.codigo}</code></td>
      <td>${a.empresa || '—'}</td>
      <td>${a.sucursal || '—'}</td>
      <td>${auditor}</td>
      <td>${fecha}</td>
      <td>${estadoBadge}</td>
      <td>${score}</td>
      <td>${califChip}</td>
      <td><button class="btn btn-primary btn-sm" onclick="abrirIndicadores('${a.id}')">Abrir</button></td>
    </tr>`;
  }).join('');
}

function limpiarFiltrosAuditorias() {
  ['aud-filtro-texto', 'aud-filtro-empresa', 'aud-filtro-estado', 'aud-filtro-desde', 'aud-filtro-hasta']
    .forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  filtrarAuditorias();
}

let informesCache = [];

async function cargarInformes() {
  const tbody = document.getElementById('informes-tabla');
  if (!tbody) return;

  try {
    const response = await fetch(`${API_BASE}/auditorias/informes`);
    if (!response.ok) throw new Error('No se pudieron cargar los informes');

    informesCache = await response.json();

    // Poblar selector de empresas
    const empresasUnicas = [...new Set(informesCache.map((item) => String(item.empresa || '')).filter(Boolean))].sort();
    const filtroEmpresa = document.getElementById('filtro-empresa');
    if (filtroEmpresa) {
      filtroEmpresa.innerHTML = '<option value="">Todas las empresas</option>' +
        empresasUnicas.map((e) => `<option value="${e}">${e}</option>`).join('');
    }

    filtrarInformes();
  } catch (error) {
    console.error(error);
    tbody.innerHTML = '<tr><td colspan="10">Error al cargar informes.</td></tr>';
  }
}

function filtrarInformes() {
  const tbody = document.getElementById('informes-tabla');
  if (!tbody) return;

  const textoBusqueda = String(document.getElementById('filtro-codigo')?.value || '').toLowerCase().trim();
  const empresaFiltro = String(document.getElementById('filtro-empresa')?.value || '');
  const califFiltro = String(document.getElementById('filtro-calificacion')?.value || '');
  const fechaDesde = document.getElementById('filtro-fecha-desde')?.value || '';
  const fechaHasta = document.getElementById('filtro-fecha-hasta')?.value || '';

  const parseFechaFiltro = (valor) => {
    if (!valor) return null;
    const parsed = new Date(valor + 'T00:00:00');
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  };

  const desde = parseFechaFiltro(fechaDesde);
  const hasta = parseFechaFiltro(fechaHasta);

  const filtrados = informesCache.filter((informe) => {
    // Texto libre
    if (textoBusqueda) {
      const haystack = `${informe.codigo || ''} ${informe.empresa || ''} ${informe.sucursal || ''} ${informe.auditor_nombre || ''}`.toLowerCase();
      if (!haystack.includes(textoBusqueda)) return false;
    }

    // Empresa
    if (empresaFiltro && informe.empresa !== empresaFiltro) return false;

    // Calificación
    if (califFiltro && !String(informe.calificacion || '').toUpperCase().startsWith(califFiltro)) return false;

    // Rango de fecha cierre
    const fechaCierreVal = informe.fecha_cierre || informe.fecha_realizacion;
    if (desde || hasta) {
      const fechaInforme = fechaCierreVal ? new Date(fechaCierreVal) : null;
      if (!fechaInforme || Number.isNaN(fechaInforme.getTime())) return false;
      if (desde && fechaInforme < desde) return false;
      if (hasta) {
        const hastaFin = new Date(hasta);
        hastaFin.setHours(23, 59, 59, 999);
        if (fechaInforme > hastaFin) return false;
      }
    }

    return true;
  });

  const conteoEl = document.getElementById('informes-conteo');
  if (conteoEl) {
    conteoEl.textContent = filtrados.length === informesCache.length
      ? `${informesCache.length} informe${informesCache.length !== 1 ? 's' : ''}`
      : `${filtrados.length} de ${informesCache.length} informe${informesCache.length !== 1 ? 's' : ''}`;
  }

  if (!filtrados.length) {
    tbody.innerHTML = '<tr><td colspan="10">No hay informes que coincidan con los filtros.</td></tr>';
    return;
  }

  tbody.innerHTML = filtrados.map((informe) => {
    const hallazgosCount = (tryParseJsonArray(informe.hallazgos) || []).length;
    const recomendacionesCount = (tryParseJsonArray(informe.recomendaciones) || []).length;
    const score = Number(informe.score_final);
    const fechaCierre = informe.fecha_cierre ? formatDate(informe.fecha_cierre) : formatDate(informe.fecha_realizacion);
    const scoreLabel = Number.isFinite(score) ? `${(score * 100).toFixed(2)}%` : '-';
    const califCode = String(informe.calificacion || '').split(' - ')[0] || '-';
    const califClass = { SAT: 'calificacion-sat', ADE: 'calificacion-ade', SUJ: 'calificacion-suj', NAD: 'calificacion-nad', INS: 'calificacion-ins' }[califCode] || '';

    return `
      <tr>
        <td><strong>${informe.codigo || '-'}</strong></td>
        <td>${informe.empresa || '-'}</td>
        <td>${informe.sucursal || '-'}</td>
        <td>${informe.auditor_nombre || formatAuditorDisplay(informe.auditor_id)}</td>
        <td>${fechaCierre}</td>
        <td><strong>${scoreLabel}</strong></td>
        <td><span class="calificacion-chip ${califClass}">${informe.calificacion || '-'}</span></td>
        <td>${hallazgosCount}</td>
        <td>${recomendacionesCount}</td>
        <td>
          <div class="informes-actions">
            <button class="btn btn-secondary" onclick="abrirInforme('${informe.id}', 'resumen')">Abrir</button>
            <button class="btn btn-success" onclick="abrirInforme('${informe.id}', 'pdf')">PDF</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function limpiarFiltrosInformes() {
  const ids = ['filtro-codigo', 'filtro-empresa', 'filtro-calificacion', 'filtro-fecha-desde', 'filtro-fecha-hasta'];
  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  filtrarInformes();
}

async function abrirInforme(auditoriaId, accion = 'resumen') {
  await abrirIndicadores(auditoriaId);

  if (accion === 'pdf') {
    exportarInformePDF();
    return;
  }

  showSection('resumen-auditoria', document.getElementById('menu-resumen'));
}

async function crearAuditoria(event) {
  event.preventDefault();

  const codigo = document.getElementById('codigo').value;
  const auditorNombre = document.getElementById('auditor').value;
  const empresa = document.getElementById('empresa').value;
  const sucursal = document.getElementById('sucursal').value;
  const fecha = document.getElementById('fecha').value;

  const auditorId = auditorNombre.trim();
  const fechaRealizacion = fecha ? new Date(`${fecha}T00:00:00`).toISOString() : '';

  try {
    const response = await fetch(`${API_BASE}/auditorias`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        codigo,
        auditor_id: auditorId,
        empresa,
        sucursal,
        fecha_realizacion: fechaRealizacion
      })
    });

    if (!response.ok) throw new Error('No se pudo crear la auditoría');

    const result = await response.json();
    const modules = MODULOS_ACTIVOS.map((modulo) => ({
      modulo_numero: modulo,
      modulo_nombre: MODULO_META[modulo].nombre,
      etapa: MODULO_META[modulo].etapa,
      ponderacion: Number(appConfig.ponderaciones[String(modulo)] || PONDERACION_EQUIVALENTE)
    }));

    for (const moduleData of modules) {
      await fetch(`${API_BASE}/auditorias/${result.id}/controles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(moduleData)
      });
    }

    alert('Auditoría creada correctamente');
    document.getElementById('form-auditoria').reset();
    syncNuevaAuditoriaSelects();
    showSection('auditorias', document.querySelectorAll('.side-btn')[3]);
    cargarAuditorias();
  } catch (error) {
    console.error(error);
    alert(error.message);
  }
}

function updateAuditHeader() {
  if (!auditoriaActual) return;

  setTextIfExists('indicator-audit-title', `Auditoría ${auditoriaActual.codigo}`);
  setTextIfExists('selected-audit-label', `${auditoriaActual.codigo} · ${auditoriaActual.empresa || '-'} · ${auditoriaActual.sucursal}`);
  setTextIfExists('detalle-auditor', auditoriaActual.auditor_nombre || formatAuditorDisplay(auditoriaActual.auditor_id));
  setTextIfExists('detalle-sucursal', auditoriaActual.sucursal);
  setTextIfExists('detalle-fecha', new Date(auditoriaActual.fecha_realizacion).toLocaleDateString());
  setTextIfExists('detalle-estado', auditoriaActual.estado);

  const score = auditoriaActual.score_final ?? 0;
  setTextIfExists('detalle-score', `${(score * 100).toFixed(2)}%`);
  setTextIfExists('detalle-calificacion', auditoriaActual.calificacion || obtenerCalificacion(score));
}

async function abrirIndicadores(auditoriaId) {
  try {
    const response = await fetch(`${API_BASE}/auditorias/${auditoriaId}`);
    if (!response.ok) throw new Error('No se pudo abrir la auditoría');

    const payload = await response.json();
    auditoriaActual = payload.auditoria;
    auditoriaActual.controles = getControlesActivos(payload.controles);

    document.getElementById('menu-indicadores').disabled = false;
    document.getElementById('menu-resumen').disabled = false;
    showSection('indicadores', document.getElementById('menu-indicadores'));
    updateAuditHeader();

    await Promise.all([
      cargarTransferenciasModulo(1),
      cargarCreditosModulo(),
      cargarVentasInternasModulo(),
      cargarTransferenciasModulo(9)
    ]);
    [3, 4, 7].forEach((module) => renderGenericSummary(module));

    setIndicatorScreen(1, document.querySelectorAll('.indicator-btn')[0]);
  } catch (error) {
    console.error(error);
    alert(`Error al cargar auditoría: ${error.message}`);
  }
}

function abrirDetalle(auditoriaId) {
  return abrirIndicadores(auditoriaId);
}

function obtenerCalificacion(score) {
  if (score >= 0.94) return 'SAT - Satisfactorio';
  if (score >= 0.82) return 'ADE - Adecuado';
  if (score >= 0.65) return 'SUJ - Sujeto a mejora';
  if (score >= 0.35) return 'NAD - No adecuado';
  return 'INS - Insatisfactorio';
}

function recalcularScoreFinalLocal() {
  if (!auditoriaActual?.controles?.length) return;

  const scoreFinal = getControlesActivos(auditoriaActual.controles)
    .reduce((acc, item) => acc + (item.resultado_final || 0), 0);
  auditoriaActual.score_final = scoreFinal;
  auditoriaActual.calificacion = obtenerCalificacion(scoreFinal);
  updateAuditHeader();
}

function renderSummary(moduleNumber, total, cumplen, observadas, score) {
  const container = document.getElementById(`transfer-summary-${moduleNumber}`);
  if (!container) return;

  container.innerHTML = `
    <div class="summary-card"><span>Total</span><strong>${total}</strong></div>
    <div class="summary-card"><span>Cumplen</span><strong>${cumplen}</strong></div>
    <div class="summary-card"><span>No cumplen</span><strong>${observadas}</strong></div>
    <div class="summary-card"><span>% Cumplimiento</span><strong>${formatPercent(score)}</strong></div>
  `;
}

function renderTransferTable(moduleNumber) {
  const tbody = document.getElementById(`transfer-table-${moduleNumber}`);
  const rows = moduleState[moduleNumber].transferencias || [];

  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="9">Sin datos importados.</td></tr>';
    return;
  }

  tbody.innerHTML = rows.map((row) => {
    const requiresReview = row.cumple_base === 0;
    const checked = row.justificado === 1 ? 'checked' : '';
    const disabled = requiresReview ? '' : 'disabled';
    const statusClass = row.cumple_final === 1 ? 'ok' : 'fail';
    const statusLabel = row.cumple_final === 1 ? 'Si cumple' : 'No cumple';

    return `
      <tr>
        <td>${formatDate(row.fecha_transferencia)}</td>
        <td>${row.numero_comprobante || '-'}</td>
        <td>${row.sucursal_origen || '-'}</td>
        <td>${row.sucursal_destino || '-'}</td>
        <td>${row.dias_habiles}</td>
        <td><span class="status-chip ${statusClass}">${statusLabel}</span></td>
        <td><input type="checkbox" id="just-${row.id}" ${checked} ${disabled}></td>
        <td><textarea id="obs-${row.id}" ${disabled}>${row.observacion || ''}</textarea></td>
        <td><button class="btn btn-secondary" onclick="guardarTransferencia('${row.id}', ${moduleNumber})">Guardar</button></td>
      </tr>
    `;
  }).join('');
}

async function cargarTransferenciasModulo(moduleNumber) {
  if (!auditoriaActual?.id) return;

  const response = await fetch(`${API_BASE}/auditorias/${auditoriaActual.id}/transferencias/${moduleNumber}`);
  if (!response.ok) return;

  const payload = await response.json();
  moduleState[moduleNumber] = payload;
  updateControlCache(payload.control);

  const total = payload.control.total_items || 0;
  const observadas = payload.control.items_observacion || 0;
  const cumplen = total - observadas;
  renderSummary(moduleNumber, total, cumplen, observadas, payload.control.score_cumplimiento || 0);
  renderTransferTable(moduleNumber);
  recalcularScoreFinalLocal();
}

async function importarTransferencias() {
  if (!auditoriaActual?.id) return alert('Abre una auditoría primero.');

  const input = document.getElementById('archivo-transferencias');
  if (!input.files.length) return alert('Selecciona un archivo Excel.');

  const formData = new FormData();
  formData.append('archivo', input.files[0]);

  try {
    const response = await fetch(`${API_BASE}/auditorias/${auditoriaActual.id}/transferencias/import`, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'No se pudo importar transferencias.');

    await Promise.all([cargarTransferenciasModulo(1), cargarTransferenciasModulo(9)]);
    alert(`Importación completada. Filas procesadas: ${result.importedCount}`);
  } catch (error) {
    console.error(error);
    alert(error.message);
  }
}

async function importarTransferenciasDesdeIndicador9() {
  const input9 = document.getElementById('archivo-transferencias-9');
  if (!input9.files.length) return alert('Selecciona un archivo Excel.');

  const sharedInput = document.getElementById('archivo-transferencias');
  const dt = new DataTransfer();
  dt.items.add(input9.files[0]);
  sharedInput.files = dt.files;
  await importarTransferencias();
}

async function guardarTransferencia(transferenciaId, moduleNumber) {
  if (!auditoriaActual?.id) return;

  const justificado = document.getElementById(`just-${transferenciaId}`).checked;
  const observacion = document.getElementById(`obs-${transferenciaId}`).value.trim();

  try {
    const response = await fetch(`${API_BASE}/auditorias/${auditoriaActual.id}/transferencias/${transferenciaId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ justificado, observacion })
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'No se pudo guardar transferencia.');

    await cargarTransferenciasModulo(moduleNumber);
  } catch (error) {
    console.error(error);
    alert(error.message);
  }
}

function renderCreditosTable() {
  const tbody = document.getElementById('creditos-table-2');
  const rows = moduleState[2].creditos || [];

  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="9">Sin datos importados.</td></tr>';
    return;
  }

  tbody.innerHTML = rows.map((row) => {
    const hasClaim = row.tiene_reclamo === 1;
    const statusClass = row.cumple_final === 1 ? 'ok' : 'fail';
    const statusLabel = row.cumple_final === 1 ? 'Si cumple' : 'No cumple';

    return `
      <tr>
        <td>${formatDate(row.fecha)}</td>
        <td>${row.articulo || '-'}</td>
        <td>${row.numero_comprobante || '-'}</td>
        <td>${formatNumber(row.cantidad)}</td>
        <td>${formatMoney(row.importe)}</td>
        <td>
          <select id="reclamo-${row.id}" class="reclamo-select">
            <option value="0" ${!hasClaim ? 'selected' : ''}>No</option>
            <option value="1" ${hasClaim ? 'selected' : ''}>Si</option>
          </select>
        </td>
        <td><span class="status-chip ${statusClass}">${statusLabel}</span></td>
        <td><textarea id="credito-obs-${row.id}">${row.observacion || ''}</textarea></td>
        <td><button class="btn btn-secondary" onclick="guardarCredito('${row.id}')">Guardar</button></td>
      </tr>
    `;
  }).join('');
}

async function cargarCreditosModulo() {
  if (!auditoriaActual?.id) return;

  const response = await fetch(`${API_BASE}/auditorias/${auditoriaActual.id}/creditos`);
  if (!response.ok) return;

  const payload = await response.json();
  moduleState[2] = payload;
  updateControlCache(payload.control);

  const total = payload.control.total_items || 0;
  const observadas = payload.control.items_observacion || 0;
  const cumplen = total - observadas;
  renderSummary(2, total, cumplen, observadas, payload.control.score_cumplimiento || 0);
  renderCreditosTable();
  recalcularScoreFinalLocal();
}

async function importarCreditos() {
  if (!auditoriaActual?.id) return alert('Abre una auditoría primero.');

  const input = document.getElementById('archivo-creditos');
  if (!input.files.length) return alert('Selecciona un archivo Excel.');

  const formData = new FormData();
  formData.append('archivo', input.files[0]);

  try {
    const response = await fetch(`${API_BASE}/auditorias/${auditoriaActual.id}/creditos/import`, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'No se pudo importar créditos.');

    await cargarCreditosModulo();
    alert(`Importación de créditos completada. Filas procesadas: ${result.importedCount}`);
  } catch (error) {
    console.error(error);
    alert(error.message);
  }
}

async function guardarCredito(creditoId) {
  if (!auditoriaActual?.id) return;

  const tieneReclamo = document.getElementById(`reclamo-${creditoId}`).value === '1';
  const observacion = document.getElementById(`credito-obs-${creditoId}`).value.trim();

  try {
    const response = await fetch(`${API_BASE}/auditorias/${auditoriaActual.id}/creditos/${creditoId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tiene_reclamo: tieneReclamo, observacion })
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'No se pudo actualizar el registro.');

    await cargarCreditosModulo();
  } catch (error) {
    console.error(error);
    alert(error.message);
  }
}

function renderVentasInternasSummary(payload) {
  const control = payload?.control || null;
  const total = control?.total_items || 0;
  const observadas = control?.items_observacion || 0;
  const cumplen = total - observadas;
  const score = control?.score_cumplimiento || 0;
  const totalMuestra = payload?.totalMuestra || 0;
  const totalComprobantesVtaMostrador = payload?.totalComprobantesVtaMostrador || 0;
  const totalComprobantesMuestra = payload?.totalComprobantesMuestra || 0;
  const container = document.getElementById('transfer-summary-8');
  if (!container) return;

  container.innerHTML = `
    <div class="summary-card"><span>Total muestra</span><strong>${total}</strong></div>
    <div class="summary-card"><span>Comprobantes auditados</span><strong>${totalMuestra}</strong></div>
    <div class="summary-card"><span>Cpbtes Vta. Mostrador</span><strong>${totalComprobantesVtaMostrador}</strong></div>
    <div class="summary-card"><span>Cpbtes en muestra</span><strong>${totalComprobantesMuestra}</strong></div>
    <div class="summary-card"><span>Cumplen</span><strong>${cumplen}</strong></div>
    <div class="summary-card"><span>No cumplen</span><strong>${observadas}</strong></div>
    <div class="summary-card"><span>% Cumplimiento</span><strong>${formatPercent(score)}</strong></div>
  `;
}

async function descargarMuestraVentasInternas() {
  if (!auditoriaActual?.id) return alert('Abre una auditoría primero.');

  try {
    const response = await fetch(`${API_BASE}/auditorias/${auditoriaActual.id}/ventas-internas/export`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'No se pudo descargar la muestra.');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    const contentDisposition = response.headers.get('content-disposition') || '';
    const fileNameMatch = contentDisposition.match(/filename="([^"]+)"/i);
    const fileName = fileNameMatch?.[1] || 'muestra_ventas_internas.xlsx';

    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error(error);
    alert(error.message);
  }
}

function renderVentasInternasTable() {
  const tbody = document.getElementById('ventas-internas-table-8');
  if (!tbody) return;

  const allRows = (moduleState[8]?.ventasInternas || []).filter((row) => row.en_muestra === 1);

  if (!allRows.length) {
    tbody.innerHTML = '<tr><td colspan="12">No hay registros en muestra.</td></tr>';
    return;
  }

  // Agrupar por comprobante
  const comprobanteMap = new Map();
  allRows.forEach((row) => {
    const key = row.numero_comprobante;
    if (!comprobanteMap.has(key)) {
      comprobanteMap.set(key, []);
    }
    comprobanteMap.get(key).push(row);
  });

  // Convertir a array y renderizar una fila por comprobante
  const comprobanteRows = Array.from(comprobanteMap.values()).map((filasDelComprobante) => {
    // Usar la primera fila como representante del comprobante
    const primerRow = filasDelComprobante[0];
    const importeTotalComprobante = filasDelComprobante.reduce(
      (accumulator, item) => accumulator + Number(item.importe || 0),
      0
    );
    
    // Concatenar todos los artículos del comprobante
    const articulos = filasDelComprobante
      .map((r) => `${r.articulo_codigo || '-'} / ${r.articulo_descripcion || '-'}`)
      .join(' | ');

    // Un comprobante cumple si al menos una fila cumple
    const algunaCumple = filasDelComprobante.some((r) => r.cumple_final === 1);
    const statusClass = algunaCumple ? 'ok' : 'fail';
    const statusLabel = algunaCumple ? 'Si cumple' : 'No cumple';

    return `
      <tr>
        <td>${formatDate(primerRow.fecha)}</td>
        <td>${primerRow.tipo_comprobante || '-'}</td>
        <td>${primerRow.numero_comprobante || '-'}</td>
        <td class="col-articulos">${articulos}</td>
        <td>${primerRow.imputacion_contable || '-'}</td>
        <td>${formatMoney(importeTotalComprobante)}</td>
        <td>
          <select id="firma-deposito-${primerRow.id}" onchange="guardarVentaInternaComprobante(this)">
            <option value="0" ${primerRow.firma_responsable_deposito === 0 ? 'selected' : ''}>No</option>
            <option value="1" ${primerRow.firma_responsable_deposito === 1 ? 'selected' : ''}>Si</option>
          </select>
        </td>
        <td>
          <select id="firma-gerente-${primerRow.id}" onchange="guardarVentaInternaComprobante(this)">
            <option value="0" ${primerRow.firma_gerente_sector === 0 ? 'selected' : ''}>No</option>
            <option value="1" ${primerRow.firma_gerente_sector === 1 ? 'selected' : ''}>Si</option>
          </select>
        </td>
        <td><input type="checkbox" id="venta-just-${primerRow.id}" ${primerRow.justificado === 1 ? 'checked' : ''} onchange="guardarVentaInternaComprobante(this)"></td>
        <td><span class="status-chip ${statusClass}">${statusLabel}</span></td>
        <td><textarea id="venta-obs-${primerRow.id}" onchange="guardarVentaInternaComprobante(this)">${primerRow.observacion || ''}</textarea></td>
        <td>
          <button class="btn btn-secondary" onclick="guardarVentaInternaComprobante(document.getElementById('firma-deposito-${primerRow.id}'))">Guardar</button>
        </td>
      </tr>
    `;
  }).join('');

  tbody.innerHTML = comprobanteRows;
}

async function cargarVentasInternasModulo() {
  if (!auditoriaActual?.id) return;

  const response = await fetch(`${API_BASE}/auditorias/${auditoriaActual.id}/ventas-internas`);
  if (!response.ok) return;

  const payload = await response.json();
  moduleState[8] = payload;
  updateControlCache(payload.control);

  renderVentasInternasSummary(payload);
  renderVentasInternasTable();
  recalcularScoreFinalLocal();
}

async function importarVentasInternas() {
  if (!auditoriaActual?.id) return alert('Abre una auditoría primero.');

  const input = document.getElementById('archivo-ventas-internas');
  if (!input.files.length) return alert('Selecciona el archivo de ventas internas.');

  const formData = new FormData();
  formData.append('archivo', input.files[0]);

  try {
    const response = await fetch(`${API_BASE}/auditorias/${auditoriaActual.id}/ventas-internas/import`, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'No se pudo importar ventas internas.');

    await cargarVentasInternasModulo();
    alert(
      `Importación completada. Filas: ${result.importedCount}. `
      + `Cpbtes Vta. Mostrador: ${result.totalComprobantesVtaMostrador}. `
      + `Cpbtes en muestra: ${result.totalComprobantesMuestra}. `
      + `Muestra final (comprobantes): ${result.totalMuestra}.`
    );
  } catch (error) {
    console.error(error);
    alert(error.message);
  }
}

async function guardarVentaInternaComprobante(element) {
  if (!auditoriaActual?.id) return;

  const ventaId = String(element.id || '')
    .replace(/^firma-deposito-/, '')
    .replace(/^firma-gerente-/, '')
    .replace(/^venta-just-/, '')
    .replace(/^venta-obs-/, '');
  const allRows = (moduleState[8]?.ventasInternas || []).filter((row) => row.en_muestra === 1);
  
  // Encontrar el comprobante de esta fila
  const primerRow = allRows.find((r) => String(r.id) === ventaId);
  if (!primerRow) return;

  const numeroComprobante = primerRow.numero_comprobante;

  // Obtener valores del formulario
  const firmaResponsableDeposito = document.getElementById(`firma-deposito-${ventaId}`).value === '1';
  const firmaGerenteSector = document.getElementById(`firma-gerente-${ventaId}`).value === '1';
  const justificado = document.getElementById(`venta-just-${ventaId}`).checked;
  const observacion = document.getElementById(`venta-obs-${ventaId}`).value.trim();

  // Encontrar todas las filas del comprobante
  const filasDelComprobante = allRows.filter((row) => row.numero_comprobante === numeroComprobante);

  try {
    // Actualizar todas las filas del comprobante
    for (const fila of filasDelComprobante) {
      const response = await fetch(`${API_BASE}/auditorias/${auditoriaActual.id}/ventas-internas/${fila.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          firma_responsable_deposito: firmaResponsableDeposito,
          firma_gerente_sector: firmaGerenteSector,
          justificado,
          observacion
        })
      });

      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'No se pudo actualizar la venta interna.');
    }

    await cargarVentasInternasModulo();
  } catch (error) {
    console.error(error);
    alert(error.message);
  }
}

async function guardarVentaInterna(ventaId) {
  if (!auditoriaActual?.id) return;

  const firmaResponsableDeposito = document.getElementById(`firma-deposito-${ventaId}`).value === '1';
  const firmaGerenteSector = document.getElementById(`firma-gerente-${ventaId}`).value === '1';
  const justificado = document.getElementById(`venta-just-${ventaId}`).checked;
  const observacion = document.getElementById(`venta-obs-${ventaId}`).value.trim();

  try {
    const response = await fetch(`${API_BASE}/auditorias/${auditoriaActual.id}/ventas-internas/${ventaId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        firma_responsable_deposito: firmaResponsableDeposito,
        firma_gerente_sector: firmaGerenteSector,
        justificado,
        observacion
      })
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'No se pudo actualizar la venta interna.');

    await cargarVentasInternasModulo();
  } catch (error) {
    console.error(error);
    alert(error.message);
  }
}

function renderGenericSummary(moduleNumber) {
  const control = getControlByModule(moduleNumber);
  const container = document.getElementById(`generic-summary-${moduleNumber}`);
  const input = document.getElementById(`manual-score-${moduleNumber}`);
  if (!container || !input || !control) return;

  input.value = ((control.score_cumplimiento || 0) * 100).toFixed(2);

  container.innerHTML = `
    <div class="summary-card"><span>Ponderación</span><strong>${(control.ponderacion * 100).toFixed(2)}%</strong></div>
    <div class="summary-card"><span>% Cumplimiento</span><strong>${formatPercent(control.score_cumplimiento || 0)}</strong></div>
    <div class="summary-card"><span>Resultado</span><strong>${formatPercent(control.resultado_final || 0)}</strong></div>
  `;
}

async function guardarIndicadorManual(moduleNumber) {
  if (!auditoriaActual?.id) return;

  const control = getControlByModule(moduleNumber);
  if (!control) return;

  const input = document.getElementById(`manual-score-${moduleNumber}`);
  const percent = Number(input.value);
  if (Number.isNaN(percent) || percent < 0 || percent > 100) {
    alert('Ingresa un porcentaje válido entre 0 y 100');
    return;
  }

  const scoreCumplimiento = percent / 100;
  const resultadoFinal = (control.ponderacion || 0) * scoreCumplimiento;

  try {
    const response = await fetch(`${API_BASE}/auditorias/${auditoriaActual.id}/controles/${control.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ score_cumplimiento: scoreCumplimiento, resultado_final: resultadoFinal })
    });

    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.error || 'No se pudo guardar el indicador');
    }

    control.score_cumplimiento = scoreCumplimiento;
    control.resultado_final = resultadoFinal;
    renderGenericSummary(moduleNumber);
    recalcularScoreFinalLocal();
  } catch (error) {
    console.error(error);
    alert(error.message);
  }
}

function mostrarResumenAuditoria() {
  if (!auditoriaActual) {
    alert('No hay auditoría activa');
    return;
  }

  const controlesActivos = getControlesActivos(auditoriaActual.controles || []);
  const indicadoresCompletos = controlesActivos.length > 0
    && controlesActivos.every((control) => Number.isFinite(Number(control.score_cumplimiento)));
  const auditoriaCompletada = auditoriaActual.estado === 'completada';

  // Actualizar info básica
  setTextIfExists('resumen-codigo', auditoriaActual.codigo);
  setTextIfExists('resumen-auditor', auditoriaActual.auditor_nombre || formatAuditorDisplay(auditoriaActual.auditor_id));
  setTextIfExists('resumen-sucursal', auditoriaActual.sucursal);
  setTextIfExists('resumen-fecha', new Date(auditoriaActual.fecha_realizacion).toLocaleDateString());
  setTextIfExists('resumen-estado', auditoriaActual.estado);

  // Renderizar tabla de indicadores
  const tbody = document.getElementById('resumen-indicadores-tabla');
  if (!tbody) return;

  tbody.innerHTML = controlesActivos
    .map((control) => {
      const score = control.score_cumplimiento || 0;
      const resultado = control.resultado_final || 0;
      return `
        <tr>
          <td><strong>${control.modulo_nombre}</strong></td>
          <td>${control.etapa || '-'}</td>
          <td>${(control.ponderacion * 100).toFixed(2)}%</td>
          <td>${formatPercent(score)}</td>
          <td>${formatPercent(resultado)}</td>
        </tr>
      `;
    })
    .join('');

  // Renderizar totales
  const scoreFinal = auditoriaActual.score_final || 0;
  const calificacion = auditoriaActual.calificacion || obtenerCalificacion(scoreFinal);
  setTextIfExists('resumen-score-final', `${(scoreFinal * 100).toFixed(2)}%`);
  setTextIfExists('resumen-calificacion', calificacion);

  hydrateResumenCierreState(controlesActivos);
  renderResumenCierre(controlesActivos, indicadoresCompletos, auditoriaCompletada);

  const cierreState = getResumenCierreComputedState(controlesActivos, auditoriaCompletada);

  const cerrarBtn = document.getElementById('btn-cerrar-exportar');
  const guardarBtn = document.getElementById('btn-guardar-cierre');
  const compartirBtn = document.getElementById('btn-compartir-outlook');

  if (cerrarBtn) {
    cerrarBtn.disabled = !cierreState.puedeCerrar;
  }

  if (guardarBtn) {
    guardarBtn.disabled = auditoriaCompletada;
  }

  if (compartirBtn) {
    compartirBtn.disabled = !auditoriaCompletada;
  }

  mostrarChecklistCierre(cierreState);
  const motivos = cierreState.motivos;
  mostrarMotivosBloqueoCierre(motivos);
}

function getResumenCierreComputedState(controlesActivos, auditoriaCompletada) {
  const faltantesIndicadores = (controlesActivos || [])
    .filter((control) => !Number.isFinite(Number(control.score_cumplimiento)))
    .map((control) => control.modulo_nombre || `Módulo ${control.modulo_numero}`);

  const hallazgosValidos = (resumenCierreState.hallazgos || [])
    .map((item) => ({
      id: String(item.id || '').trim(),
      indicador: String(item.indicador || '').trim(),
      gravedad: String(item.gravedad || '').trim().toLowerCase(),
      descripcion: String(item.descripcion || '').trim()
    }))
    .filter((item) => item.id && item.indicador && ['alta', 'media', 'baja'].includes(item.gravedad) && item.descripcion);

  const hallazgoIds = new Set(hallazgosValidos.map((item) => item.id));

  const recomendacionesValidas = (resumenCierreState.recomendaciones || [])
    .map((item) => ({
      id: String(item.id || '').trim(),
      hallazgoId: String(item.hallazgoId || '').trim(),
      descripcion: String(item.descripcion || '').trim()
    }))
    .filter((item) => item.id && item.hallazgoId && item.descripcion && hallazgoIds.has(item.hallazgoId));

  const motivos = obtenerMotivosBloqueoCierre(controlesActivos, auditoriaCompletada);

  return {
    auditoriaCompletada,
    faltantesIndicadores,
    hallazgosValidos,
    recomendacionesValidas,
    motivos,
    puedeCerrar: !auditoriaCompletada && !motivos.length
  };
}

function obtenerMotivosBloqueoCierre(controlesActivos, auditoriaCompletada) {
  const motivos = [];

  if (auditoriaCompletada) {
    motivos.push('La auditoría ya está cerrada y completada.');
    return motivos;
  }

  const faltantesIndicadores = (controlesActivos || [])
    .filter((control) => !Number.isFinite(Number(control.score_cumplimiento)))
    .map((control) => control.modulo_nombre || `Módulo ${control.modulo_numero}`);

  if (faltantesIndicadores.length) {
    motivos.push(`Faltan % de cumplimiento en: ${faltantesIndicadores.join(', ')}`);
  }

  const hallazgos = (resumenCierreState.hallazgos || [])
    .map((item) => ({
      id: String(item.id || '').trim(),
      indicador: String(item.indicador || '').trim(),
      gravedad: String(item.gravedad || '').trim().toLowerCase(),
      descripcion: String(item.descripcion || '').trim()
    }))
    .filter((item) => item.id && item.indicador && ['alta', 'media', 'baja'].includes(item.gravedad) && item.descripcion);

  const hallazgoIds = new Set(hallazgos.map((item) => item.id));
  const recomendaciones = (resumenCierreState.recomendaciones || [])
    .map((item) => ({
      id: String(item.id || '').trim(),
      hallazgoId: String(item.hallazgoId || '').trim(),
      descripcion: String(item.descripcion || '').trim()
    }))
    .filter((item) => item.id && item.hallazgoId && item.descripcion && hallazgoIds.has(item.hallazgoId));

  if (!hallazgos.length) {
    motivos.push('Debes cargar al menos un hallazgo completo (indicador, gravedad y descripción).');
  }

  if (!recomendaciones.length) {
    motivos.push('Debes cargar al menos una recomendación completa vinculada a un hallazgo.');
  }

  return motivos;
}

function mostrarChecklistCierre(cierreState) {
  const container = document.getElementById('resumen-cierre-checklist');
  if (!container) return;

  const reglas = [
    {
      ok: cierreState.faltantesIndicadores.length === 0,
      labelOk: 'Indicadores completos: OK',
      labelPending: `Indicadores pendientes: ${cierreState.faltantesIndicadores.length}`
    },
    {
      ok: cierreState.hallazgosValidos.length > 0,
      labelOk: 'Hallazgos completos: OK',
      labelPending: 'Hallazgos completos: pendiente'
    },
    {
      ok: cierreState.recomendacionesValidas.length > 0,
      labelOk: 'Recomendaciones completas: OK',
      labelPending: 'Recomendaciones completas: pendiente'
    }
  ];

  container.style.display = 'block';
  container.innerHTML = `
    <strong>Checklist de cierre</strong>
    <ul>
      ${reglas.map((regla) => `<li class="${regla.ok ? 'ok' : 'pending'}">${regla.ok ? '✅' : '⚠️'} ${regla.ok ? regla.labelOk : regla.labelPending}</li>`).join('')}
    </ul>
  `;
}

function mostrarMotivosBloqueoCierre(motivos = []) {
  const container = document.getElementById('resumen-cierre-motivos');
  if (!container) return;

  if (!motivos.length) {
    container.style.display = 'none';
    container.innerHTML = '';
    return;
  }

  container.style.display = 'block';
  container.innerHTML = `
    <strong>No se puede cerrar la auditoría por estos motivos:</strong>
    <ul>${motivos.map((motivo) => `<li>${motivo}</li>`).join('')}</ul>
  `;
}

function tryParseJsonArray(value) {
  try {
    const parsed = JSON.parse(String(value || ''));
    return Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function getControlesIndicatorOptions(controlesActivos) {
  return controlesActivos.map((control) => ({
    key: String(control.modulo_numero),
    label: control.modulo_nombre
  }));
}

function hydrateResumenCierreState(controlesActivos) {
  const rawHallazgos = tryParseJsonArray(auditoriaActual?.hallazgos);
  const rawRecomendaciones = tryParseJsonArray(auditoriaActual?.recomendaciones);
  const options = getControlesIndicatorOptions(controlesActivos);
  const firstIndicator = options[0]?.key || '';

  if (rawHallazgos) {
    resumenCierreState.hallazgos = rawHallazgos.map((item, index) => ({
      id: item.id || `H${index + 1}`,
      indicador: String(item.indicador || firstIndicator),
      gravedad: ['alta', 'media', 'baja'].includes(String(item.gravedad || '').toLowerCase())
        ? String(item.gravedad).toLowerCase()
        : 'media',
      descripcion: String(item.descripcion || '')
    }));
  } else if (String(auditoriaActual?.hallazgos || '').trim()) {
    resumenCierreState.hallazgos = [{
      id: 'H1',
      indicador: firstIndicator,
      gravedad: 'media',
      descripcion: String(auditoriaActual.hallazgos || '')
    }];
  } else if (!resumenCierreState.hallazgos.length) {
    resumenCierreState.hallazgos = [{
      id: 'H1',
      indicador: firstIndicator,
      gravedad: 'media',
      descripcion: ''
    }];
  }

  if (rawRecomendaciones) {
    const defaultHallazgoId = resumenCierreState.hallazgos[0]?.id || 'H1';
    resumenCierreState.recomendaciones = rawRecomendaciones.map((item, index) => ({
      id: item.id || `R${index + 1}`,
      hallazgoId: String(item.hallazgoId || defaultHallazgoId),
      descripcion: String(item.descripcion || '')
    }));
  } else if (String(auditoriaActual?.recomendaciones || '').trim()) {
    resumenCierreState.recomendaciones = [{
      id: 'R1',
      hallazgoId: resumenCierreState.hallazgos[0]?.id || 'H1',
      descripcion: String(auditoriaActual.recomendaciones || '')
    }];
  } else if (!resumenCierreState.recomendaciones.length) {
    resumenCierreState.recomendaciones = [{
      id: 'R1',
      hallazgoId: resumenCierreState.hallazgos[0]?.id || 'H1',
      descripcion: ''
    }];
  }
}

function renderResumenCierre(controlesActivos, indicadoresCompletos, auditoriaCompletada) {
  const hallazgosContainer = document.getElementById('resumen-hallazgos-lista');
  const recomendacionesContainer = document.getElementById('resumen-recomendaciones-lista');
  const addHallazgoBtn = document.getElementById('btn-agregar-hallazgo');
  const addRecomendacionBtn = document.getElementById('btn-agregar-recomendacion');
  if (!hallazgosContainer || !recomendacionesContainer) return;

  const readOnly = !indicadoresCompletos || auditoriaCompletada;
  const indicatorOptions = getControlesIndicatorOptions(controlesActivos);
  const hallazgoOptions = resumenCierreState.hallazgos.map((item) => ({
    id: item.id,
    label: `${item.id} · ${item.gravedad.toUpperCase()}`
  }));

  hallazgosContainer.innerHTML = resumenCierreState.hallazgos.length
    ? resumenCierreState.hallazgos.map((hallazgo, index) => {
    const optionsHtml = indicatorOptions
      .map((opt) => `<option value="${opt.key}" ${opt.key === hallazgo.indicador ? 'selected' : ''}>${opt.label}</option>`)
      .join('');

    return `
      <article class="hallazgo-item">
        <div class="hallazgo-item-head">
          <span>Hallazgo ${index + 1}</span>
          ${readOnly ? '' : `<button type="button" class="btn btn-secondary btn-inline-delete" onclick="eliminarHallazgoResumen(${index})">Eliminar</button>`}
        </div>
        <div class="hallazgo-item-grid">
          <div class="form-group">
            <label>Indicador de referencia</label>
            <select ${readOnly ? 'disabled' : ''} onchange="actualizarHallazgoCampo(${index}, 'indicador', this.value)">
              ${optionsHtml}
            </select>
          </div>
          <div class="form-group">
            <label>Gravedad</label>
            <select ${readOnly ? 'disabled' : ''} onchange="actualizarHallazgoCampo(${index}, 'gravedad', this.value)">
              <option value="alta" ${hallazgo.gravedad === 'alta' ? 'selected' : ''}>Alta</option>
              <option value="media" ${hallazgo.gravedad === 'media' ? 'selected' : ''}>Media</option>
              <option value="baja" ${hallazgo.gravedad === 'baja' ? 'selected' : ''}>Baja</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>Descripción del hallazgo</label>
          <textarea ${readOnly ? 'disabled' : ''} rows="4" placeholder="Describe el hallazgo detectado" oninput="actualizarHallazgoCampo(${index}, 'descripcion', this.value)" onchange="actualizarHallazgoCampo(${index}, 'descripcion', this.value)">${hallazgo.descripcion || ''}</textarea>
        </div>
      </article>
    `;
  }).join('')
    : '<div class="hallazgo-empty">No hay hallazgos cargados.</div>';

  recomendacionesContainer.innerHTML = resumenCierreState.recomendaciones.length
    ? resumenCierreState.recomendaciones.map((item, index) => {
    const optionsHtml = hallazgoOptions
      .map((opt) => `<option value="${opt.id}" ${opt.id === item.hallazgoId ? 'selected' : ''}>${opt.label}</option>`)
      .join('');

    return `
      <article class="hallazgo-item recomendacion-item">
        <div class="hallazgo-item-head">Recomendación ${index + 1}</div>
        <div class="form-group">
          <label>Hallazgo de referencia</label>
          <select ${readOnly ? 'disabled' : ''} onchange="actualizarRecomendacionCampo(${index}, 'hallazgoId', this.value)">
            ${optionsHtml}
          </select>
        </div>
        <div class="form-group">
          <label>Descripción de la recomendación</label>
          <textarea ${readOnly ? 'disabled' : ''} rows="4" placeholder="Describe la recomendación" oninput="actualizarRecomendacionCampo(${index}, 'descripcion', this.value)" onchange="actualizarRecomendacionCampo(${index}, 'descripcion', this.value)">${item.descripcion || ''}</textarea>
        </div>
      </article>
    `;
  }).join('')
    : '<div class="hallazgo-empty">No hay recomendaciones cargadas.</div>';

  if (addHallazgoBtn) addHallazgoBtn.disabled = readOnly;
  if (addRecomendacionBtn) addRecomendacionBtn.disabled = readOnly || !resumenCierreState.hallazgos.length;
}

function getNextItemId(prefix, items) {
  const max = (items || []).reduce((acc, item) => {
    const match = String(item?.id || '').match(/\d+/);
    const num = match ? Number(match[0]) : 0;
    return Number.isFinite(num) && num > acc ? num : acc;
  }, 0);
  return `${prefix}${max + 1}`;
}

function actualizarHallazgoCampo(index, field, value) {
  if (!resumenCierreState.hallazgos[index]) return;
  resumenCierreState.hallazgos[index][field] = field === 'descripcion' ? String(value || '').trim() : String(value || '');
  const controlesActivos = getControlesActivos(auditoriaActual?.controles || []);
  const auditoriaCompletada = auditoriaActual?.estado === 'completada';
  const cierreState = getResumenCierreComputedState(controlesActivos, auditoriaCompletada);
  mostrarChecklistCierre(cierreState);
  mostrarMotivosBloqueoCierre(cierreState.motivos);
  const cerrarBtn = document.getElementById('btn-cerrar-exportar');
  if (cerrarBtn) cerrarBtn.disabled = !cierreState.puedeCerrar;
}

function actualizarRecomendacionCampo(index, field, value) {
  if (!resumenCierreState.recomendaciones[index]) return;
  resumenCierreState.recomendaciones[index][field] = String(value || '').trim();
  const controlesActivos = getControlesActivos(auditoriaActual?.controles || []);
  const auditoriaCompletada = auditoriaActual?.estado === 'completada';
  const cierreState = getResumenCierreComputedState(controlesActivos, auditoriaCompletada);
  mostrarChecklistCierre(cierreState);
  mostrarMotivosBloqueoCierre(cierreState.motivos);
  const cerrarBtn = document.getElementById('btn-cerrar-exportar');
  if (cerrarBtn) cerrarBtn.disabled = !cierreState.puedeCerrar;
}

function agregarHallazgoResumen() {
  if (!auditoriaActual) return;
  const controlesActivos = getControlesActivos(auditoriaActual.controles || []);
  const nextId = getNextItemId('H', resumenCierreState.hallazgos);
  resumenCierreState.hallazgos.push({
    id: nextId,
    indicador: String(controlesActivos[0]?.modulo_numero || ''),
    gravedad: 'media',
    descripcion: ''
  });
  if (!resumenCierreState.recomendaciones.length) {
    resumenCierreState.recomendaciones.push({ id: 'R1', hallazgoId: nextId, descripcion: '' });
  }
  const indicadoresCompletos = controlesActivos.length > 0 && controlesActivos.every((control) => Number.isFinite(Number(control.score_cumplimiento)));
  const auditoriaCompletada = auditoriaActual.estado === 'completada';
  renderResumenCierre(controlesActivos, indicadoresCompletos, auditoriaCompletada);
  const cierreState = getResumenCierreComputedState(controlesActivos, auditoriaCompletada);
  mostrarChecklistCierre(cierreState);
  mostrarMotivosBloqueoCierre(cierreState.motivos);
  const cerrarBtn1 = document.getElementById('btn-cerrar-exportar');
  if (cerrarBtn1) cerrarBtn1.disabled = !cierreState.puedeCerrar;
}

function eliminarHallazgoResumen(index) {
  if (!auditoriaActual) return;
  const hallazgo = resumenCierreState.hallazgos[index];
  if (!hallazgo) return;

  resumenCierreState.hallazgos.splice(index, 1);
  resumenCierreState.recomendaciones = resumenCierreState.recomendaciones.filter(
    (item) => item.hallazgoId !== hallazgo.id
  );

  const fallbackHallazgoId = resumenCierreState.hallazgos[0]?.id || null;
  if (fallbackHallazgoId) {
    resumenCierreState.recomendaciones = resumenCierreState.recomendaciones.map((item) => ({
      ...item,
      hallazgoId: item.hallazgoId || fallbackHallazgoId
    }));
  }

  const controlesActivos = getControlesActivos(auditoriaActual.controles || []);
  const indicadoresCompletos = controlesActivos.length > 0 && controlesActivos.every((control) => Number.isFinite(Number(control.score_cumplimiento)));
  const auditoriaCompletada = auditoriaActual.estado === 'completada';
  renderResumenCierre(controlesActivos, indicadoresCompletos, auditoriaCompletada);
  const cierreState2 = getResumenCierreComputedState(controlesActivos, auditoriaCompletada);
  mostrarChecklistCierre(cierreState2);
  mostrarMotivosBloqueoCierre(cierreState2.motivos);
  const cerrarBtn2 = document.getElementById('btn-cerrar-exportar');
  if (cerrarBtn2) cerrarBtn2.disabled = !cierreState2.puedeCerrar;
}

function agregarRecomendacionResumen() {
  if (!auditoriaActual) return;
  const hallazgoId = resumenCierreState.hallazgos[0]?.id;
  if (!hallazgoId) {
    alert('Primero agrega un hallazgo para poder asociar una recomendación.');
    return;
  }
  const nextId = getNextItemId('R', resumenCierreState.recomendaciones);
  resumenCierreState.recomendaciones.push({ id: nextId, hallazgoId, descripcion: '' });
  const controlesActivos = getControlesActivos(auditoriaActual.controles || []);
  const indicadoresCompletos = controlesActivos.length > 0 && controlesActivos.every((control) => Number.isFinite(Number(control.score_cumplimiento)));
  const auditoriaCompletada = auditoriaActual.estado === 'completada';
  renderResumenCierre(controlesActivos, indicadoresCompletos, auditoriaCompletada);
  const cierreState3 = getResumenCierreComputedState(controlesActivos, auditoriaCompletada);
  mostrarChecklistCierre(cierreState3);
  mostrarMotivosBloqueoCierre(cierreState3.motivos);
  const cerrarBtn3 = document.getElementById('btn-cerrar-exportar');
  if (cerrarBtn3) cerrarBtn3.disabled = !cierreState3.puedeCerrar;
}

async function guardarCierreBorrador() {
  if (!auditoriaActual?.id) {
    alert('No hay auditoría activa');
    return;
  }

  const activeElement = document.activeElement;
  if (activeElement && typeof activeElement.blur === 'function') {
    activeElement.blur();
  }

  const hallazgos = (resumenCierreState.hallazgos || []).map((item) => ({
    id: String(item.id || '').trim(),
    indicador: String(item.indicador || '').trim(),
    gravedad: String(item.gravedad || '').trim().toLowerCase(),
    descripcion: String(item.descripcion || '').trim()
  }));

  const recomendaciones = (resumenCierreState.recomendaciones || []).map((item) => ({
    id: String(item.id || '').trim(),
    hallazgoId: String(item.hallazgoId || '').trim(),
    descripcion: String(item.descripcion || '').trim()
  }));

  try {
    const response = await fetch(`${API_BASE}/auditorias/${auditoriaActual.id}/cierre-borrador`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        hallazgos: JSON.stringify(hallazgos),
        recomendaciones: JSON.stringify(recomendaciones)
      })
    });

    const responseText = await response.text();
    let payload = null;
    try {
      payload = responseText ? JSON.parse(responseText) : null;
    } catch {
      payload = null;
    }

    if (!response.ok) {
      const isHtmlResponse = String(responseText || '').trim().startsWith('<');
      const fallback = isHtmlResponse
        ? 'No se pudo guardar el borrador. Verifica que el backend esté reiniciado y actualizado.'
        : 'No se pudo guardar el borrador de cierre';
      throw new Error(payload?.error || fallback);
    }

    if (!payload || !payload.auditoria) {
      throw new Error('Respuesta inválida al guardar borrador. Reinicia backend y vuelve a intentar.');
    }

    auditoriaActual = { ...auditoriaActual, ...payload.auditoria };
    alert('Hallazgos y recomendaciones guardados correctamente');
  } catch (error) {
    console.error(error);
    alert(error.message);
  }
}

function descargarInformeJSON() {
  if (!auditoriaActual) {
    alert('No hay auditoría activa');
    return;
  }

  const informe = {
    auditoria: {
      id: auditoriaActual.id,
      codigo: auditoriaActual.codigo,
      auditor: auditoriaActual.auditor_nombre || auditoriaActual.auditor_id,
      sucursal: auditoriaActual.sucursal,
      fecha_realizacion: auditoriaActual.fecha_realizacion,
      estado: auditoriaActual.estado,
      score_final: auditoriaActual.score_final,
      calificacion: auditoriaActual.calificacion || obtenerCalificacion(auditoriaActual.score_final || 0)
    },
    indicadores: (auditoriaActual.controles || []).map((control) => ({
      numero: control.modulo_numero,
      nombre: control.modulo_nombre,
      etapa: control.etapa,
      ponderacion: control.ponderacion,
      score_cumplimiento: control.score_cumplimiento,
      resultado_final: control.resultado_final,
      total_items: control.total_items,
      items_observacion: control.items_observacion
    })),
    fecha_exportacion: new Date().toISOString()
  };

  informe.indicadores = informe.indicadores.filter((control) => MODULOS_ACTIVOS.includes(control.numero));

  const blob = new Blob([JSON.stringify(informe, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `Informe_${auditoriaActual.codigo}_${Date.now()}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function generarInformeHTML() {

  if (!auditoriaActual) {
    alert('No hay auditoría activa');
    return;
  }

  const score = auditoriaActual.score_final || 0;
  const calificacion = auditoriaActual.calificacion || obtenerCalificacion(score);
  const controlesActivos = getControlesActivos(auditoriaActual.controles || []);

  const html = `
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Informe - ${auditoriaActual.codigo}</title>
  <style>
    body { font-family: Arial, sans-serif; color: #1f2937; margin: 40px; }
    h1 { color: #c2410c; }
    table { width: 100%; border-collapse: collapse; margin-top: 16px; }
    th, td { border: 1px solid #d1d5db; padding: 8px; text-align: left; }
    th { background: #f3f4f6; }
  </style>
</head>
<body>
  <h1>Tablero de Resultados - Control Integral de Depósito</h1>
  <p><strong>Auditoría:</strong> ${auditoriaActual.codigo}</p>
  <p><strong>Empresa:</strong> ${auditoriaActual.empresa || '-'}</p>
  <p><strong>Sucursal:</strong> ${auditoriaActual.sucursal}</p>
  <p><strong>Auditor:</strong> ${auditoriaActual.auditor_nombre || auditoriaActual.auditor_id}</p>
  <p><strong>Fecha:</strong> ${new Date(auditoriaActual.fecha_realizacion).toLocaleDateString()}</p>
  <p><strong>Score:</strong> ${(score * 100).toFixed(2)}%</p>
  <p><strong>Calificación:</strong> ${calificacion}</p>

  <table>
    <thead>
      <tr>
        <th>Módulo</th>
        <th>Etapa</th>
        <th>Ponderación</th>
        <th>% Cumplimiento</th>
        <th>Resultado</th>
      </tr>
    </thead>
    <tbody>
      ${controlesActivos.map((control) => `
        <tr>
          <td>${control.modulo_nombre}</td>
          <td>${control.etapa || '-'}</td>
          <td>${(control.ponderacion * 100).toFixed(2)}%</td>
          <td>${formatPercent(control.score_cumplimiento || 0)}</td>
          <td>${formatPercent(control.resultado_final || 0)}</td>
        </tr>
      `).join('')}
    </tbody>
  </table>
</body>
</html>
  `;

  const blob = new Blob([html], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `Auditoria_${auditoriaActual.codigo}_${Date.now()}.html`;
  link.click();
  URL.revokeObjectURL(url);
}

function exportarInformePDF() {
  if (!auditoriaActual) {
    alert('No hay auditoría activa');
    return;
  }

  if (!window.jspdf || !window.jspdf.jsPDF) {
    alert('No se pudo cargar el generador PDF');
    return;
  }

  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ orientation: 'p', unit: 'pt', format: 'a4' });
  const controlesActivos = getControlesActivos(auditoriaActual.controles || []);
  const score = Number(auditoriaActual.score_final || 0);
  const calificacion = auditoriaActual.calificacion || obtenerCalificacion(score);

  const pageWidth = doc.internal.pageSize.getWidth();
  const formatPercent = (value) => `${(Number(value || 0) * 100).toFixed(2)}%`;
  const formatDate = (value) => {
    if (!value) return '-';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return '-';
    return parsed.toLocaleDateString('es-AR');
  };
  const cleanPdfText = (value) => {
    const text = String(value ?? '-')
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n')
      .replace(/\u00a0/g, ' ')
      .replace(/[≈≃∼]/g, 'aprox. ')
      .replace(/[×]/g, 'x')
      .replace(/[–—]/g, '-')
      .replace(/[•]/g, '- ')
      .replace(/[“”]/g, '"')
      .replace(/[‘’]/g, "'")
      .replace(/\t/g, ' ')
      .replace(/\s+\n/g, '\n')
      .replace(/\n{2,}/g, '\n')
      .replace(/[ ]{2,}/g, ' ')
      .trim();
    return text || '-';
  };

  const EMPRESA_PALETTES = {
    Autolux:  { main: [198, 0, 0],    etapa: [220, 0, 0],    etapaText: [255, 255, 255] },
    Autosol:  { main: [28, 78, 175],  etapa: [35, 95, 210],  etapaText: [255, 255, 255] },
    Ciel:     { main: [30, 30, 30],   etapa: [50, 50, 50],   etapaText: [255, 255, 255] },
    Portico:  { main: [155, 105, 65], etapa: [175, 125, 80], etapaText: [255, 255, 255] },
    VOGE:     { main: [20, 20, 20],   etapa: [220, 185, 0],  etapaText: [20, 20, 20] }
  };
  const empresaKey = String(auditoriaActual.empresa || '');
  const compPalette = EMPRESA_PALETTES[empresaKey] || EMPRESA_PALETTES.Autosol;
  const brandColor = compPalette.main;
  const etapaFill = compPalette.etapa;
  const etapaTextColor = compPalette.etapaText;
  const palette = {
    lightGray: [244, 244, 244],
    dark: [32, 32, 32],
    white: [255, 255, 255]
  };

  const calificacionTexto = {
    SAT: 'No existen desvíos, o si existen estos son escasos y no significativos.',
    ADE: 'Se detectan oportunidades de mejora de impacto controlado.',
    SUJ: 'Existen desvíos que requieren acciones prioritarias de mejora.',
    NAD: 'Se observan desviaciones relevantes que afectan la operación.',
    INS: 'La situación requiere intervención inmediata y plan de corrección.'
  };

  const califCode = String(calificacion).split(' - ')[0] || String(calificacion);
  const scoreLabel = `${(score * 100).toFixed(2).replace('.', ',')}%`;

  doc.setFillColor(...brandColor);
  doc.rect(0, 0, pageWidth, 76, 'F');

  doc.setTextColor(...palette.white);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(21);
  doc.text('Control Integral de Depósito', 28, 33);
  doc.setFontSize(13);
  doc.text('Tablero de Resultados', 28, 54);
  doc.setFontSize(12);
  doc.text('GRUPO CENOA', pageWidth - 142, 34);

  doc.setFillColor(...palette.white);
  doc.roundedRect(28, 92, 230, 56, 10, 10, 'F');
  doc.roundedRect(pageWidth - 258, 92, 230, 56, 10, 10, 'F');

  doc.setTextColor(...palette.dark);
  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.text('Sucursal', 44, 116);
  doc.setFont('helvetica', 'normal');
  doc.text(String(auditoriaActual.sucursal || '-'), 44, 134);

  doc.setFont('helvetica', 'bold');
  doc.text('Fecha de realización', pageWidth - 242, 116);
  doc.setFont('helvetica', 'normal');
  doc.text(formatDate(auditoriaActual.fecha_realizacion), pageWidth - 242, 134);

  doc.setDrawColor(110, 110, 110);
  doc.setFillColor(...palette.lightGray);
  doc.roundedRect(44, 176, pageWidth - 88, 116, 18, 18, 'FD');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(12);
  doc.text('Calificación global del control:', 298, 212);
  doc.setFontSize(25);
  doc.text(scoreLabel, 112, 250);
  doc.setFontSize(24);
  doc.text(califCode, 298, 246);
  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');
  doc.text(
    calificacionTexto[califCode] || 'Resultado global de la auditoría.',
    298,
    266,
    { maxWidth: 240 }
  );

  doc.setFillColor(...brandColor);
  doc.rect(28, 318, pageWidth - 56, 26, 'F');
  doc.setTextColor(...palette.white);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(14);
  doc.text('Tablero de Resultados - Control Integral de Depósito', 50, 336);

  const infoRows = [
    ['Sucursal', String(auditoriaActual.sucursal || '-')],
    ['Auditor', String(auditoriaActual.auditor_nombre || auditoriaActual.auditor_id || '-')],
    ['Fecha de realización', formatDate(auditoriaActual.fecha_realizacion)],
    ['Código Auditoría', String(auditoriaActual.codigo || '-')]
  ];

  doc.autoTable({
    body: infoRows,
    startY: 344,
    margin: { left: 28, right: 28 },
    theme: 'grid',
    styles: { fontSize: 10, cellPadding: 4, textColor: [255, 255, 255] },
    columnStyles: {
      0: { fillColor: brandColor, fontStyle: 'bold', cellWidth: 170 },
      1: { fillColor: brandColor }
    }
  });

  const tableBody = controlesActivos.map((control) => ([
    String(control.etapa || '-'),
    String(control.modulo_nombre || '-'),
    formatPercent(control.ponderacion),
    formatPercent(control.score_cumplimiento),
    formatPercent(control.resultado_final)
  ]));

  doc.autoTable({
    head: [['Etapas', 'Parámetros', 'Ponderación', '% Cumplimiento', 'Resultado final']],
    body: tableBody,
    startY: (doc.lastAutoTable?.finalY || 380) + 2,
    margin: { left: 28, right: 28 },
    theme: 'grid',
    styles: { fontSize: 9, cellPadding: 4, textColor: [0, 0, 0] },
    headStyles: { fillColor: brandColor, textColor: [255, 255, 255], fontStyle: 'bold' },
    alternateRowStyles: { fillColor: [248, 248, 248] },
    didParseCell: (hookData) => {
      if (hookData.section === 'body' && hookData.column.index === 0) {
        hookData.cell.styles.fillColor = etapaFill;
        hookData.cell.styles.textColor = etapaTextColor;
        hookData.cell.styles.fontStyle = 'bold';
      }
      if (hookData.section === 'body' && hookData.column.index >= 2) {
        hookData.cell.styles.halign = 'center';
      }
    }
  });

  const hallazgos = tryParseJsonArray(auditoriaActual.hallazgos) || [];
  const recomendaciones = tryParseJsonArray(auditoriaActual.recomendaciones) || [];
  const hallazgosMap = new Map(hallazgos.map((item) => [item.id, item]));

  let startY = (doc.lastAutoTable?.finalY || 560) + 22;
  if (startY > 720) {
    doc.addPage();
    startY = 46;
  }

  doc.setFillColor(...brandColor);
  doc.rect(28, startY, pageWidth - 56, 22, 'F');
  doc.setTextColor(...palette.white);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(12);
  doc.text('Hallazgos', 40, startY + 15);

  doc.autoTable({
    head: [['ID', 'Indicador', 'Gravedad', 'Descripción']],
    body: (hallazgos.length ? hallazgos : [{ id: '-', indicador: '-', gravedad: '-', descripcion: '-' }]).map((item) => ([
      cleanPdfText(item.id),
      cleanPdfText(item.indicador),
      cleanPdfText(item.gravedad),
      cleanPdfText(item.descripcion)
    ])),
    startY: startY + 22,
    margin: { left: 28, right: 28 },
    theme: 'grid',
    styles: {
      fontSize: 9,
      cellPadding: { top: 6, right: 6, bottom: 6, left: 6 },
      overflow: 'linebreak',
      valign: 'top',
      lineWidth: 0.5,
      lineColor: [210, 214, 220],
      halign: 'left',
      cellWidth: 'wrap'
    },
    headStyles: {
      fillColor: brandColor,
      textColor: [255, 255, 255],
      fontStyle: 'bold',
      valign: 'middle'
    },
    alternateRowStyles: { fillColor: [248, 248, 248] },
    columnStyles: {
      0: { cellWidth: 34, halign: 'center', fontStyle: 'bold' },
      1: { cellWidth: 52, halign: 'center' },
      2: { cellWidth: 64, halign: 'center' },
      3: { cellWidth: pageWidth - 56 - 34 - 52 - 64 }
    },
    rowPageBreak: 'avoid'
  });

  let recomendacionesStartY = (doc.lastAutoTable?.finalY || startY + 30) + 20;
  if (recomendacionesStartY > 720) {
    doc.addPage();
    recomendacionesStartY = 46;
  }

  doc.setFillColor(...brandColor);
  doc.rect(28, recomendacionesStartY, pageWidth - 56, 22, 'F');
  doc.setTextColor(...palette.white);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(12);
  doc.text('Recomendaciones', 40, recomendacionesStartY + 15);

  doc.autoTable({
    head: [['ID', 'Hallazgo ref.', 'Descripción']],
    body: (recomendaciones.length ? recomendaciones : [{ id: '-', hallazgoId: '-', descripcion: '-' }]).map((item) => ([
      cleanPdfText(item.id),
      cleanPdfText(`${item.hallazgoId || '-'}${hallazgosMap.get(item.hallazgoId)?.gravedad ? ` (${String(hallazgosMap.get(item.hallazgoId).gravedad).toUpperCase()})` : ''}`),
      cleanPdfText(item.descripcion)
    ])),
    startY: recomendacionesStartY + 22,
    margin: { left: 28, right: 28 },
    theme: 'grid',
    styles: {
      fontSize: 9,
      cellPadding: { top: 6, right: 6, bottom: 6, left: 6 },
      overflow: 'linebreak',
      valign: 'top',
      lineWidth: 0.5,
      lineColor: [210, 214, 220],
      halign: 'left',
      cellWidth: 'wrap'
    },
    headStyles: {
      fillColor: brandColor,
      textColor: [255, 255, 255],
      fontStyle: 'bold',
      valign: 'middle'
    },
    alternateRowStyles: { fillColor: [248, 248, 248] },
    columnStyles: {
      0: { cellWidth: 34, halign: 'center', fontStyle: 'bold' },
      1: { cellWidth: 92, halign: 'center' },
      2: { cellWidth: pageWidth - 56 - 34 - 92 }
    },
    rowPageBreak: 'avoid'
  });

  doc.save(`Informe_${auditoriaActual.codigo}_${Date.now()}.pdf`);
}

async function cerrarAuditoriaYExportarPDF() {
  if (!auditoriaActual?.id) {
    alert('No hay auditoría activa');
    return;
  }

  const activeElement = document.activeElement;
  if (activeElement && typeof activeElement.blur === 'function') {
    activeElement.blur();
  }

  const hallazgos = (resumenCierreState.hallazgos || [])
    .map((item) => ({
      id: String(item.id || '').trim(),
      indicador: String(item.indicador || '').trim(),
      gravedad: String(item.gravedad || '').trim().toLowerCase(),
      descripcion: String(item.descripcion || '').trim()
    }))
    .filter((item) => item.id && item.indicador && ['alta', 'media', 'baja'].includes(item.gravedad) && item.descripcion);

  const recomendaciones = (resumenCierreState.recomendaciones || [])
    .map((item) => ({
      id: String(item.id || '').trim(),
      hallazgoId: String(item.hallazgoId || '').trim(),
      descripcion: String(item.descripcion || '').trim()
    }))
    .filter((item) => item.id && item.hallazgoId && item.descripcion);

  const controlesActivos = getControlesActivos(auditoriaActual.controles || []);
  const motivosPrevios = obtenerMotivosBloqueoCierre(controlesActivos, auditoriaActual.estado === 'completada');
  if (motivosPrevios.length) {
    mostrarMotivosBloqueoCierre(motivosPrevios);
    alert('No se puede cerrar la auditoría. Revisa los motivos en pantalla.');
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/auditorias/${auditoriaActual.id}/cierre`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        hallazgos: JSON.stringify(hallazgos),
        recomendaciones: JSON.stringify(recomendaciones)
      })
    });

    const responseText = await response.text();
    let payload = null;
    try {
      payload = responseText ? JSON.parse(responseText) : null;
    } catch {
      payload = null;
    }

    if (!response.ok) {
      const backendMotivos = [];
      if (Array.isArray(payload?.faltantes) && payload.faltantes.length) {
        backendMotivos.push(`Faltan % de cumplimiento en: ${payload.faltantes.join(', ')}`);
      }
      if (payload?.error) {
        backendMotivos.push(payload.error);
      }
      if (backendMotivos.length) {
        mostrarMotivosBloqueoCierre(backendMotivos);
      }

      const message = payload?.error
        || (responseText && !responseText.trim().startsWith('<') ? responseText : '')
        || 'No se pudo cerrar la auditoría';
      throw new Error(message);
    }

    if (!payload || !payload.auditoria) {
      throw new Error('Respuesta inválida al cerrar la auditoría. Reinicia backend y vuelve a intentar.');
    }

    auditoriaActual = {
      ...auditoriaActual,
      ...payload.auditoria,
      hallazgos: JSON.stringify(hallazgos),
      recomendaciones: JSON.stringify(recomendaciones)
    };

    mostrarResumenAuditoria();
    await Promise.all([cargarAuditorias(), cargarDashboard()]);
    exportarInformePDF();
    alert('Auditoría cerrada y PDF exportado correctamente');
  } catch (error) {
    console.error(error);
    alert(error.message);
  }
}

function compartirPorOutlook() {
  if (!auditoriaActual?.id) {
    alert('No hay auditoría activa');
    return;
  }

  if (auditoriaActual.estado !== 'completada') {
    alert('Primero debes cerrar la auditoría para compartir el informe.');
    return;
  }

  const hallazgos = tryParseJsonArray(auditoriaActual.hallazgos) || [];
  const recomendaciones = tryParseJsonArray(auditoriaActual.recomendaciones) || [];
  const hallazgosTexto = hallazgos.length
    ? hallazgos.map((item) => `- ${item.id} [${String(item.gravedad || '').toUpperCase()}] ${item.descripcion}`).join('\n')
    : '-';
  const recomendacionesTexto = recomendaciones.length
    ? recomendaciones.map((item) => `- ${item.id} (${item.hallazgoId}) ${item.descripcion}`).join('\n')
    : '-';

  const subject = encodeURIComponent(`Informe de Auditoría ${auditoriaActual.codigo}`);
  const body = encodeURIComponent(
    `Hola,\n\nSe comparte el informe de la auditoría ${auditoriaActual.codigo} (${auditoriaActual.empresa || '-' } - ${auditoriaActual.sucursal || '-' }).\n` +
    `Hallazgos:\n${hallazgosTexto}\n\n` +
    `Recomendaciones:\n${recomendacionesTexto}\n\n` +
    'Adjuntar el PDF exportado desde la aplicación.\n\nSaludos.'
  );

  window.location.href = `mailto:?subject=${subject}&body=${body}`;
}

// ── Sesión de auditor ──────────────────────────────────────────────────────
function renderAuditorSelectOptions(selectedValue = '') {
  const select = document.getElementById('login-nombre-select');
  if (!select) return;

  select.innerHTML = '<option value="">Seleccionar auditor...</option>' + AUDITORES_DISPONIBLES
    .map((nombre) => `<option value="${nombre}" ${nombre === selectedValue ? 'selected' : ''}>${nombre}</option>`)
    .join('');
}

function mostrarLoginModal() {
  const modal = document.getElementById('login-modal');
  if (!modal) return;
  modal.style.display = 'flex';
  const select = document.getElementById('login-nombre-select');
  renderAuditorSelectOptions();
  if (select) {
    select.focus();
    select.onkeydown = (e) => { if (e.key === 'Enter') confirmarAuditor(); };
  }
}

function confirmarAuditor() {
  const select = document.getElementById('login-nombre-select');
  const nombre = (select?.value || '').trim();
  if (!AUDITORES_DISPONIBLES.includes(nombre)) {
    if (select) select.style.borderColor = 'var(--danger, #c62828)';
    return;
  }
  localStorage.setItem('auditor_nombre', nombre);
  const modal = document.getElementById('login-modal');
  if (modal) modal.style.display = 'none';
  document.getElementById('auditor-sesion-label').textContent = nombre;
  _inicializarApp();
}

function cambiarAuditor() {
  if (!confirm('¿Deseas cambiar de auditor?')) return;
  localStorage.removeItem('auditor_nombre');
  location.reload();
}
// ────────────────────────────────────────────────────────────────────────────

async function _inicializarApp() {
  await cargarConfiguracion();
  cargarDashboard();
}

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  const nombre = localStorage.getItem('auditor_nombre');
  if (!AUDITORES_DISPONIBLES.includes(nombre || '')) {
    localStorage.removeItem('auditor_nombre');
    mostrarLoginModal();
  } else {
    const label = document.getElementById('auditor-sesion-label');
    if (label) label.textContent = nombre;
    _inicializarApp();
  }
});
