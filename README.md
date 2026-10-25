# VideosIA 🎬 — fábrica reproducible de videos técnicos con IA

**Estado actual: v0.1 / laboratorio local.** Proyecto en español (México) preparado para desarrollo por Codex. **No es un pipeline de publicación automático ni un motor HyperFrames listo para producción.** Incluye investigación profunda, contratos, normas editoriales, planes de agentes, n8n de demostración y un renderizador FFmpeg real para comprobar el circuito técnico sin servicios externos.

## Qué funciona hoy

- API Node.js 22 sin dependencias runtime; endpoint de salud, trabajo demo y trabajos mediante storyboard validado.
- Autenticación por API key, trabajos idempotentes simples, cola **de un solo proceso** y guardado de estados en archivos.
- Render de video MP4 vertical H.264 + audio AAC **silencioso**, transiciones entre escenas estáticas, comparación visual y ffprobe.
- Manifest con flag `publication_allowed=false`; pruebas unitarias y prueba real FFmpeg.
- Flujo n8n manual **requiere configuración**; no publica en Facebook, YouTube ni Instagram.

## Qué NO funciona todavía

Investigación web automática, conexión a Claude/OpenAI/Gemini, narración TTS, marcas temporales, subtítulos auténticos, HyperFrames/Remotion, edición 3D, analítica, almacenamiento S3/R2, aprobación multiusuario, publicación ni monetización. Están detallados como roadmap y especificaciones. **No crear cuentas ni pagar servicios hasta terminar la POC local.**

## Inicio rápido (Linux / WSL2 / macOS con FFmpeg)

1. Instalar Node.js 22 o superior, FFmpeg/ffprobe, Git y una tipografía DejaVu Sans. Se recomienda Docker si no quieres instalar dependencias locales.
2. Ejecutar desde la raíz:

```bash
node -v && ffmpeg -version && ffprobe -version
npm test
npm run demo
# Resultado: data/demo/video-demo.mp4 + manifest.json
```

3. Para levantar la API local (proteger y **no exponer a internet**):

```bash
cp .env.example .env   # .env NO se sube a GitHub
# Asignar una VIDEOSIA_API_KEY aleatoria de 32+ caracteres
set -a; source .env; set +a
npm start
curl http://127.0.0.1:3000/health
curl -X POST http://127.0.0.1:3000/api/v1/demo -H "x-api-key: $VIDEOSIA_API_KEY" -H 'idempotency-key: mi-demo-001'
# Consultar job con GET /api/v1/jobs/<job_id>
```

La API **no sirve el MP4 por HTTP**: el archivo se recupera localmente de `data/renders/<job_id>/video-demo.mp4`. No contiene audio de voz, sólo un canal silencioso para comprobar el contenedor de forma reproducible.

## Docker

```bash
cp .env.example .env
# Configurar VIDEOSIA_API_KEY y, si se usa n8n, N8N_ENCRYPTION_KEY
# Levantar sólo API (localhost:3000)
docker compose -f infra/docker-compose.yml up --build -d api
# n8n opcional: docker compose -f infra/docker-compose.yml --profile automation up -d
```

El contenedor incluye FFmpeg, ffprobe y fuente necesaria. Ver `docs/operations/ENTORNO_Y_DESPLIEGUE.md` para seguridad, almacenamiento y errores.

## Skills listos para Codex

Se incluyen cuatro skills de proyecto en `.agents/skills/`: `research-verification`, `video-render`, `quality-gate` y `automation-n8n`. Codex los descubre por la metadata de `SKILL.md` y permite seleccionarlos según la tarea. Están listos como procedimientos, **no sustituyen integraciones de APIs ni confirman que un motor externo esté instalado**. Más información: https://learn.chatgpt.com/docs/build-skills.

## Ruta de trabajo desde Codex

- Instrucciones obligatorias: [`AGENTS.md`](AGENTS.md).
- Siguiente tarea y aceptación: [`docs/roadmap/BACKLOG.md`](docs/roadmap/BACKLOG.md).
- Arquitectura y estados: [`docs/architecture/ARQUITECTURA_OBJETIVO.md`](docs/architecture/ARQUITECTURA_OBJETIVO.md).
- Investigación de la comunidad: [`docs/research/AUDITORIA_GUIA_COMUNIDAD.md`](docs/research/AUDITORIA_GUIA_COMUNIDAD.md).
- Matriz oficial de fuentes: [`docs/research/FUENTES_OFICIALES.md`](docs/research/FUENTES_OFICIALES.md).
- Derechos y publicación: [`docs/policy/PLATAFORMAS_Y_LICENCIAS.md`](docs/policy/PLATAFORMAS_Y_LICENCIAS.md).

**Prompt inicial para Codex:**

> Lee AGENTS.md y README.md; luego docs/roadmap/BACKLOG.md y los ADR. Ejecuta npm test y npm run demo. Describe exactamente qué es real y qué está planeado. Trabaja únicamente el primer P0 de POC HyperFrames/Remotion y documenta resultados reales. No publiques ni gastes en APIs sin mi aprobación.

## Credenciales y costos

El demo no requiere clave de IA ni servicio de voz. Para fases posteriores las claves son distintas de las suscripciones ChatGPT/Claude. `docs/operations/COSTOS.md` ofrece estructura de medición, no promesas de facturación. Nunca versionar `.env`, logs sensibles ni producciones.

## Publicación

**Bloqueada por diseño.** Cualquier implementación futura requiere evidencia, QA completo, derechos comerciales, cuenta elegible, acceso a API y aprobación persistida fuera de un prompt. Las vistas no garantizan ingresos.

## Licencia y procedencia

Código propio: MIT (`LICENSE`). Las bibliotecas de terceros, voces, modelos, videos, fuentes, músicas y guías comunitarias conservan **sus propias licencias y términos**. La investigación de la comunidad se citó sin redistribuir su material de pago. No se incluyen tipografías ni pesos de IA descargados.