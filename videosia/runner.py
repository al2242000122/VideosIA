"""Adaptador del CLI: medios locales, configuración nueva y publicación bloqueada."""

import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .job import JobError, build_params, load_job, sha256

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "engines" / "MoneyPrinterTurbo"
ENGINE_ENTRY = ROOT / "videosia" / "engine_entry.py"
PROCESS_TIMEOUT = 300
MAX_RESULT_BYTES = 1024 * 1024
CONTAINER_IMAGE = "videosia-mpt:local"


def engine_python(engine=ENGINE):
    relative = "Scripts/python.exe" if os.name == "nt" else "bin/python"
    return engine / ".venv" / relative


def find_ffmpeg(source=None, engine=ENGINE):
    """Ubicaciones explícitas o wheel instalado; nunca descarga un ejecutable."""
    source = os.environ if source is None else source
    configured = source.get("IMAGEIO_FFMPEG_EXE")
    if configured:
        return str(Path(configured).resolve()) if Path(configured).is_file() else None
    search_path = next((value for key, value in source.items() if key.upper() == "PATH"), "")
    installed = shutil.which("ffmpeg", path=search_path)
    if installed:
        return installed
    patterns = (
        "Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg*.exe",
        "lib/python*/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux*",
        "lib/python*/site-packages/imageio_ffmpeg/binaries/ffmpeg-osx*",
    )
    candidates = [path for pattern in patterns for path in (engine / ".venv").glob(pattern) if path.is_file()]
    return str(candidates[0].resolve()) if len(candidates) == 1 else None


def child_environment(runtime, source=None):
    """No hereda claves, proxies ni directorios de credenciales del operador."""
    source = os.environ if source is None else source
    allowed = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT"}
    env = {key: value for key, value in source.items() if key.upper() in allowed}
    temporary = runtime / "tmp"
    temporary.mkdir(exist_ok=True)
    env.update({
        "MPT_HOME": str(runtime), "HOME": str(runtime), "USERPROFILE": str(runtime),
        "APPDATA": str(runtime), "LOCALAPPDATA": str(runtime),
        "TMP": str(temporary), "TEMP": str(temporary), "TMPDIR": str(temporary),
        "HF_HOME": str(runtime / "models"), "HF_HUB_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1", "DO_NOT_TRACK": "1",
        "LITELLM_LOCAL_MODEL_COST_MAP": "True",
        "TRANSFORMERS_OFFLINE": "1", "PYTHONUTF8": "1", "PYTHONNOUSERSITE": "1",
        "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false", "AUTO_PUBLISH": "false",
        "MPT_CHECK_UPDATES": "0",
    })
    ffmpeg = find_ffmpeg(source)
    if ffmpeg:
        env["IMAGEIO_FFMPEG_EXE"] = ffmpeg
    return env


def write_config(runtime):
    config = (
        'log_level = "WARNING"\nlisten_host = "127.0.0.1"\nlisten_port = 8080\n'
        '[diagnostics]\nlog_requests = false\n'
        '[app]\napi_key = "' + secrets.token_hex(32) + '"\n'
        'llm_provider = ""\nvideo_source = "local"\n'
        'upload_post_enabled = false\nupload_post_auto_upload = false\n'
        'upload_post_api_key = ""\nsubtitle_provider = ""\ntls_verify = true\n'
        '[ui]\nvoice_mode = "upload"\nsubtitle_enabled = false\nbgm_type = ""\n'
    )
    (runtime / "config.toml").write_text(config, encoding="utf-8")


def run_logged(command, runtime, stem, *, cwd, env):
    """Salida a disco en vez de memoria; no muestra guiones ni errores del proveedor."""
    stdout_path, stderr_path = runtime / f"{stem}.stdout", runtime / f"{stem}.stderr"
    with stdout_path.open("wb") as output, stderr_path.open("wb") as errors:
        process = None
        try:
            options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=output, stderr=errors,
                                       shell=False, **options)
            returncode = process.wait(timeout=PROCESS_TIMEOUT)
        except subprocess.TimeoutExpired as exc:
            if process is not None:
                _stop_process_tree(process, errors)
            if command[0] == "docker" and "--name" in command:
                # Killing a Docker client does not stop its server-side container.
                name = command[command.index("--name") + 1]
                subprocess.run(["docker", "rm", "--force", name], stdout=errors, stderr=errors,
                               timeout=15, check=False, shell=False)
            raise JobError(f"{stem}: se agotó el límite de {PROCESS_TIMEOUT} segundos") from exc
        except OSError as exc:
            raise JobError(f"{stem}: no se pudo iniciar el ejecutable requerido") from exc
    if returncode:
        raise JobError(f"{stem}: falló; consulta los logs privados del trabajo")
    if stdout_path.stat().st_size > MAX_RESULT_BYTES:
        raise JobError(f"{stem}: respuesta mayor al límite permitido")
    try:
        return stdout_path.read_text(encoding="utf-8-sig")
    except UnicodeError as exc:
        raise JobError(f"{stem}: respuesta con codificación no válida") from exc


def _stop_process_tree(process, errors):
    if os.name == "nt":
        system = Path(os.environ.get("SYSTEMROOT", "C:/Windows")) / "System32" / "taskkill.exe"
        try:
            subprocess.run([str(system), "/PID", str(process.pid), "/T", "/F"],
                           stdout=errors, stderr=errors, timeout=15, check=False, shell=False)
        except (OSError, subprocess.TimeoutExpired):
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=15)


def resolve_video(payload, runtime, container=False):
    try:
        if payload["failed"] != 0 or payload["succeeded"] != 1 or payload["total"] != 1:
            raise JobError("El motor no completó exactamente un video")
        tasks = payload["tasks"]
        if not isinstance(tasks, list) or len(tasks) != 1 or tasks[0]["status"] != "succeeded":
            raise JobError("El motor no devolvió una tarea terminada")
        videos = tasks[0]["result"]["videos"]
        if not isinstance(videos, list) or len(videos) != 1 or not isinstance(videos[0], str):
            raise JobError("El motor no devolvió exactamente un archivo")
        raw = videos[0]
        if container:
            if not raw.startswith("/runtime/"):
                raise JobError("El resultado del contenedor no pertenece al trabajo")
            raw = str(runtime / raw.removeprefix("/runtime/"))
        path = Path(raw).resolve()
        if not path.is_relative_to(runtime.resolve()) or path.suffix.lower() != ".mp4" or not path.is_file():
            raise JobError("El resultado no es un MP4 dentro del trabajo")
        if path.stat().st_size == 0:
            raise JobError("El motor devolvió un archivo vacío")
        return path
    except (KeyError, TypeError, IndexError) as exc:
        raise JobError("El motor devolvió un resultado incompleto") from exc


def engine_commit(engine=ENGINE):
    try:
        result = subprocess.run(["git", "-C", str(engine), "rev-parse", "HEAD"],
                                capture_output=True, text=True, timeout=10, check=True)
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def engine_dirty(engine=ENGINE):
    """None significa que Git no pudo establecer el estado, nunca limpio supuesto."""
    try:
        result = subprocess.run(["git", "-C", str(engine), "status", "--porcelain", "--untracked-files=normal"],
                                capture_output=True, text=True, timeout=10, check=True)
        return bool(result.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        return None


def inspect_container_image(runtime, env):
    """Resolve the operator's fixed local tag once; run only its immutable identity."""
    raw = run_logged(["docker", "image", "inspect", CONTAINER_IMAGE, "--format", "{{json .Id}}"],
                     runtime, "image-inspect", cwd=runtime, env=env)
    try:
        image_id = json.loads(raw)
    except ValueError as exc:
        raise JobError("Docker no devolvió una identidad de imagen válida") from exc
    if not isinstance(image_id, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", image_id) is None:
        raise JobError("Docker no devolvió un digest SHA-256 de imagen válido")
    return image_id


def build_command(runtime, batch, inputs, container=False, image_id=None):
    if container:
        if not isinstance(image_id, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", image_id) is None:
            raise JobError("El contenedor requiere una identidad de imagen verificada")
        return [
            "docker", "run", "--rm", "--network", "none", "--read-only",
            "--name", "videosia-" + runtime.parent.name,
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--memory", "2g", "--cpus", "2", "--pids-limit", "128",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=256m",
            "--mount", f"type=bind,source={inputs.resolve()},target=/inputs,readonly",
            "--mount", f"type=bind,source={runtime.resolve()},target=/runtime",
            "--env", "MPT_HOME=/runtime", "--env", "HF_HUB_OFFLINE=1",
            "--env", "HF_HUB_DISABLE_TELEMETRY=1", "--env", "DO_NOT_TRACK=1",
            "--env", "LITELLM_LOCAL_MODEL_COST_MAP=True",
            "--env", "STREAMLIT_BROWSER_GATHER_USAGE_STATS=false",
            "--env", "AUTO_PUBLISH=false", "--env", "MPT_CHECK_UPDATES=0",
            "--entrypoint", "python", image_id, "-I",
            "/opt/videosia-engine-entry.py", "/app/cli.py",
            "--batch-file", "/runtime/batch.json", "--stop-at", "video",
        ]
    interpreter = engine_python()
    if not interpreter.is_file() or not (ENGINE / "cli.py").is_file():
        raise JobError("Falta el entorno del motor; consulta la guía de instalación")
    return [str(interpreter), "-I", str(ENGINE_ENTRY), str(ENGINE / "cli.py"),
            "--batch-file", str(batch), "--stop-at", "video"]


def verify_media(video, runtime, env):
    ffmpeg = find_ffmpeg(env)
    if not ffmpeg:
        raise JobError("Falta FFmpeg para comprobar el video")
    # Never auto-probe attacker-controlled output: DASH/HLS can cause native
    # FFmpeg requests outside the Python socket guard or the Docker container.
    run_logged([str(ffmpeg), "-v", "error", "-xerror", "-protocol_whitelist", "file,pipe",
                "-f", "mov", "-i", str(video),
                "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"],
               runtime, "decode", cwd=runtime, env=env)
    result = {"decoded_video_and_audio": True, "duration_seconds": None, "width": None, "height": None}
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        raw = run_logged([ffprobe, "-v", "error", "-protocol_whitelist", "file,pipe", "-f", "mov",
                          "-show_streams", "-show_format", "-of", "json", "-i", str(video)],
                         runtime, "probe", cwd=runtime, env=env)
        try:
            probe = json.loads(raw)
            visual = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
            result.update(duration_seconds=float(probe["format"]["duration"]),
                          width=visual["width"], height=visual["height"])
        except (ValueError, KeyError, TypeError, StopIteration) as exc:
            raise JobError("ffprobe no devolvió metadatos válidos") from exc
    return result


def render(job_path, *, root=ROOT, container=False):
    inputs = root / "inputs"
    if not inputs.resolve().is_relative_to(root.resolve()):
        raise JobError("El directorio inputs no puede salir del proyecto")
    job = load_job(job_path, inputs)
    job_id = str(uuid.uuid4())
    jobs = root / "data" / "jobs"
    if not jobs.resolve().is_relative_to(root.resolve()):
        raise JobError("El directorio de trabajos no puede salir del proyecto")
    jobs.mkdir(parents=True, exist_ok=True)
    job_dir = jobs / job_id
    runtime = job_dir / "runtime"
    job_dir.mkdir(mode=0o700)
    runtime.mkdir(mode=0o700)
    env = child_environment(runtime)
    checkout_commit = engine_commit()
    checkout_dirty = engine_dirty()
    manifest = {
        "schema_version": 1, "job_id": job_id, "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "running", "engine": {
            "name": "MoneyPrinterTurbo", "commit": None if container else checkout_commit,
            "dirty": None if container else checkout_dirty,
            "checkout_commit": checkout_commit, "checkout_dirty": checkout_dirty,
            "image_id": None, "source_revision": None if container else checkout_commit,
        },
        "execution": {"mode": "container" if container else "local",
                      "network_isolation": "docker-network-none" if container else "not_enforced",
                      "python_socket_audit_guard": True,
                      "python_guard_is_malware_sandbox": False,
                      "telemetry_opt_out": True, "litellm_cost_map": "local"},
        "inputs": [{"path": p.relative_to(inputs.resolve()).as_posix(), "sha256": sha256(p)}
                   for p in [job["audio"], *job["materials"]]],
        "script_sha256": hashlib.sha256(job["script"].encode()).hexdigest(),
        "audio_duration_seconds": job["audio_duration_seconds"],
        "ai_disclosure": job["ai_disclosure"], "rights": {"note": job["rights_note"], "reviewed": False},
        "costs": {"cloud_requests_enabled": False, "cloud_cost": 0, "currency": "MXN"},
        "editorial_review": "pending", "human_approval": None,
        "publication_allowed": False, "AUTO_PUBLISH": False,
        "subtitles": {"present": False, "timings_measured": False}, "qa": {"passed": False},
    }
    started = time.monotonic()
    try:
        if not find_ffmpeg(env):
            raise JobError("Se requiere FFmpeg en el host para QA antes de iniciar el motor, incluso con --container")
        write_config(runtime)
        batch = runtime / "batch.json"
        batch.write_text(json.dumps([build_params(job, inputs, container)], ensure_ascii=False), encoding="utf-8")
        image_id = inspect_container_image(runtime, env) if container else None
        manifest["engine"]["image_id"] = image_id
        command = build_command(runtime, batch, inputs, container, image_id=image_id)
        raw = run_logged(command, runtime, "engine", cwd=ENGINE, env=env)
        try:
            payload = json.loads(raw)
        except ValueError as exc:
            raise JobError("El motor no devolvió JSON válido") from exc
        video = resolve_video(payload, runtime, container)
        qa = verify_media(video, runtime, env)
        manifest.update(status="succeeded", output={"path": str(video), "sha256": sha256(video)},
                        qa={"passed": True, **qa})
    except (JobError, OSError) as exc:
        manifest.update(status="failed", error=str(exc))
    except Exception:
        # Unexpected adapter defects still leave a terminal manifest and local evidence.
        (runtime / "wrapper.stderr").write_text(traceback.format_exc(), encoding="utf-8")
        manifest.update(status="failed", error="Error interno; consulta wrapper.stderr del trabajo")
    finally:
        manifest["elapsed_seconds"] = round(time.monotonic() - started, 3)
        (job_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return job_dir / "manifest.json", manifest


def doctor():
    return {
        "engine_checkout": (ENGINE / "cli.py").is_file(), "engine_commit": engine_commit(), "engine_dirty": engine_dirty(),
        "engine_python": str(engine_python()), "engine_environment_exists": engine_python().is_file(),
        "ffmpeg": find_ffmpeg(),
        "ffprobe": shutil.which("ffprobe"), "docker": shutil.which("docker"),
        "AUTO_PUBLISH": False,
        "privacy": "El modo local bloquea sockets Python con un audit hook; no es un sandbox ni un límite de red del SO. --container usa Docker --network none.",
    }
