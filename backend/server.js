import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import os from 'os';
import { initDb } from './db/database.js';
import auditoriaRoutes from './routes/auditorias.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Inicializar base de datos
initDb();

// Servir frontend estático desde el mismo servidor
app.use(express.static(join(__dirname, '../frontend')));

// Rutas API
app.use('/api/auditorias', auditoriaRoutes);

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// SPA fallback: cualquier ruta no-API sirve el index.html
app.get('*', (req, res) => {
  res.sendFile(join(__dirname, '../frontend/index.html'));
});

// Error handler
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ error: err.message });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log('\n========================================');
  console.log('  Control Integral de Depósitos');
  console.log('  Grupo Cenoa');
  console.log('========================================');
  console.log(`\n  Local:   http://localhost:${PORT}`);

  // Mostrar IPs de red para que otros equipos puedan conectarse
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        console.log(`  Red:     http://${iface.address}:${PORT}`);
      }
    }
  }
  console.log('\n  Comparte la dirección "Red" con los auditores.');
  console.log('========================================\n');
});
