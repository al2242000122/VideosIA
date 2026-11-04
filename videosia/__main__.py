"""Interfaz CLI sin dependencias de terceros ni arranque implícito del motor."""

import argparse
import json
from pathlib import Path

from .job import JobError
from .runner import doctor, render


def main(argv=None):
    parser = argparse.ArgumentParser(description="VideosIA: generación local con revisión antes de publicar")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Comprobar herramientas sin ejecutar el motor")
    render_parser = commands.add_parser("render", help="Procesar un trabajo JSON con medios de inputs/")
    render_parser.add_argument("job", type=Path)
    render_parser.add_argument("--container", action="store_true", help="Aislar con Docker y red deshabilitada")
    args = parser.parse_args(argv)
    if args.command == "doctor":
        print(json.dumps(doctor(), indent=2, ensure_ascii=False))
        return 0
    try:
        path, manifest = render(args.job, container=args.container)
    except (JobError, OSError) as exc:
        print(json.dumps({"status": "rejected", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": manifest["status"], "manifest": str(path),
                      "error": manifest.get("error")}, ensure_ascii=False))
    return 0 if manifest["status"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
