# MoneyPrinterTurbo local Implementation Plan

> For agentic workers: ejecutar por entregables con verificación y revisión.

**Goal:** integrar un fork revisado y producir un video local con manifiesto.

**Architecture:** coordinador Python estándar y submódulo MoneyPrinterTurbo.
Cada trabajo valida entrada, crea runtime propio e invoca la CLI con batch local.
El contenedor opcional bloquea salida de red a nivel de runtime.

**Tech Stack:** Python 3.11+, unittest, MoneyPrinterTurbo, FFmpeg, Windows SAPI demo.

**Spec:** ../specs/2026-11-03-moneyprinter-design.md

## Global Constraints

- AUTO_PUBLISH=false y publication_allowed=false.
- No secretos o videos en Git; no proveedores cloud en la primera entrega.
- No afirmar API, n8n, subtítulos o Docker probados si no se ejecutaron.

## Task 1: fork y privacidad

- [x] Clonar ambos repos y documentar diferencias README/código real.
- [x] Crear fork mediante API GitHub autenticada y verificar parent/fork=true.
- [x] Revisar fuente sin ejecutar; Defender y OSV sobre lock como datos.
- [x] Corregir defaults y dependencias, actualizar lock y repetir OSV.
- [x] Ejecutar pruebas de auth, divulgación y privacidad del fork.

## Task 2: circuito local real

- [x] Implementar videosia/ con validación antes de crear procesos.
- [x] Probar rechazo de URLs/rutas externas y entorno sin credenciales heredadas.
- [x] Generar PNG y WAV propios con voz es-MX instalada, sin proveedor remoto.
- [x] Ejecutar render real y decode FFmpeg; guardar manifiesto de evidencia.

## Task 3: entrega verificable

- [x] Documentar políticas YouTube y auditoría con rutas/commits/fuentes.
- [x] Revisiones adversariales de seguridad, lógica y calidad; corregir hallazgos.
- [x] Commit/push en ramas propias y PR de integración sin mezclar main (se verifica antes de entrega).
