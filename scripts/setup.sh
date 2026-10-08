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
  printf 'Usage: %s <start|stop|restart|run|status|install-dev|install-prod [version]|publish|upgrade [version]|rollback <version>|uninstall>\n' "${0##*/}" >&2
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

do_install_dev() {
  funbuild install
}

do_install_prod() {
  local version="${1:-}"
  if [[ -n "${version}" ]]; then
    uv tool install "${SERVICE_NAME}==${version}"
  else
    uv tool install "${SERVICE_NAME}"
  fi
}

do_publish() {
  funbuild build
}

main() {
  local action="${1:-}"
  shift || true

  case "${action}" in
    start|stop|restart|run|status|publish)
      (( $# == 0 )) || {
        usage
        die "${action} takes no further arguments"
      }
      "do_${action}"
      ;;
    install-dev)
      (( $# == 0 )) || die "install-dev takes no further arguments"
      do_install_dev
      ;;
    install-prod)
      (( $# <= 1 )) || die "install-prod accepts at most one version"
      do_install_prod "${1:-}"
      ;;
    upgrade)
      (( $# <= 1 )) || die "upgrade accepts at most one version"
      "${CLI_NAME}" upgrade "$@"
      ;;
    rollback)
      (( $# == 1 )) || die "rollback requires a version"
      "${CLI_NAME}" rollback "$1"
      ;;
    uninstall)
      (( $# == 0 )) || die "uninstall takes no further arguments"
      "${CLI_NAME}" uninstall
      ;;
    *)
      usage
      die "unknown action: ${action:-<empty>}"
      ;;
  esac
}

main "$@"
