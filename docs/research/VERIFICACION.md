# Evidencia de verificación

Fecha: 2026-11-03, America/Mexico_City. Exportado del ledger SQLite temporal de comprobaciones reales.

| Fase | Comprobación | Resultado | Evidencia |
| --- | --- | --- | --- |
| baseline | repository-baseline | PASS | VideosIA commit41954f9 only README.md+AGENTS.md; no package/code/docs |
| baseline | original-npm-test | FAIL / histórico | ENOENT package.json: documented demo not present |
| baseline | upstream-osv | FAIL / histórico | 130 lock packages; 4 affected: multidict pyasn1 python-multipart setuptools |
| baseline | defender-source | PASS | Custom scan event1001 completed; no1116 in scan window; definitions1.463.110.0 |
| after | upstream-parse | PASS | compileall app cli.py main.py passes |
| after | osv-corrected-lock | PASS | 130 registry packages checked; zero returned advisories |
| after | real-render-first | PASS | 15.17s H2641080x1920 AAC; full decode both streams; native pre-guard demo; no publishing |
| after | focused-fork-tests-before-test-update | FAIL / histórico | 54passed1failed: old test expected empty-key bypass; updated assertion to503 |
| after | full-upstream-suite-interrupted | FAIL / histórico | Broader suite interrupted after initial failures; not counted passing |
| after | root-tests | PASS | 21checks:20passed1Windows-symlinkskip; real bootstrap sockets denied tests |
| after | root-parse | PASS | npm run check + compileall scripts |
| after | fork-focused-http | PASS | 427passed6skipped82subtests; real authenticated TestClient fixtures |
| after | guarded-real-render | PASS | Socket guard enabled; real MP4 produced and full audio/video decode passed |
| after | readiness-secrets | PASS | fixed local JSON contract + env whitelist + ignored runtime; no provider keys |
| after | readiness-degradation | PASS | failure manifest terminal, missing executable handled; cloud routes not enabled |
| after | readiness-observability | PASS | private per-job logs and failed state; no automatic publication |
| after | root-lint-final | PASS | ruff videosia tests scripts passes afterunusedimportsfix |
| after | fork-lint | PASS | ruff changed stagedPython files passes |
| after | root-regression-unicode | PASS | New test failed beforefix then rejects surrogateintextpaths afterfix |
| after | native-media-network-regression | PASS | Actual wheelFFmpeg fakeDASH .mp4 + loopbackHTTP receiver:zeroGET |
| after | root-tests-round2 | PASS | 30 checks:28passed2Windowsplatformskips |
| review | security-round1 | FAIL / histórico | FAIL:highnativeFFmpegnetwork;mediumPOSIXperms;bothfixesinstagedround2 |
| review | logic-round1 | FAIL / histórico | FAIL:Unicode,hostffmpegpreflight,Dockerprovenance;allfixedwithregressions |
| review | quality-round1 | FAIL / histórico | FAIL:conflictingChineseauthcomment;updated |
| review | security-round2 | PASS | PASS; actual FFmpeg/DASH regression noHTTP; privatePOSIXdirs;28pass2skip |
| review | logic-round2 | PASS | PASS; Unicode/preflight/immutableimage provenancefixed;28pass2skip |
| review | quality-round2 | PASS | PASS; bilingualauthcommentsfixed;commandsanddocsconsistent |
| after | fork-focused-final | PASS | 55passed21subtests after finalconfigcommentfix |
| after | defender-installed-environment | PASS | Customscan100seconds completed21:07:03; events1000/1001;no1116 |
| after | render-safe-demuxer | PASS | Real guardedrender2aa0dea7 succeededwithmov/filepipe QA |
| after | final-npm-test-render | PASS | npm run test:render passed; engine91bd7e5 clean; full forcedMOVlocalprotocoldecode;15.17s1080x1920AAC |

## Alcance y límites

- VideosIA: 30 comprobaciones, 28 correctas y 2 omisiones por Windows (symlink y permisos POSIX).
- Motor: 427 pruebas enfocadas correctas, 6 omisiones y 82 subtests. Una ejecución global se interrumpió al detectar supuestos antiguos de auth; no se declara toda la suite global correcta. Se adaptaron los tests afectados a clave real y se repitió el conjunto enfocado.
- Tres revisiones finales PASS tras corregir Unicode, QA nativo con red, permisos, requisitos/procedencia Docker y comentario de autenticación.
- Docker no instalado: imagen/contenedor sin ejecutar; sus argumentos y procedencia tienen pruebas unitarias.
- MP4 real con decodificación completa de audio y video. Sin ffprobe: dimensiones/duración se comprobaron adicionalmente leyendo FFmpeg; no se inventan en el manifiesto.
- No se prueban publicación, ingresos, cuentas sociales o subtítulos. Defender/OSV/revisión no certifican ausencia universal de malware.

## Entrega

- Motor: `91bd7e5dffe27bb2dd8fe6b7dd7ea0bf4aaa8bdd`.
- PR motor: https://github.com/al2242000122/MoneyPrinterTurbo/pull/1
- Rama raíz: `feat/moneyprinter-integration`.
- Rollback: revertir el commit de integración; no elimina datos locales. El motor conserva upstream en su historial.
