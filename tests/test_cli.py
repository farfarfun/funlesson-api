from typer.testing import CliRunner

from funlesson_api import cli


runner = CliRunner()


def test_cli_exposes_service_and_package_commands() -> None:
    result = runner.invoke(cli.app, ["--help"])

    assert result.exit_code == 0
    for command in ("server", "upgrade", "rollback", "uninstall"):
        assert command in result.output

    result = runner.invoke(cli.app, ["server", "--help"])
    assert result.exit_code == 0
    for command in ("start", "run", "stop", "restart", "status"):
        assert command in result.output


def test_package_commands_use_uv_tool(monkeypatch) -> None:
    commands: list[list[str]] = []
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda command, check: commands.append(command)
        or type("Result", (), {"returncode": 0})(),
    )
    monkeypatch.setattr(cli, "server_stop", lambda: None)

    for arguments in (("upgrade",), ("upgrade", "1.2.3"), ("rollback", "1.2.2"), ("uninstall",)):
        result = runner.invoke(cli.app, list(arguments))
        assert result.exit_code == 0, result.output

    assert commands == [
        ["uv", "tool", "install", "--upgrade", "funlesson-api"],
        ["uv", "tool", "install", "--upgrade", "funlesson-api==1.2.3"],
        ["uv", "tool", "install", "--force", "funlesson-api==1.2.2"],
        ["uv", "tool", "uninstall", "funlesson-api"],
    ]
