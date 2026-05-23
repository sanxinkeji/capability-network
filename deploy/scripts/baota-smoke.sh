#!/usr/bin/env bash
# 宝塔生产冒烟：/health + /health/ready + 注册 + 登录
# 用法：
#   API_BASE=https://api.example.com/api/v1 ./deploy/scripts/baota-smoke.sh
#   HEALTH_URL=https://api.example.com/health READY_URL=https://api.example.com/health/ready API_BASE=... ./deploy/scripts/baota-smoke.sh
set -euo pipefail

HEALTH_URL="${HEALTH_URL:-${API_BASE%/api/v1}/health}"
READY_URL="${READY_URL:-${HEALTH_URL%/health}/health/ready}"
API_BASE="${API_BASE:-https://api.example.com/api/v1}"
SMOKE_EMAIL="${SMOKE_EMAIL:-smoke_$(date +%Y%m%d%H%M%S)@example.com}"
SMOKE_PASSWORD="${SMOKE_PASSWORD:-password123}"
SMOKE_NAME="${SMOKE_NAME:-Baota Smoke}"

echo "==> Health: ${HEALTH_URL}"
health_body="$(curl -sS "${HEALTH_URL}")"
health_code="$(curl -sS -o /dev/null -w "%{http_code}" "${HEALTH_URL}")"
echo "HTTP ${health_code}"
echo "${health_body}"
if [[ "${health_code}" != "200" ]]; then
  echo "错误: /health 非 200" >&2
  exit 1
fi
if ! grep -q '"status":"ok"' <<<"${health_body}" && ! grep -q '"status": "ok"' <<<"${health_body}"; then
  echo "错误: /health 响应不含 status ok" >&2
  exit 1
fi

echo ""
echo "==> Ready: ${READY_URL}"
ready_body="$(curl -sS "${READY_URL}")"
ready_code="$(curl -sS -o /dev/null -w "%{http_code}" "${READY_URL}")"
echo "HTTP ${ready_code}"
echo "${ready_body}"
if [[ "${ready_code}" != "200" ]]; then
  echo "错误: /health/ready 非 200" >&2
  exit 1
fi
if ! grep -q '"status":"ok"' <<<"${ready_body}" && ! grep -q '"status": "ok"' <<<"${ready_body}"; then
  echo "错误: /health/ready 响应不含 status ok" >&2
  exit 1
fi

echo ""
echo "==> Register: ${API_BASE}/auth/register"
register_resp="$(curl -sS -X POST "${API_BASE}/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${SMOKE_EMAIL}\",\"password\":\"${SMOKE_PASSWORD}\",\"display_name\":\"${SMOKE_NAME}\"}")"
echo "${register_resp}"
if ! grep -q '"code":0' <<<"${register_resp}" && ! grep -q '"code": 0' <<<"${register_resp}"; then
  echo "错误: 注册失败" >&2
  exit 1
fi

echo ""
echo "==> Login: ${API_BASE}/auth/login"
login_resp="$(curl -sS -X POST "${API_BASE}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"account\":\"${SMOKE_EMAIL}\",\"password\":\"${SMOKE_PASSWORD}\"}")"
echo "${login_resp}"
if ! grep -q '"access_token"' <<<"${login_resp}"; then
  echo "错误: 登录未返回 access_token" >&2
  exit 1
fi

echo ""
echo "==> PASSED (health + ready + register + login)"
