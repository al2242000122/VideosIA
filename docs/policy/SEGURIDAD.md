# Seguridad y datos

- AUTO_PUBLISH=false; ninguna revisión técnica habilita publicación.
- No aceptar código, comandos, URLs o rutas de salida desde el JSON de un trabajo.
- Sólo archivos dentro de inputs/; no introducir material privado en el demo.
- No versionar config.toml, .env, credenciales, logs, audios ni producciones.
- La ejecución local inicial no configura proveedores cloud ni importa credenciales
  de Codex, navegador o sistema. Las voces Windows instaladas trabajan localmente.
- El fork limita la API a loopback y rechaza acceso protegido sin API key. La CLI
  no abre un servidor. No arrancar WebUI/API innecesariamente.
- Uso de proveedores online implica transmisión de prompts, texto, imágenes o
  videos según el servicio. Edge TTS también usa red. Gratis no equivale a local.
- Para aislar la salida de red usar Docker --network none. El modo Python nativo
  está limitado por configuración y revisión, pero no es una barrera de seguridad.
- Construir/instalar con red sólo desde registros oficiales y lock corregido.
- No descargar paquetes de arranque de terceros ni ejecutar instaladores de skills.
- Repetir auditoría OSV y revisión de cambios antes de actualizar el submódulo.
- Los avisos de dependencias son evidencia de versiones afectadas, no prueba
  automática de explotación. Los escaneos no certifican ausencia de malware.
