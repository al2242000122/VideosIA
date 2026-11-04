# Build with: docker build -f infra/Dockerfile -t videosia-mpt:local .
# Network is needed during build; run via VideosIA --container for network none.
FROM ghcr.io/astral-sh/uv:0.13.7 AS uv
FROM python:3.11-slim-trixie
COPY --from=uv /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY engines/MoneyPrinterTurbo/pyproject.toml engines/MoneyPrinterTurbo/uv.lock ./
RUN uv sync --frozen --no-dev --no-build --no-install-project
COPY engines/MoneyPrinterTurbo/app ./app
COPY engines/MoneyPrinterTurbo/cli.py engines/MoneyPrinterTurbo/config.example.toml ./
COPY videosia/engine_entry.py /opt/videosia-engine-entry.py
# Intentionally exclude upstream fonts/music; local entry point disables both.
ENV PATH="/app/.venv/bin:$PATH" PYTHONUTF8=1 PYTHONNOUSERSITE=1 \
    MPT_HOME=/runtime HOME=/tmp HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false MPT_CHECK_UPDATES=0 AUTO_PUBLISH=false \
    LITELLM_LOCAL_MODEL_COST_MAP=True DO_NOT_TRACK=1 HF_HUB_DISABLE_TELEMETRY=1
CMD ["python", "/app/cli.py", "--help"]
