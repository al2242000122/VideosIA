# Diseño de primera entrega

Autorización: el usuario pidió crear un fork, integrarlo con VideosIA e iniciar el
proyecto; después ordenó ejecutarlo ahora y añadió revisión antivirus/datos.

Se crea un fork GitHub y se conserva VideosIA como coordinador local. La integración
es arquitectónica pero se acota a un trabajo offline completo. La estructura es:
videosia/ (CLI, validación y ejecución), tests/ (límites y estados), inputs/ (medios
locales ignorados), examples/ (JSON), scripts/ (demo local), infra/ (contenedor),
docs/ (arquitectura, auditoría y fuentes), engines/MoneyPrinterTurbo (submódulo).

El trabajo sólo recibe título, guion, WAV, imágenes PNG/JPG locales, derechos y decisión de
divulgación IA. El motor recibe un batch de un video con fuentes locales, BGM
desactivada y sin subtítulos ficticios. No se crean cuentas ni se gastan APIs.

Criterio de aceptación: una ejecución real produce MP4 con audio, supera decode
completo FFmpeg, conserva procedencia/hashes/versión y publication_allowed=false.
La ejecución Docker sólo se declarará probada si existe Docker y se ejecuta.
La auditoría informa límites, dependencias afectadas y comunicaciones legítimas.
