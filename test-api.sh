#!/bin/bash
# Script de prueba rápida del API

# Crear una auditoría de prueba
echo "====== Creando auditoría de prueba ======"
curl -X POST http://localhost:5000/api/auditorias \
  -H "Content-Type: application/json" \
  -d '{
    "codigo": "TEST-001",
    "auditor_id": "AUD_GUSTAVO_ZAMBRANO",
    "sucursal": "Casa Central Jujuy",
    "fecha_realizacion": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }' | jq

echo -e "\n====== Listando auditorías ======"
curl http://localhost:5000/api/auditorias | jq

echo -e "\n====== Health check ======"
curl http://localhost:5000/api/health | jq
