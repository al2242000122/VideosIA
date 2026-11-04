# Decisiones

## ADR-001: MoneyPrinterTurbo como motor local fijado

Fecha: 2026-11-03 (America/Mexico_City).
Estado: implementando por petición explícita del propietario en este chat.

El repositorio remoto inicial sólo contenía README.md y AGENTS.md, aunque el
README describía código y documentos que no estaban versionados. Se conserva
AGENTS.md y se sustituye el inventario del README por capacidades comprobadas.

Se integra el fork como submódulo para conservar procedencia, licencia y posibilidad
de actualizar sin mezclar proyectos Python/Node inexistentes. El nuevo encargo de
MoneyPrinterTurbo tiene prioridad sobre la recomendación anterior de empezar por
HyperFrames/Remotion. No se afirma haber realizado esa comparativa.

Primera entrega: CLI local, entrada limitada, voz local para demo Windows,
manifiesto y QA real. Docker sin red será la opción de aislamiento; ejecutar Python
en un venv no se presenta como protección contra malware. Una auditoría estática,
antivirus y OSV reducen incertidumbre, no prueban ausencia universal de amenazas.
