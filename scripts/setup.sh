#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="funlesson-api"
CLI_NAME="funlesson-api"       # 安装后的 CLI 名，见 service-release-governance
PORT=18812
CONFIG_PATH=""                  # 留空则用 CLI 自身默认路径
                                 # (${XDG_CONFIG_HOME:-~/.config}/farfarfun/funlesson-api/config.toml)。
                                 # "${CLI_NAME}" 自己在该路径旁写/读 server.pid，这个脚本不直接碰 PID 文件。

readonly SERVICE_NAME CLI_NAME PORT CONFIG_PATH

usage() {
  printf 'Usage: %s <start|stop|restart|run|status|install|publish>\n' "${0##*/}" >&2
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 2
}

cli_args() {
  CLI_ARGS=(--port "${PORT}")
  if [[ -n "${CONFIG_PATH}" ]]; then
    CLI_ARGS+=(--config "${CONFIG_PATH}")
  fi
}

do_start() {
  cli_args
  "${CLI_NAME}" server start "${CLI_ARGS[@]}"
}

do_run() {
  cli_args
  exec "${CLI_NAME}" server run "${CLI_ARGS[@]}"
}

do_stop() {
  "${CLI_NAME}" server stop
}

do_restart() {
  do_stop
  do_start
}

do_status() {
  "${CLI_NAME}" server status
}

do_install() {
  funbuild install
}

do_publish() {
  funbuild build
}

main() {
  local action="${1:-}"

  case "${action}" in
    start|stop|restart|run|status|install|publish)
      (( $# == 1 )) || {
        usage
        die "${action} takes no further arguments"
      }
      "do_${action}"
      ;;
    *)
      usage
      die "unknown action: ${action:-<empty>}"
      ;;
  esac
}

main "$@"
