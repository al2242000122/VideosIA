# VideosIA — videos locales con revisión humana

Primera integración ejecutable del fork de [MoneyPrinterTurbo](https://github.com/al2242000122/MoneyPrinterTurbo), fijado como submódulo en `engines/MoneyPrinterTurbo`. Idioma: español de México.

El repo inicial sólo tenía README y AGENTS: su descripción de API Node.js, demo FFmpeg, n8n y documentos no correspondía a archivos versionados. Esta versión describe capacidades reales. HyperFrames/Remotion siguen pendientes.

## Qué hace hoy

- Valida un JSON cerrado con guion, WAV PCM e imágenes PNG/JPG dentro de `inputs/`.
- Rechaza URLs, rutas externas, proveedores y campos ajenos al contrato.
- Invoca MoneyPrinterTurbo con medios/audio locales, sin LLM ni TTS cloud.
- Crea un runtime por trabajo sin credenciales heredadas ni publicación automática.
- El bootstrap bloquea sockets Python; no es un sandbox contra malware.
- Exige decodificar completamente audio y video del MP4 antes de aprobar QA.
- Conserva hashes, versión/estado Git del motor, derechos, decisión de aviso IA y `publication_allowed=false` en el manifiesto.
- Demo Windows: tarjetas originales y narración de voz es-MX instalada localmente.

No implementa API propia, n8n, investigación automática, publicación, subtítulos sincronizados ni monetización. El demo no tiene subtítulos y requiere revisión editorial y de derechos.

## Inicio en Windows

Git, Python 3.11+ (probado con 3.14.2) y una voz es-MX instalada. Node/npm sólo son atajos opcionales. No requiere claves ni servicios pagados.

```powershell
git clone --recurse-submodules --branch feat/moneyprinter-integration https://github.com/al2242000122/VideosIA.git
cd VideosIA
powershell -NoProfile -File scripts/setup.ps1
python -m videosia doctor
python -m unittest discover -s tests -v
python scripts/create_demo.py
python -m videosia render examples/demo.json
```

El setup consulta OSV antes de instalar y se detiene si encuentra avisos o la consulta falla. Usa PyPI oficial, wheels del lock y no ejecuta builds de fuentes. FFmpeg viene del wheel fijado imageio-ffmpeg o de una instalación propia.

Atajos: `npm test`, `npm run check`, `npm run doctor`, `npm run demo`, `npm run test:render`. Los últimos dos generan un video real. El render devuelve `data/jobs/<uuid>/manifest.json`, que contiene la ruta del MP4 real. Entradas, salidas, logs y secretos se excluyen de Git.

Para tu contenido coloca medios propios en `inputs/`, duplica `examples/demo.json` y usa rutas relativas a esa carpeta. Contrato: `configs/job.schema.json`. Linux/macOS pueden aportar WAV/medios propios; el generador de demo usa Windows.

## Aislamiento de red

El modo nativo bloquea los sockets Python antes de importar el motor, pero conserva permisos del usuario. Código nativo y subprocesos pueden eludir esa defensa; un venv no es un sandbox. Con Docker instalado:

```powershell
docker build -f infra/Dockerfile -t videosia-mpt:local .
python -m videosia render examples/demo.json --container
```

El contenedor usa red `none`, entradas de sólo lectura, sin puertos, claves ni perfil personal. El QA posterior necesita FFmpeg en el host (disponible tras el setup); se comprueba antes de arrancar. Se registra y ejecuta el ID inmutable de la imagen: la revisión del checkout no se atribuye al contenido de la imagen. Construirla necesita red. Docker no está instalado en el equipo de validación: sus argumentos tienen pruebas, pero la imagen/contenedor no se han ejecutado aquí.

## Documentación y seguridad

- [Auditoría y datos enviados](docs/research/AUDITORIA_MONEYPRINTER.md).
- [IA, etiquetas y monetización en YouTube](docs/research/YOUTUBE_IA_Y_MONETIZACION.md).
- [OSV del lock corregido](docs/research/dependencies-osv-2026-11-03.json).
- [Arquitectura](docs/architecture/ARQUITECTURA_OBJETIVO.md), [ADR](docs/architecture/ADR.md), [seguridad](docs/policy/SEGURIDAD.md), [backlog](docs/roadmap/BACKLOG.md).

La interfaz completa de MoneyPrinterTurbo conserva servicios cloud que envían datos cuando se utilizan. La revisión y Defender no certifican ausencia universal de malware. No se instala desde paquetes de arranque de terceros.

Código propio: MIT. El submódulo conserva licencia MIT e historial originales. Ver `THIRD_PARTY_NOTICES.md`; voces, modelos, fuentes y recursos conservan sus propios términos.
