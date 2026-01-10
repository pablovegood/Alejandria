#!/usr/bin/env bash
set -euo pipefail

APP="alejandria-pablo"     # cámbialo
REGION="fra"
VOLUME="alejandria_texts"

flyctl auth login
flyctl apps create "$APP" || true

# Volumen de 1GB en Europa
flyctl volumes create "$VOLUME" --app "$APP" --region "$REGION" --size 1

# (Opcional) Secrets de observabilidad (Grafana Cloud OTLP)
# flyctl secrets set --app "$APP" OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp-gateway-prod-eu-west-0.grafana.net/otlp"
