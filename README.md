# Autopercepción Cuatrovientos

Aplicación Flask + Angular 21 para cuestionarios de autopercepción de primero y segundo. Incluye roles de alumnado, tutoría y administración; invitaciones por código; múltiples intentos; análisis individual/grupal y exportación CSV.

## Desarrollo local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
cp .env.example .env
flask --app backend.app db upgrade
flask --app backend.app seed-data
flask --app backend.app run --debug
```

En otra terminal:

```bash
cd frontend
npm install
npm start
```

La API queda en `http://127.0.0.1:5000` y Angular en `http://localhost:4200`.

## Decisiones funcionales

- Rangos iniciales editables: 1,00–1,99 Incipiente; 2,00–2,99 En desarrollo; 3,00–4,00 Generado.
- Los ítems redactados en negativo invierten la puntuación (`5 - respuesta`).
- Las respuestas históricas de los documentos de referencia no se importan por privacidad.
- El enlace RGPD se muestra en acceso y pie de página.
- Google OAuth queda preparado mediante variables de entorno; antes del despliegue hay que registrar la URL final de callback en Google Cloud.

La guía completa de instalación y despliegue se entrega en `docs/Guia_instalacion_y_despliegue.docx`.
