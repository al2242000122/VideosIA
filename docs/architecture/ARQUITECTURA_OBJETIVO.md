# Arquitectura: primera integración local

VideosIA mantiene su propio contrato de trabajo, manifiestos, revisión editorial
y documentación. MoneyPrinterTurbo es un submódulo Git fijado a un commit del fork
https://github.com/al2242000122/MoneyPrinterTurbo. No se copia su código ni se pierde
su historial. La rama de integración incorpora medidas de privacidad verificadas.

Flujo inicial: JSON validado → archivos dentro de inputs/ → CLI MoneyPrinterTurbo
en proceso hijo → MP4 → decodificación FFmpeg → manifest.json.

Un trabajo sólo admite texto y medios locales. No puede seleccionar proveedor,
comando, URL ni ruta de salida. Usa audio WAV ya grabado/generado localmente, sin
LLM, Edge TTS, generación remota de imágenes, Whisper descargable ni música incluida.
Cada ejecución tiene MPT_HOME propio en data/jobs/ y no recibe claves del entorno.

La ejecución nativa no es un sandbox: el proceso conserva permisos del usuario.
La opción Docker usa --network none, entradas de sólo lectura, sin puertos ni
credenciales, límites de recursos y sin privilegios. Hay que comprobar Docker
disponible antes de afirmar aislamiento efectivo. La construcción de la imagen
y descarga de paquetes necesitan red; la ejecución offline no.

La decisión sobre aviso de IA queda en el manifiesto, pendiente de revisión humana.
QA técnico y clasificación de IA no autorizan publicación. AUTO_PUBLISH y
publication_allowed permanecen false. No se implementa publicación en esta fase.

Subtítulos sincronizados, proveedores cloud, API y comparativa HyperFrames/Remotion
siguen pendientes y requieren aceptación medible antes de anunciarse terminados.
