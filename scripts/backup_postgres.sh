#!/bin/bash
# ==============================================================================
# LingCast & AI Short Drama - PostgreSQL Automated Backup Script
# Retention Policy: 7 days rotation
# Checksum: SHA-256 for integrity verification
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/workspace/data/backups/postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP="$(date +'%Y%m%d_%H%M%S')"
BACKUP_FILENAME="pg_backup_${TIMESTAMP}.sql.gz"
TARGET_FILE="${BACKUP_DIR}/${BACKUP_FILENAME}"

POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-shortdrama}"
POSTGRES_DB="${POSTGRES_DB:-shortdrama_db}"
export PGPASSWORD="${POSTGRES_PASSWORD:-shortdrama_secret_2026}"

mkdir -p "${BACKUP_DIR}"

echo "[$(date +'%Y-%m-%d %H:%M:%S')] Starting PostgreSQL backup for database '${POSTGRES_DB}'..."

# Dump and compress
if command -v docker >/dev/null 2>&1 && [ "${USE_DOCKER_EXEC:-true}" = "true" ]; then
    echo "Executing pg_dump via docker container 'short_drama_postgres'..."
    docker exec short_drama_postgres pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --clean --if-exists | gzip > "${TARGET_FILE}"
else
    pg_dump -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --clean --if-exists | gzip > "${TARGET_FILE}"
fi

# Calculate SHA256 checksum
if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${TARGET_FILE}" > "${TARGET_FILE}.sha256"
elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${TARGET_FILE}" > "${TARGET_FILE}.sha256"
fi

BACKUP_SIZE="$(ls -lh "${TARGET_FILE}" | awk '{print $5}')"
echo "[$(date +'%Y-%m-%d %H:%M:%S')] Backup created successfully: ${TARGET_FILE} (${BACKUP_SIZE})"

# Enforce retention policy (cleanup older than RETENTION_DAYS)
echo "Enforcing ${RETENTION_DAYS}-day retention policy..."
find "${BACKUP_DIR}" -name "pg_backup_*.sql.gz*" -mtime "+${RETENTION_DAYS}" -type f -exec rm -f {} +

echo "[$(date +'%Y-%m-%d %H:%M:%S')] Backup rotation complete."
