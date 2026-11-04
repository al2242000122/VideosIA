"""Contrato de entrada cerrado; ningún campo elige servicios o ejecutables."""

import hashlib
import json
import wave
from pathlib import PurePosixPath, PureWindowsPath

MAX_JSON_BYTES = 64 * 1024
MAX_ASSET_BYTES = 50 * 1024 * 1024
MAX_AUDIO_SECONDS = 300
FIELDS = {"title", "script", "audio", "materials", "ai_disclosure", "rights_note"}


class JobError(ValueError):
    """Entrada o resultado que no satisface el contrato local."""


def _text(value, name, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise JobError(f"{name}: se requiere texto de 1 a {maximum} caracteres")
    if "\x00" in value:
        raise JobError(f"{name}: contiene un carácter no permitido")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise JobError(f"{name}: contiene Unicode no válido") from exc
    return value.strip()


def resolve_asset(name, inputs, extensions):
    """Sólo archivos regulares dentro de inputs, incluso al resolver enlaces."""
    if not isinstance(name, str) or not name or "\\" in name or ":" in name or "\x00" in name:
        raise JobError("La ruta debe ser relativa a inputs y usar / como separador")
    try:
        name.encode("utf-8")
    except UnicodeError as exc:
        raise JobError("La ruta contiene Unicode no válido") from exc
    relative = PurePosixPath(name)
    if relative.is_absolute() or PureWindowsPath(name).is_absolute() or ".." in relative.parts:
        raise JobError("La ruta no puede salir de inputs")
    root = inputs.resolve()
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise JobError("El recurso no existe dentro de inputs")
    if candidate.suffix.lower() not in extensions:
        raise JobError("El recurso tiene un formato no admitido")
    if not 0 < candidate.stat().st_size <= MAX_ASSET_BYTES:
        raise JobError("El recurso debe ocupar entre 1 byte y 50 MiB")
    return candidate


def load_job(path, inputs):
    if path.stat().st_size > MAX_JSON_BYTES:
        raise JobError("El trabajo excede el límite de 64 KiB")
    try:
        job = json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, UnicodeError) as exc:
        raise JobError("El trabajo debe ser JSON UTF-8 válido") from exc
    if not isinstance(job, dict) or set(job) != FIELDS:
        raise JobError("El trabajo debe contener únicamente los campos del contrato")
    title = _text(job["title"], "title", 160)
    script = _text(job["script"], "script", 10000)
    rights = _text(job["rights_note"], "rights_note", 2000)
    disclosure = job["ai_disclosure"]
    if not isinstance(disclosure, dict) or set(disclosure) != {"decision", "reason"}:
        raise JobError("ai_disclosure requiere decision y reason")
    if not isinstance(disclosure["decision"], str) or disclosure["decision"] not in {"required", "not_required", "needs_review"}:
        raise JobError("Decisión de divulgación no válida")
    reason = _text(disclosure["reason"], "ai_disclosure.reason", 2000)
    materials = job["materials"]
    if not isinstance(materials, list) or not 1 <= len(materials) <= 20:
        raise JobError("materials debe contener entre 1 y 20 archivos")
    audio = resolve_asset(job["audio"], inputs, {".wav"})
    images = [resolve_asset(item, inputs, {".png", ".jpg", ".jpeg"}) for item in materials]
    for image in images:
        with image.open("rb") as source:
            header = source.read(8)
        valid_signature = header == b"\x89PNG\r\n\x1a\n" if image.suffix.lower() == ".png" else header.startswith(b"\xff\xd8\xff")
        if not valid_signature:
            raise JobError("El recurso no contiene la firma PNG o JPEG correspondiente a su extensión")
    try:
        with wave.open(str(audio), "rb") as source:
            if source.getcomptype() != "NONE" or source.getnchannels() not in (1, 2):
                raise JobError("La narración debe ser WAV PCM mono o estéreo")
            duration = source.getnframes() / source.getframerate()
            if not 0 < duration <= MAX_AUDIO_SECONDS:
                raise JobError("La narración debe durar entre 0 y 300 segundos")
    except (wave.Error, EOFError, ZeroDivisionError) as exc:
        raise JobError("La narración no es un WAV PCM válido") from exc
    return {
        "title": title, "script": script, "audio": audio, "materials": images,
        "audio_duration_seconds": duration,
        "ai_disclosure": {"decision": disclosure["decision"], "reason": reason},
        "rights_note": rights,
    }


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_params(job, inputs, container=False):
    def asset_path(path):
        return "/inputs/" + path.relative_to(inputs.resolve()).as_posix() if container else str(path)
    return {
        "video_subject": job["title"], "video_script": job["script"],
        "video_language": "es-MX", "video_source": "local",
        "video_materials": [{"provider": "local", "url": asset_path(p)} for p in job["materials"]],
        "custom_audio_file": asset_path(job["audio"]), "voice_name": "no-voice",
        "subtitle_enabled": False, "bgm_type": "", "bgm_volume": 0,
        "video_count": 1, "video_aspect": "9:16", "video_concat_mode": "sequential",
        "video_fit_mode": "contain", "image_motion": "static", "n_threads": 2,
        "video_clip_duration": max(1, round(job["audio_duration_seconds"] / len(job["materials"]))),
    }
