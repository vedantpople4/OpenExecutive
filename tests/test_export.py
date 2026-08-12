"""Tests for openexec.export — action-item writers."""

import csv
import json

from openexec.export import (
    export_action_items_csv,
    export_action_items_json,
    export_action_items_markdown,
)

SAMPLE = [
    {"priority": "HIGH", "task": "Post job reqs", "owner": "CEO", "due_date": "2026-08-14"},
    {"priority": "MEDIUM", "task": "Cut vendor", "owner": "CFO", "due_date": "2026-09-01"},
]


class TestJson:
    def test_writes_valid_json(self, tmp_path):
        out = tmp_path / "a.json"
        export_action_items_json(SAMPLE, str(out))
        assert json.loads(out.read_text()) == SAMPLE


class TestCsv:
    def test_writes_header_and_rows(self, tmp_path):
        out = tmp_path / "a.csv"
        export_action_items_csv(SAMPLE, str(out))
        with open(out) as f:
            rows = list(csv.DictReader(f))
        assert rows[0]["task"] == "Post job reqs"
        assert rows[1]["owner"] == "CFO"

    def test_empty_list_writes_no_file(self, tmp_path):
        out = tmp_path / "a.csv"
        export_action_items_csv([], str(out))
        assert not out.exists()


class TestMarkdown:
    def test_writes_checklist(self, tmp_path):
        out = tmp_path / "a.md"
        export_action_items_markdown(SAMPLE, str(out))
        text = out.read_text()
        assert "# Action Items" in text
        assert "[HIGH] Post job reqs" in text
        assert "Owner: CFO" in text

    def test_empty_list_still_writes_header(self, tmp_path):
        out = tmp_path / "a.md"
        export_action_items_markdown([], str(out))
        assert "# Action Items" in out.read_text()