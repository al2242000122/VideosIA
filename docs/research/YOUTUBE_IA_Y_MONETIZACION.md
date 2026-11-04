# IA en YouTube: etiquetas, monetización y repositorios

Consulta: 2026-11-03, hora de México. Sin enlaces a videos concretos no se puede atribuir su falta de etiqueta a una técnica o fallo específico.

## Ausencia de etiqueta no demuestra ausencia de detección

YouTube exige aviso para contenido realista generado o alterado significativamente: personas diciendo algo que no dijeron, eventos alterados o escenas realistas inventadas. Usar IA para ideas, guion, títulos o subtítulos no exige por sí solo ese aviso. El contenido no realista puede quedar fuera del requisito.

La etiqueta puede aparecer en el reproductor o la descripción ampliada. Puede provenir del creador, herramientas de YouTube, C2PA o sistemas internos. Como espectadores no vemos toda la evaluación interna. Estas posibilidades no demuestran cuál corresponde a un video determinado.

Declarar IA no limita por sí solo audiencia ni monetización. Omitir reiteradamente un aviso obligatorio puede provocar retirada o suspensión del programa de partners. [Fuente oficial](https://support.google.com/youtube/answer/14328491?hl=es).

## Monetización: evaluación independiente

El canal debe aportar valor original. Plantillas repetitivas, producción masiva con poca variación y material reutilizado sin aporte sustancial pueden impedir monetizar. Tener permiso de copyright no resuelve por sí solo la política de contenido reutilizado. La revisión considera el canal, no sólo un video. Usar IA puede formar parte de un proceso creativo válido; ni usarla ni etiquetarla garantizan ingresos. [Política oficial](https://support.google.com/youtube/answer/1311392?hl=es).

## Qué encontré en los repos originales

| Repo/commit | Evidencia previa a esta integración |
| --- | --- |
| VideosIA `41954f9` | Sólo README.md y AGENTS.md. Mencionan derechos, revisión humana y no garantizar ingresos. Los documentos de política enlazados no existían; no había detector ni publicador. |
| MoneyPrinterTurbo `c8dbf96` | README describe generación/publicación y advierte sobre música incluida. No encontré explicación específica del detector de YouTube en README/docs revisados. Sí hay una declaración de contenido sintético en código. |

Búsqueda: `synthetic`, `disclos`, `c2pa`, `watermark`, `monetiz`, `inauthentic`, `ai.generated` y `youtube`, seguida de lectura de coincidencias. No cubre toda la historia, issues o recursos externos.

[Código original del publicador](https://github.com/harry0703/MoneyPrinterTurbo/blob/c8dbf96e9dfee43b30f7c3f440175d6bd4de61de/app/services/upload_post.py#L246-L253): enviaba `containsSyntheticMedia=true` para YouTube cuando existía `youtube_extra`. El fork lo hace independiente de los metadatos opcionales y añade regresiones. Se verifica el formulario enviado a Upload-Post; no se ha comprobado propagación en una cuenta real de YouTube. VideosIA no publica en esta fase.

El manifiesto registra `ai_disclosure` y su motivo como revisión humana, no como detector ni solicitud enviada a YouTube. El demo queda `needs_review`; se conserva origen de guion, voz, imágenes y licencias. La aprobación editorial sigue separada del QA técnico.
