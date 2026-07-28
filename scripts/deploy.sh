#!/usr/bin/env sh
set -eu

: "${API_IMAGE:?API_IMAGE must be an immutable digest reference}"
: "${APP_DOMAIN:?APP_DOMAIN is required}"
case "$API_IMAGE" in *@sha256:*) ;; *) echo "API_IMAGE must contain @sha256" >&2; exit 2;; esac

for secret in api_secret identity_kek identity_blind_index_key identity_session_pepper identity_export_key google_client_secret email_password postgres_password; do
  [ -s "secrets/$secret.txt" ] || { echo "missing required secret file: secrets/$secret.txt" >&2; exit 2; }
done

./scripts/backup.sh
docker compose -f compose.yaml -f compose.remote.yaml pull
docker compose -f compose.yaml -f compose.remote.yaml run --rm api alembic upgrade head
docker compose -f compose.yaml -f compose.remote.yaml up -d --remove-orphans
curl --fail --retry 10 --retry-delay 3 "https://$APP_DOMAIN/api/v1/health/ready"
python3 scripts/synthetic.py "https://$APP_DOMAIN"
