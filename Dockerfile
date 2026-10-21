# syntax=docker/dockerfile:1.7
# SportPredict API image: wheel built in a separate stage, slim non-root runtime,
# dataset pinned to a commit and verified by SHA-256 at build time (reproducibility).

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder
WORKDIR /src
RUN pip install --no-cache-dir build==1.2.2
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m build --wheel --outdir /dist

FROM python:${PYTHON_VERSION}-slim AS runtime
ARG VERSION=dev
ARG REVISION=unknown
LABEL org.opencontainers.image.title="sportpredict-api" \
      org.opencontainers.image.description="Elo ratings and football outcome probabilities over REST" \
      org.opencontainers.image.source="https://github.com/Safyd-Zey/sportpredict-core" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SPORTPREDICT_DATA=/app/data/results.csv

RUN useradd --create-home --uid 10001 app && mkdir -p /app/data
WORKDIR /app

COPY --from=builder /dist/*.whl /tmp/
RUN pip install "$(ls /tmp/*.whl)[api]" && rm /tmp/*.whl

ADD --chmod=444 \
    --checksum=sha256:b38434f8f74cd9faacb269eb1c97760fc2dfac43fcb211779e0bd2cbb48f89e3 \
    https://raw.githubusercontent.com/martj42/international_results/b7a3a8ee5d37780c6a03101c188658fd439e241d/results.csv \
    /app/data/results.csv

USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["uvicorn", "sportpredict.api:app", "--host", "0.0.0.0", "--port", "8000"]
