#!/usr/bin/env bash
# 备份 PostgreSQL 数据库（读取项目根目录 .env 中的 POSTGRES_* 变量）
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "${DEPLOY_DIR}/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"
BACKUP_DIR="${BACKUP_DIR:-${PROJECT_ROOT}/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "错误: 未找到 ${ENV_FILE}" >&2
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "${ENV_FILE}"
set +a

: "${POSTGRES_USER:?请在 .env 中设置 POSTGRES_USER}"
: "${POSTGRES_DB:?请在 .env 中设置 POSTGRES_DB}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

mkdir -p "${BACKUP_DIR}"
OUTPUT="${BACKUP_DIR}/${POSTGRES_DB}_${TIMESTAMP}.sql.gz"

echo "备份 ${POSTGRES_DB} @ ${POSTGRES_HOST}:${POSTGRES_PORT} -> ${OUTPUT}"

export PGPASSWORD="${POSTGRES_PASSWORD}"
pg_dump \
  -h "${POSTGRES_HOST}" \
  -p "${POSTGRES_PORT}" \
  -U "${POSTGRES_USER}" \
  -d "${POSTGRES_DB}" \
  --no-owner \
  --no-privileges \
  | gzip > "${OUTPUT}"
unset PGPASSWORD

echo "完成: ${OUTPUT}"
