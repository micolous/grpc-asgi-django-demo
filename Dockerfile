# Base Python image version for running Python things without uv
ARG PYTHON_VERSION=3.12-slim-bookworm
# Base ghcr.io/astral-sh/uv image for building Python things
ARG UV_VERSION=0.5-python3.12-bookworm-slim
ARG GRPC_HEALTH_PROBE_VERSION=v0.4.37
ARG ENVOY_VERSION=v1.32-latest
ARG DOCKER_MIRROR=docker.io

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS builder-grpc-asgi-server
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# grpc-asgi-django-demo-proto
COPY \
  proto/hatch_build.py \
  proto/pyproject.toml \
  proto/uv.lock \
  /app/proto/
COPY proto/proto/ /app/proto/proto/

# grpc-asgi-django-demo-server metadata
COPY \
  server/.python-version \
  server/pyproject.toml \
  server/uv.lock \
  /app/server/

# Install server dependencies
WORKDIR /app/server
RUN \
  --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-install-project --no-dev --no-editable \
    --refresh-package grpc_asgi_django_demo_proto

# grpc-asgi-django-demo-server code
COPY server .
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev --no-editable

# grpc-health-probe
FROM ghcr.io/grpc-ecosystem/grpc-health-probe:${GRPC_HEALTH_PROBE_VERSION} AS grpc-health-probe

# Final server image without uv
FROM ${DOCKER_MIRROR}/python:${PYTHON_VERSION} AS grpc-asgi-server

COPY --from=grpc-health-probe \
  /ko-app/grpc-health-probe /app/server/.venv/bin/

COPY --from=builder-grpc-asgi-server --chown=app:app \
  /app/server/.venv \
  /app/server/.venv

COPY --from=builder-grpc-asgi-server --chown=app:app \
    /app/server/entrypoint.sh \
    /app/server/health_check.sh \
    /app/server/

# Place executables in the environment at the front of the path
ENV PATH="/app/server/.venv/bin:$PATH" BIND_ADDR="0.0.0.0:8081"

WORKDIR /app/server
RUN grpc-asgi-django-demo-server --help
EXPOSE 8081/tcp

HEALTHCHECK \
  --start-period=10s \
  --start-interval=1s \
  --interval=30s \
  --timeout=10s \
  --retries=3 \
  CMD /app/server/health_check.sh

CMD ["/app/server/entrypoint.sh"]

# Envoy image with config and descriptors
FROM ${DOCKER_MIRROR}/envoyproxy/envoy:${ENVOY_VERSION} AS grpc-asgi-envoy
COPY --link --chown=0:0 --chmod=644 \
  envoy/envoy.yaml \
  envoy/x_http_code_as_status.lua \
  /etc/envoy/

COPY --from=grpc-asgi-server --link --chown=0:0 --chmod=644 \
  /app/server/.venv/lib/python3.12/site-packages/grpc_asgi_django_demo/proto/v1/service.binpb \
  /etc/envoy/
