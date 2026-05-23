#!/usr/bin/env bash
# 重启 Supervisor 管理的 uvicorn 后端进程
set -euo pipefail

SUPERVISOR_PROGRAM="${SUPERVISOR_PROGRAM:-capability-network-backend}"

if command -v supervisorctl >/dev/null 2>&1; then
  echo "重启 Supervisor 程序: ${SUPERVISOR_PROGRAM}"
  supervisorctl restart "${SUPERVISOR_PROGRAM}"
  supervisorctl status "${SUPERVISOR_PROGRAM}"
  exit 0
fi

# 宝塔面板内置 supervisor 路径（部分版本）
BT_SUPERVISORCTL="/www/server/panel/pyenv/bin/supervisorctl"
if [[ -x "${BT_SUPERVISORCTL}" ]]; then
  echo "重启 Supervisor 程序: ${SUPERVISOR_PROGRAM}"
  "${BT_SUPERVISORCTL}" restart "${SUPERVISOR_PROGRAM}"
  "${BT_SUPERVISORCTL}" status "${SUPERVISOR_PROGRAM}"
  exit 0
fi

echo "错误: 未找到 supervisorctl，请确认已安装 Supervisor 插件" >&2
exit 1
