# Auditoría de MoneyPrinterTurbo

Fecha: 2026-11-03, America/Mexico_City. Base oficial revisada: `c8dbf96e9dfee43b30f7c3f440175d6bd4de61de`. Fork: https://github.com/al2242000122/MoneyPrinterTurbo.

## Conclusión y límites

No se encontró evidencia de malware o exfiltración encubierta en los flujos fuente inspeccionados. No certifica ausencia de malware, dependencias comprometidas o fallos desconocidos. Sí existen comunicaciones a terceros por las funciones ofrecidas; upstream no es un programa que nunca envíe datos.

Se revisaron arranque, scripts, dependencias, red/proveedores, logs, claves, API, publicación y descargas antes de ejecutar. No se usó su instalador automático de skill ni paquetes de arranque de terceros.

## Antivirus

Microsoft Defender activo, firmas `1.463.110.0` actualizadas el 3 de noviembre. Examen personalizado del clon oficial terminado 20:33:48: eventos 1000/1001 con el mismo identificador, sin detecciones 1116 en esa ventana. Este examen inicial cubrió el clon; no todos los futuros paquetes/modelos ni todo su comportamiento.

Segundo examen personalizado del entorno Python instalado: comenzó 21:05:23 y terminó 21:07:03 (100 segundos), eventos 1000/1001 con el mismo identificador y sin eventos de detección 1116 en esa ventana. Tampoco es una certificación de comportamiento ni cubre descargas futuras.

## Dependencias: consulta real a OSV

Se consultaron 130 paquetes del lock por nombre/versión, sin enviar claves, prompts ni archivos privados.

| Paquete | Antes | Corregido | Avisos representativos |
| --- | --- | --- | --- |
| multidict | 6.7.1 | 7.2.1 | [GHSA-54p9-h82j-f925](https://osv.dev/vulnerability/GHSA-54p9-h82j-f925) |
| pyasn1 | 0.6.4 | 0.6.5 | [GHSA-2qm8-x737-gmw5](https://osv.dev/vulnerability/GHSA-2qm8-x737-gmw5) y otros tres |
| python-multipart | 0.0.30 | 0.0.33 | [GHSA-v9pg-7xvm-68hf](https://osv.dev/vulnerability/GHSA-v9pg-7xvm-68hf) |
| setuptools | 82.0.1 | 84.2.1 | [GHSA-h35f-9h28-mq5c](https://osv.dev/vulnerability/GHSA-h35f-9h28-mq5c), [GHSA-xmj3-9gf7-h52w](https://osv.dev/vulnerability/GHSA-xmj3-9gf7-h52w) |

La segunda consulta devolvió cero avisos para las 130 versiones. No equivale a detectar malware. Se instalaron wheels del lock desde PyPI oficial sin builds de fuentes. uv regeneró metadata/hashes/fechas (diff grande): sólo cambian las cuatro versiones enumeradas.

Repetir: `python scripts/audit_dependencies.py`. Una consulta fallida no cuenta como limpia y detiene el setup. Evidencia: `dependencies-osv-2026-11-03.json`.

## Datos y conexiones observados

| Función upstream | Datos/destino | Primera integración |
| --- | --- | --- |
| LLM | Prompt/guion al proveedor configurado | Guion ya proporcionado |
| TTS cloud, incluido Edge | Texto narrado al servicio | WAV de voz Windows local |
| Stock/generación visual | Términos/prompt y descarga | Medios propios locales |
| Upload-Post | MP4/metadatos a api.upload-post.com | Desactivado, sin credenciales |
| Versión WebUI | Consulta a api.github.com | Opt-in en fork; no se abre WebUI |
| Catálogos/modelos | models.dev, proveedor, Hugging Face | No se seleccionan ni descargan |
| LiteLLM | Catálogo remoto potencial al importar | Catálogo local forzado |
| Config/exportación | Claves en config.toml/JSON local | Runtime nuevo, excluido de Git |

Fuentes: `app/services/{version_checker,codex_models,llm,voice,upload_post,subtitle}.py`, `webui/Main.py`. Lanzadores oficiales desactivan estadísticas Streamlit: eso no desactiva todos los servicios. El fork elimina guiones completos de dos logs identificados y baja el nivel a WARNING; otros logs y la salida CLI pueden contener contenido y deben quedar privados.

## Mitigaciones y pendientes

- API original escucha en todas las interfaces y permite clave vacía. Fork: loopback y rechazo de acceso protegido sin clave. La integración no abre servidores.
- Descargas de proveedores no tienen protección SSRF general en todas sus rutas (`material.py`, `loomloom.py`). No se exponen por el contrato local; siguen siendo riesgo al usar la interfaz completa con proveedores ajenos.
- Bootstrap bloquea sockets Python antes de importar el motor y excluye credenciales heredadas. Código nativo/subprocesos podrían eludirlo: no es un sandbox de malware.
- Revisión adversarial encontró que FFmpeg podía tratar un falso MP4 como DASH y hacer una solicitud remota. Se eliminan entradas MP4 y se comprueba la firma de las imágenes; el QA de salida fija el demuxer MOV y protocolos file/pipe. Una regresión usa un receptor HTTP local y exige cero solicitudes.
- En POSIX cada trabajo/runtime se crea con permisos 0700. En Windows se aplican ACL heredadas: no se presenta como aislamiento entre usuarios del sistema.
- Docker usa red `none`, entradas de sólo lectura y sin perfil personal. No hay Docker instalado aquí: no se declara contenedor probado.
- Instalación/construcción usan red; el flujo de render local no requiere transmitir contenido. No se gastan APIs ni se publica.
- Tarjetas propias y voz instalada; sin música de upstream. Modelos, fuentes, voces y recursos tienen términos independientes.
