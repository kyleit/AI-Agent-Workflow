# msgbus-ws relay server — stdlib only, no pip install needed.
# Build from the repo root:
#   docker build -t registry.example.invalid/example/message-bus:1.0.0 .
FROM python:3.12-slim

# Run as non-root; store lives on a mounted volume so data survives restarts.
RUN useradd --create-home --uid 10001 msgbus && mkdir -p /data && chown msgbus:msgbus /data

WORKDIR /app
COPY scripts/ /app/
RUN chown -R msgbus:msgbus /app

USER msgbus

ENV MSGBUS_BIND=0.0.0.0 \
    MSGBUS_PORT=8787 \
    MSGBUS_STORE=/data
# MSGBUS_TOKEN is injected at runtime (k8s Secret) — do NOT bake it into the image.

EXPOSE 8787
VOLUME ["/data"]

# Liveness/readiness hit /health (no token required).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,os,sys; sys.exit(0 if urllib.request.urlopen(f\"http://127.0.0.1:{os.environ.get('MSGBUS_PORT','8787')}/health\",timeout=2).status==200 else 1)"

ENTRYPOINT ["python", "/app/msgbus_server.py"]
