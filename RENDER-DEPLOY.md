# Deploy en Render

## Lo que ya queda preparado

- La app real corre con `Node.js` desde `backend/server.js`.
- El frontend actual se sirve desde `frontend/`.
- La base `SQLite` puede vivir fuera del repo usando `SQLITE_DB_PATH`.
- El archivo `render.yaml` ya define:
  - `buildCommand`
  - `startCommand`
  - `healthCheckPath`
  - disco persistente en `/var/data`
  - `SQLITE_DB_PATH=/var/data/auditorias.db`

## Como publicarla

1. Entra a Render.
2. Elige `New +` -> `Blueprint`.
3. Conecta el repo `responsableauditoriacenoa/Control-Deposito-Cenoa`.
4. Render va a detectar `render.yaml`.
5. Crea el servicio.

## Importante

- El `Persistent Disk` es clave para que `SQLite` no se pierda entre despliegues.
- La app expone un health check en `/api/health`.
- El servidor ya usa `PORT` y escucha en `0.0.0.0`, que es lo esperado para Render.

## Si quieres cargar una base inicial

Opciones:

- Subir una copia de `auditorias.db` manualmente al disco de Render.
- O hacer un primer despliegue vacío y luego cargar datos desde la app.

## Si luego crecemos

Para uso más intensivo o más concurrencia, el siguiente paso natural sería migrar de `SQLite` a `PostgreSQL`, pero para replicar tu app actual en Render esta preparación ya sirve.
