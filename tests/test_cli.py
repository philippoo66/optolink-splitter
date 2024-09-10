from click.testing import CliRunner
from optolink_splitter.cli import main

def test_cli_smoke_test() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--help"
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

def test_cli_poll_items_config_path_missing() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--optolink-port",
            "/dev/SomePort",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 2
    output = result.output.strip()
    assert "Missing option '--poll-items-config-path'" in output
