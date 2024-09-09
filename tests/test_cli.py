from click.testing import CliRunner
from optolink_splitter.cli import main

def test_smoke_test_cli() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--help"
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
