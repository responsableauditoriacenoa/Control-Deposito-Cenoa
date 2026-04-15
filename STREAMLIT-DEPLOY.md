# Streamlit Deployment

## Ejecutar local

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Base de datos

- La version Streamlit usa `data/auditorias.db`.
- Si existe `backend/db/auditorias.db`, en la primera ejecucion se copia a `data/`.
- Si quieres otra ruta, define `CONTROL_DEPOSITOS_DB`.
- Si defines `DATABASE_URL`, la app usa MySQL en lugar de SQLite.
- Alternativamente puedes definir:
  - `MYSQL_HOST`
  - `MYSQL_PORT`
  - `MYSQL_DATABASE`
  - `MYSQL_USER`
  - `MYSQL_PASSWORD`

## Publicar en Streamlit Cloud

1. Sube este proyecto a GitHub.
2. En Streamlit Cloud crea una app nueva desde ese repo.
3. Usa `streamlit_app.py` como `Main file path`.
4. En `Secrets` carga tu conexion MySQL con `DATABASE_URL` o las variables `MYSQL_*`.
5. Si no configuras MySQL, la app cae a SQLite local.

## Importante

- Streamlit Cloud si puede correr esta app Python.
- Streamlit Cloud no puede correr el backend Node actual.
- SQLite sirve para demo y pruebas.
- En Streamlit Cloud, SQLite no es una base persistente robusta para uso real multiusuario.
- Si reinicias, redespliegas o cambia el contenedor, puedes perder cambios hechos en la nube.
- Para tu caso ahora, MySQL ya queda contemplado como base recomendada de despliegue.
