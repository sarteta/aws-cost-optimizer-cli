FROM python:3.13-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

COPY requirements.txt ./
RUN pip install --prefix=/install -r requirements.txt


FROM python:3.13-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/sarteta/aws-cost-optimizer-cli"
LABEL org.opencontainers.image.description="Python CLI that scans an AWS account and lists obvious cost leaks"
LABEL org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN groupadd --system --gid 10001 app \
 && useradd  --system --uid 10001 --gid app --create-home app

COPY --from=builder /install /usr/local

WORKDIR /app
COPY --chown=app:app src ./src

USER app

# Mock run (no AWS creds needed):
#   docker run --rm ghcr.io/sarteta/aws-cost-optimizer-cli --mock --output /tmp/report
# Real run (mount creds):
#   docker run --rm -v $HOME/.aws:/home/app/.aws:ro ghcr.io/sarteta/aws-cost-optimizer-cli \
#     --profile default --region us-east-1
ENTRYPOINT ["python", "-m", "src.scan"]
