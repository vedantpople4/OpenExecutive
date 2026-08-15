"""Tests for the `openexec render` command.

Lives outside test_cli.py deliberately: test_cli.py is excluded from the CI
run (`pytest tests/ --ignore=tests/test_cli.py`) because it hits the
live-LLM path elsewhere in that file. `render` never touches an LLM -- it
only reads a stored decision JSON and writes HTML -- so it belongs in the
CI-covered suite, and a regression here should actually fail CI.

Regression coverage: a prior bug had a malformed comment block
(`# ==============================@app.command()` on one line) swallow the
`@app.command()` decorator into a comment, so `render` was defined but never
registered with Typer -- it was silently absent from `openexec --help` and
`openexec render ...` failed with "No such command 'render'". These tests
invoke the real `app` object via CliRunner so a missing registration fails
the test the same way it fails a real invocation.
"""

import json

from typer.testing import CliRunner

from openexec.cli import app


def test_render_is_a_registered_command():
    result = CliRunner().invoke(app, ["render", "--help"])
    assert result.exit_code == 0
    assert "No such command" not in result.output


def test_render_writes_standalone_html(tmp_path):
    decision = {
        "timestamp": "20260101_000000",
        "prompt": "Test decision?",
        "results": {
            "executive_summary": "Ship the integration path.",
            "board_decision": {
                "summary": "Commit to integration.",
                "consensus_points": ["Speed matters."],
            },
            "agent_reports": {},
        },
    }
    decision_path = tmp_path / "decision_20260101_000000.json"
    decision_path.write_text(json.dumps(decision))
    output_path = tmp_path / "rendered.html"

    result = CliRunner().invoke(
        app, ["render", str(decision_path), "-o", str(output_path)]
    )

    assert result.exit_code == 0, result.output
    assert output_path.exists()
    html = output_path.read_text()
    assert "<html" in html.lower()
    assert "Commit to integration." in html


def test_render_missing_decision_exits_nonzero(tmp_path):
    result = CliRunner().invoke(
        app, ["render", str(tmp_path / "does_not_exist.json")]
    )
    assert result.exit_code != 0
