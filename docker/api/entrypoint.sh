#!/bin/bash
# SentinelClaw API — Container-Entrypoint
# Kopiert OpenShell-Config und passt Gateway-Endpoint für Docker an

set -euo pipefail

OPENSHELL_SRC="/openshell-config"
OPENSHELL_DST="${HOME}/.config/openshell"

# OpenShell-Konfiguration vom Read-Only-Mount kopieren und anpassen
if [ -d "${OPENSHELL_SRC}" ]; then
    mkdir -p "${OPENSHELL_DST}"
    cp -r "${OPENSHELL_SRC}/." "${OPENSHELL_DST}/"

    # Gateway-Endpoint für Docker-Netzwerk umschreiben
    if [ -n "${OPENSHELL_GATEWAY_ENDPOINT:-}" ]; then
        find "${OPENSHELL_DST}" -name "metadata.json" -exec \
            sed -i "s|https://127.0.0.1:[0-9]*|${OPENSHELL_GATEWAY_ENDPOINT}|g" {} +
        echo "[entrypoint] OpenShell Gateway: ${OPENSHELL_GATEWAY_ENDPOINT}"
    fi
else
    echo "[entrypoint] Keine OpenShell-Konfiguration gefunden (${OPENSHELL_SRC})"
fi

# Weitergabe an CMD (uvicorn)
exec "$@"
