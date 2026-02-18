"""
Tests for src/utils/export.py
"""
import json
import os
import tempfile
from pathlib import Path

import pytest
from src.utils.export import (
    export_to_eve_csv,
    export_to_markdown,
    export_to_html,
    ExportManager,
)

SKILLS_DATA = [
    {"name": "Drones",          "trained_skill_level": 5, "skillpoints_in_skill": 256_000},
    {"name": "Drone Navigation", "trained_skill_level": 3, "skillpoints_in_skill": 8_000},
    {"name": "Gunnery",         "trained_skill_level": 1, "skillpoints_in_skill": 250},
]

QUEUE_DATA = [
    {"name": "Drones",    "finished_level": 5},
    {"name": "Gunnery",   "finished_level": 2},
]

PLAN_DATA = [
    {"name": "Drones",    "level": 5},
    {"name": "Gunnery",   "level": 2},
]


@pytest.fixture
def tmp_path_file(tmp_path):
    return tmp_path


class TestExportCSV:
    def test_skills_csv_has_header(self, tmp_path):
        path = tmp_path / "out.csv"
        export_to_eve_csv(path, SKILLS_DATA, "skills_all")
        content = path.read_text()
        assert "Skill Name,Level" in content

    def test_skills_csv_rows(self, tmp_path):
        path = tmp_path / "out.csv"
        export_to_eve_csv(path, SKILLS_DATA, "skills_all")
        content = path.read_text()
        assert "Drones,5" in content
        assert "Gunnery,1" in content

    def test_queue_csv(self, tmp_path):
        path = tmp_path / "queue.csv"
        export_to_eve_csv(path, QUEUE_DATA, "queue")
        content = path.read_text()
        assert "Drones,5" in content

    def test_plan_csv(self, tmp_path):
        path = tmp_path / "plan.csv"
        export_to_eve_csv(path, PLAN_DATA, "plan")
        content = path.read_text()
        assert "Gunnery,2" in content


class TestExportMarkdown:
    def test_has_table_header(self, tmp_path):
        path = tmp_path / "out.md"
        export_to_markdown(path, SKILLS_DATA, "skills_all", "TestChar")
        content = path.read_text()
        assert "| Skill Name | Level |" in content
        assert "|------------|-------|" in content

    def test_has_char_name_heading(self, tmp_path):
        path = tmp_path / "out.md"
        export_to_markdown(path, SKILLS_DATA, "skills_all", "TestChar")
        content = path.read_text()
        assert "TestChar" in content

    def test_rows_present(self, tmp_path):
        path = tmp_path / "out.md"
        export_to_markdown(path, SKILLS_DATA, "skills_all")
        content = path.read_text()
        assert "| Drones | 5 |" in content

    def test_total_line(self, tmp_path):
        path = tmp_path / "out.md"
        export_to_markdown(path, SKILLS_DATA, "skills_all")
        content = path.read_text()
        assert "Total:" in content


class TestExportHTML:
    def test_is_valid_html(self, tmp_path):
        path = tmp_path / "out.html"
        export_to_html(path, SKILLS_DATA, "skills_all", "TestChar")
        content = path.read_text()
        assert "<!DOCTYPE html>" in content
        assert "<table>" in content
        assert "</html>" in content

    def test_has_skill_rows(self, tmp_path):
        path = tmp_path / "out.html"
        export_to_html(path, SKILLS_DATA, "skills_all", "TestChar")
        content = path.read_text()
        assert "Drones" in content
        assert "Gunnery" in content

    def test_char_name_in_title(self, tmp_path):
        path = tmp_path / "out.html"
        export_to_html(path, SKILLS_DATA, "skills_all", "TestChar")
        content = path.read_text()
        assert "TestChar" in content

    def test_empty_data(self, tmp_path):
        path = tmp_path / "empty.html"
        export_to_html(path, [], "skills_all")
        content = path.read_text()
        assert "<table>" in content  # should still produce valid HTML


class TestExportManager:
    def test_csv_export(self, tmp_path):
        mgr  = ExportManager(output_dir=tmp_path)
        path = tmp_path / "result.csv"
        res  = mgr.export("Char", "skills_all", "csv", SKILLS_DATA, full_path=str(path))
        assert "Saved to" in res
        assert path.exists()

    def test_markdown_export(self, tmp_path):
        mgr  = ExportManager(output_dir=tmp_path)
        path = tmp_path / "result.md"
        res  = mgr.export("Char", "skills_all", "markdown", SKILLS_DATA, full_path=str(path))
        assert "Saved to" in res
        assert path.exists()

    def test_html_export(self, tmp_path):
        mgr  = ExportManager(output_dir=tmp_path)
        path = tmp_path / "result.html"
        res  = mgr.export("Char", "skills_all", "html", SKILLS_DATA, full_path=str(path))
        assert "Saved to" in res
        assert path.exists()

    def test_unsupported_format(self, tmp_path):
        mgr = ExportManager(output_dir=tmp_path)
        res = mgr.export("Char", "skills_all", "pdf", SKILLS_DATA,
                         full_path=str(tmp_path / "x.pdf"))
        assert "Unsupported" in res

    def test_backup_tokens(self, tmp_path):
        tokens_file = tmp_path / "tokens.json"
        tokens_file.write_text('{"test": 1}')
        mgr    = ExportManager(output_dir=tmp_path)
        backup = mgr.backup_tokens(tokens_file)
        assert backup is not None
        assert Path(backup).exists()
        assert "backup_tokens_" in backup

    def test_backup_tokens_missing_file(self, tmp_path):
        mgr    = ExportManager(output_dir=tmp_path)
        result = mgr.backup_tokens(tmp_path / "nonexistent.json")
        assert result is None
