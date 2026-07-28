#!/usr/bin/env sh
set -eu

: "${PREVIOUS_API_IMAGE:?PREVIOUS_API_IMAGE must be an immutable digest reference}"
case "$PREVIOUS_API_IMAGE" in *@sha256:*) ;; *) echo "PREVIOUS_API_IMAGE must contain @sha256" >&2; exit 2;; esac
export API_IMAGE="$PREVIOUS_API_IMAGE"
docker compose -f compose.yaml -f compose.remote.yaml up -d --no-deps api worker
curl --fail --retry 10 --retry-delay 3 "https://$APP_DOMAIN/api/v1/health/ready"
python3 scripts/synthetic.py "https://$APP_DOMAIN"

