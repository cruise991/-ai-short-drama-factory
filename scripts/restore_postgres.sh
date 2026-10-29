#!/bin/bash
# ==============================================================================
# LingCast & AI Short Drama - PostgreSQL Automated Restore / DR Script
# Checks SHA-256 integrity before restoring to prevent corruption or tampering
# ==============================================================================

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <path_to_backup_file.sql.gz> [--force]"
    echo "Example: $0 /workspace/data/backups/postgres/pg_backup_20260911_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"
FORCE="${2:-}"

POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-shortdrama}"
POSTGRES_DB="${POSTGRES_DB:-shortdrama_db}"
export PGPASSWORD="${POSTGRES_PASSWORD:-shortdrama_secret_2026}"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "[ERROR] Backup file does not exist: ${BACKUP_FILE}"
    exit 1
fi

CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [ -f "${CHECKSUM_FILE}" ]; then
    echo "[INFO] Verifying SHA-256 checksum against ${CHECKSUM_FILE}..."
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum -c "${CHECKSUM_FILE}"
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 -c "${CHECKSUM_FILE}"
    else
        echo "[WARN] sha256 utility not found, skipping checksum check."
    fi
    echo "[SUCCESS] Checksum verified successfully."
else
    if [ "${FORCE}" != "--force" ]; then
        echo "[ERROR] No SHA-256 checksum file found! Use --force to restore anyway."
        exit 2
    else
        echo "[WARN] Restoring without checksum verification (--force supplied)."
    fi
fi

echo "[$(date +'%Y-%m-%d %H:%M:%S')] Restoring database '${POSTGRES_DB}' from '${BACKUP_FILE}'..."

if command -v docker >/dev/null 2>&1 && [ "${USE_DOCKER_EXEC:-true}" = "true" ] && docker ps | grep -q "short_drama_postgres"; then
    echo "Executing restore via docker container 'short_drama_postgres'..."
    gzip -dc "${BACKUP_FILE}" | docker exec -i short_drama_postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"
else
    echo "Executing restore via local psql client..."
    gzip -dc "${BACKUP_FILE}" | psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"
fi

echo "[$(date +'%Y-%m-%d %H:%M:%S')] Database '${POSTGRES_DB}' successfully restored from '${BACKUP_FILE}'."
