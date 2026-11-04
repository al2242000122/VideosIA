$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
git submodule update --init --recursive
if ($LASTEXITCODE -ne 0) { throw 'No se pudo obtener el motor fijado' }
python -c "import sys; assert sys.version_info >= (3,11), 'Se requiere Python 3.11+'"
if ($LASTEXITCODE -ne 0) { throw 'Python no disponible o incompatible' }
python scripts/audit_dependencies.py
if ($LASTEXITCODE -ne 0) { throw 'Auditoría no aprobada; no se instalarán dependencias' }
python -m venv .venv-tools
if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno de herramientas' }
& .\.venv-tools\Scripts\python.exe -m pip install --disable-pip-version-check --only-binary=:all: --index-url https://pypi.org/simple uv==0.13.7
if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar uv desde PyPI oficial' }
$uv = Join-Path (Get-Location) '.venv-tools\Scripts\uv.exe'
$pythonPath = (python -c "import sys; print(sys.executable)").Trim()
Push-Location engines/MoneyPrinterTurbo
try {
    & $uv sync --frozen --no-build --no-install-project --no-managed-python --python $pythonPath --default-index https://pypi.org/simple
    if ($LASTEXITCODE -ne 0) { throw 'La instalación del lock fijado no se completó' }
} finally { Pop-Location }
python -m videosia doctor
