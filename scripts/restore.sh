#!/usr/bin/env sh
set -eu

: "${RESTORE_ARCHIVE:?RESTORE_ARCHIVE is required}"
: "${RESTORE_CHECKSUM:?RESTORE_CHECKSUM is required}"
: "${RESTORE_AGE_IDENTITY_FILE:?RESTORE_AGE_IDENTITY_FILE is required}"
: "${RESTORE_DATABASE_URL:?RESTORE_DATABASE_URL must target an isolated database}"

actual="$(sha256sum "$RESTORE_ARCHIVE" | cut -d ' ' -f 1)"
[ "$actual" = "$RESTORE_CHECKSUM" ] || { echo "restore_checksum_failed" >&2; exit 2; }
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT INT TERM
age --decrypt --identity "$RESTORE_AGE_IDENTITY_FILE" --output "$work_dir/backup.tar.gz" "$RESTORE_ARCHIVE"
tar -xzf "$work_dir/backup.tar.gz" -C "$work_dir"
psql "$RESTORE_DATABASE_URL" --file="$work_dir/globals.sql"
pg_restore --dbname="$RESTORE_DATABASE_URL" --clean --if-exists "$work_dir/database.dump"
revision="$(psql "$RESTORE_DATABASE_URL" -Atc 'select version_num from alembic_version')"
[ -n "$revision" ] || { echo "restore_missing_migration_revision" >&2; exit 2; }
psql "$RESTORE_DATABASE_URL" -v ON_ERROR_STOP=1 -c "update u02_identity.sessions set revoked_at = now(), revoke_reason = 'restore_safety' where revoked_at is null"
${RESTORE_SMOKE_COMMAND:-true}
printf 'restore_verified checksum=%s revision=%s identity_exports_restored=false\n' "$actual" "$revision"
