import tempfile
from pathlib import Path

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


def test_cli_get_lfdi(runner):
    file_name = "example-certs/example-ABC-cert.pem"
    result = runner.invoke(app, ["cert-lfdi", file_name])
    expected_lfdi = "CA6A-EDC0-3021-4C70-B798-89EF-B8E5-D8CD-244D-CDAA"
    assert f"The LFDI is: {expected_lfdi}" in result.stdout
    assert result.exit_code == 0


def test_cli_create_serca(runner):
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(app, ["create-serca", "--output-dir", tmpdir])
        assert result.exit_code == 0

        exp_file = Path(tmpdir) / "serca.pem"
        assert exp_file.exists()
