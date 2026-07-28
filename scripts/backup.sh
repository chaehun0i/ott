#!/usr/bin/env sh
set -eu

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_REMOTE:?BACKUP_REMOTE is required, for example s3:bucket/prefix}"
BACKUP_AGE_RECIPIENT_FILE="${BACKUP_AGE_RECIPIENT_FILE:-}"
BACKUP_AGE_RECIPIENT="${BACKUP_AGE_RECIPIENT:-}"
[ -n "$BACKUP_AGE_RECIPIENT_FILE" ] || [ -n "$BACKUP_AGE_RECIPIENT" ] || { echo "backup age recipient is required" >&2; exit 2; }

work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT INT TERM
created_at="$(date -u +%Y%m%dT%H%M%SZ)"
archive="$work_dir/ott-feed-$created_at.tar.gz"
encrypted="$archive.age"

pg_dumpall --dbname="$DATABASE_URL" --globals-only > "$work_dir/globals.sql"
pg_dump --dbname="$DATABASE_URL" --format=custom --file="$work_dir/database.dump"
tar -czf "$archive" -C "$work_dir" globals.sql database.dump
if [ -n "$BACKUP_AGE_RECIPIENT_FILE" ]; then
  age --recipient-file "$BACKUP_AGE_RECIPIENT_FILE" --output "$encrypted" "$archive"
else
  age --recipient "$BACKUP_AGE_RECIPIENT" --output "$encrypted" "$archive"
fi
checksum="$(sha256sum "$encrypted" | cut -d ' ' -f 1)"

revision="$(psql "$DATABASE_URL" -Atc 'select version_num from alembic_version')"
printf '{"createdAt":"%s","checksum":"%s","encrypted":true,"retentionDays":30,"migrationRevision":"%s","identityExportsExcluded":true}\n' "$created_at" "$checksum" "$revision" > "$work_dir/manifest.json"
rclone copyto "$encrypted" "$BACKUP_REMOTE/$(basename "$encrypted")"
rclone copyto "$work_dir/manifest.json" "$BACKUP_REMOTE/ott-feed-$created_at.manifest.json"
printf 'backup_success created_at=%s checksum=%s\n' "$created_at" "$checksum"
