"""funlesson-api 命令行入口。

服务生命周期（`server run/start/stop/restart/status`），逻辑照搬 funflix。
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Annotated, Any, NoReturn

import typer

from funlesson_api import __version__

app = typer.Typer(help="funlesson-api 命令行工具")
server_app = typer.Typer(help="API 服务生命周期", no_args_is_help=True)
app.add_typer(server_app, name="server")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def _main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="打印版本号后退出",
        ),
    ] = False,
) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


# --- 输出 helpers ------------------------------------------------------------


def _fail(message: str) -> NoReturn:
    typer.secho(message, fg=typer.colors.RED, err=True)
    raise typer.Exit(1)


def _ok(message: str) -> None:
    typer.secho(message, fg=typer.colors.GREEN)


def _warn(message: str) -> None:
    typer.secho(message, fg=typer.colors.YELLOW)


# --- server 子命令 ------------------------------------------------------------

DEFAULT_SERVER_HOST = "127.0.0.1"
DEFAULT_SERVER_PORT = 18812

SERVER_STOP_TIMEOUT_SECONDS = 10


def _default_server_config_path() -> Path:
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(xdg_config_home) / "farfarfun" / "funlesson-api" / "config.toml"


def _server_state_dir() -> Path:
    return _default_server_config_path().parent


def _server_pid_file() -> Path:
    return _server_state_dir() / "server.pid"


def _server_log_file() -> Path:
    return _server_state_dir() / "server.log"


def _load_server_config(config: Path | None) -> dict[str, Any]:
    path = config or _default_server_config_path()
    if not path.exists():
        if config is not None:
            _fail(f"配置文件不存在：{path}")
        return {}

    suffix = path.suffix.lower()
    if suffix == ".toml":
        import tomllib

        data: dict[str, Any] = tomllib.loads(path.read_text(encoding="utf-8"))
    elif suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
    elif suffix == ".env":
        from dotenv import dotenv_values

        data = dict(dotenv_values(path))
    else:
        _fail(f"不支持的配置文件格式：{path.suffix}（仅支持 .toml / .json / .env）")
    return {str(key).lower(): value for key, value in data.items() if value is not None}


def _resolve_server_host_port(
    host: str | None, port: int | None, config: Path | None
) -> tuple[str, int]:
    file_config = _load_server_config(config)
    resolved_host = host or str(file_config.get("host") or DEFAULT_SERVER_HOST)
    resolved_port = (
        port
        if port is not None
        else int(file_config.get("port") or DEFAULT_SERVER_PORT)
    )
    return resolved_host, resolved_port


def _read_server_pid() -> int | None:
    pid_file = _server_pid_file()
    if not pid_file.exists():
        return None
    try:
        pid = int(pid_file.read_text().strip())
    except ValueError:
        return None
    return pid if pid > 1 else None


def _pid_is_live(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _resolve_cli_executable() -> str:
    return shutil.which("funlesson-api") or sys.argv[0]


@server_app.command("run")
def server_run(
    host: Annotated[str | None, typer.Option(help="监听地址，覆盖配置文件")] = None,
    port: Annotated[int | None, typer.Option(help="监听端口，覆盖配置文件")] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config", help="配置文件路径（.toml/.json/.env），缺省用 XDG 默认路径"
        ),
    ] = None,
    reload: Annotated[
        bool, typer.Option(help="代码变更自动重载（开发用，不代表托管生命周期）")
    ] = False,
) -> None:
    """前台启动 API 服务，Ctrl-C 停止。

    调试、临时跑一下用这个；要后台常驻用 `funlesson-api server start`——它内部
    就是拉一个子进程跑这条命令，只是重定向了输出、写了 PID 文件。
    """
    import uvicorn

    resolved_host, resolved_port = _resolve_server_host_port(host, port, config)
    uvicorn.run(
        "funlesson_api.main:app",
        host=resolved_host,
        port=resolved_port,
        reload=reload,
    )


@server_app.command("start")
def server_start(
    host: Annotated[str | None, typer.Option(help="监听地址，覆盖配置文件")] = None,
    port: Annotated[int | None, typer.Option(help="监听端口，覆盖配置文件")] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config", help="配置文件路径（.toml/.json/.env），缺省用 XDG 默认路径"
        ),
    ] = None,
) -> None:
    """后台启动 API 服务。

    拉一个子进程跑 `server run`，PID 写到配置目录下的 `server.pid`，输出
    重定向到同目录的 `server.log`。停止/重启见 `server stop` / `server restart`。
    """
    existing = _read_server_pid()
    if existing is not None and _pid_is_live(existing):
        _fail(f"funlesson-api 已在运行（pid {existing}）")

    pid_file = _server_pid_file()
    log_file = _server_log_file()
    pid_file.parent.mkdir(parents=True, exist_ok=True)

    command = [_resolve_cli_executable(), "server", "run"]
    if host is not None:
        command += ["--host", host]
    if port is not None:
        command += ["--port", str(port)]
    if config is not None:
        command += ["--config", str(config)]

    with log_file.open("ab") as log:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    pid_file.write_text(f"{process.pid}\n")

    time.sleep(1)
    if process.poll() is not None:
        pid_file.unlink(missing_ok=True)
        _fail(f"funlesson-api 启动失败，看日志：{log_file}")

    _, resolved_port = _resolve_server_host_port(host, port, config)
    _ok(
        f"funlesson-api 已启动（pid {process.pid}，端口 {resolved_port}，日志 {log_file}）"
    )


@server_app.command("stop")
def server_stop() -> None:
    """停止后台运行的 API 服务（发 SIGTERM，等它优雅退出）。"""
    pid_file = _server_pid_file()
    pid = _read_server_pid()
    if pid is None:
        pid_file.unlink(missing_ok=True)
        _warn("funlesson-api 未在运行")
        return
    if not _pid_is_live(pid):
        pid_file.unlink(missing_ok=True)
        _warn("PID 文件已失效，已清理")
        return

    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + SERVER_STOP_TIMEOUT_SECONDS
    while _pid_is_live(pid):
        if time.monotonic() >= deadline:
            _fail(
                f"funlesson-api 在 {SERVER_STOP_TIMEOUT_SECONDS}s 内未退出（pid {pid}）"
            )
        time.sleep(0.2)

    pid_file.unlink(missing_ok=True)
    _ok("funlesson-api 已停止")


@server_app.command("restart")
def server_restart(
    host: Annotated[str | None, typer.Option(help="监听地址，覆盖配置文件")] = None,
    port: Annotated[int | None, typer.Option(help="监听端口，覆盖配置文件")] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config", help="配置文件路径（.toml/.json/.env），缺省用 XDG 默认路径"
        ),
    ] = None,
) -> None:
    """重启：先 `stop`（没在跑也不报错），再 `start`。"""
    server_stop()
    server_start(host=host, port=port, config=config)


@server_app.command("status")
def server_status() -> None:
    """查看后台服务是否在跑，以及安装的版本号。"""
    pid = _read_server_pid()
    if pid is not None and _pid_is_live(pid):
        _ok(f"运行中（pid {pid}，版本 {__version__}）")
    elif _server_pid_file().exists():
        _warn(f"PID 文件失效（{_server_pid_file()}）")
    else:
        _warn("未在运行")


if __name__ == "__main__":
    app()
