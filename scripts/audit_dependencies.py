"""Check public PyPI versions in the engine lock against OSV; execute no packages."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import sys
import tomllib
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def audit(lock: Path) -> dict:
    data = tomllib.loads(lock.read_text(encoding="utf-8"))
    packages = [item for item in data["package"] if "registry" in item.get("source", {})]
    if not packages:
        raise ValueError("El lock no contiene paquetes de registro para auditar")
    payload = {"queries": [
        {"package": {"name": p["name"], "ecosystem": "PyPI"}, "version": p["version"]}
        for p in packages
    ]}
    request = urllib.request.Request(
        "https://api.osv.dev/v1/querybatch", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "VideosIA-dependency-audit"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        results = json.load(response)["results"]
    if len(results) != len(packages):
        raise ValueError("Respuesta OSV incompleta; no se puede afirmar auditoría limpia")
    return {
        "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
        "packages_checked": len(packages),
        "packages": [{"name": p["name"], "version": p["version"]} for p in packages],
        "source": "https://api.osv.dev/v1/querybatch",
        "scope": "Known advisories in lockfile; not malware certification or installed-environment audit",
        "findings": [
            {"package": p["name"], "version": p["version"], "vulns": result["vulns"]}
            for p, result in zip(packages, results) if result.get("vulns")
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=ROOT / "engines/MoneyPrinterTurbo/uv.lock")
    parser.add_argument("--output", type=Path, default=ROOT / "data/audit/osv.json")
    args = parser.parse_args()
    try:
        report = audit(args.lock)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"packages_checked": report["packages_checked"],
                          "affected_packages": len(report["findings"]), "report": str(args.output)}))
        return int(bool(report["findings"]))
    except (OSError, ValueError, KeyError) as error:
        print(f"Auditoría no completada: {type(error).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
