import pytest
from typer.testing import CliRunner

from sep2tools.cli import app


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_version(runner):
    result = runner.invoke(app, ["--version"])
    assert "sep2tools version:" in result.stdout
    assert result.exit_code == 0
