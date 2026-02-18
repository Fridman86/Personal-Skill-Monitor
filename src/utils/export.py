"""
Export utilities for Personal Skill Monitor.

Supported formats:
  - Clipboard  (EVE-format: "Skill Name Level")
  - CSV        (Skill Name, Level)
  - Markdown   (GitHub-flavoured table)
  - HTML       (standalone table page)
"""
from __future__ import annotations

import csv
import shutil
from datetime import datetime
from pathlib import Path

from src.utils.paths import PathManager
from src.data import skills_db


# ── Helpers ──────────────────────────────────────────────────────────────────

def _iter_rows(data: list[dict], data_type: str):
    """Yield (name, level) tuples for any data_type."""
    if data_type.startswith("skills"):
        for s in data:
            name  = s.get("name", skills_db.get_skill_name(s.get("skill_id", 0)))
            level = s.get("trained_skill_level", 0)
            if level > 0:
                yield name, level
    elif data_type == "queue":
        for q in data:
            name  = q.get("name", skills_db.get_skill_name(q.get("skill_id", 0)))
            level = q.get("finished_level", 0)
            yield name, level
    elif data_type == "plan":
        for p in data:
            name  = p.get("name", "")
            level = p.get("level", 0)
            yield name, level


# ── Clipboard ─────────────────────────────────────────────────────────────────

def export_to_eve_clipboard(root, data: list[dict], data_type: str = "skills") -> str:
    """Copy skills in EVE Online game format: 'Skill Name Level'."""
    lines = [f"{name} {level}" for name, level in _iter_rows(data, data_type)]
    text  = "\n".join(lines)
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    return f"Copied {len(lines)} skills to clipboard"


# ── CSV ───────────────────────────────────────────────────────────────────────

def export_to_eve_csv(path: str | Path, data: list[dict], data_type: str = "skills") -> None:
    """Save skills to a CSV file: Skill Name, Level."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Skill Name", "Level"])
        for name, level in _iter_rows(data, data_type):
            writer.writerow([name, level])


# ── Markdown ──────────────────────────────────────────────────────────────────

def export_to_markdown(path: str | Path, data: list[dict], data_type: str = "skills",
                       char_name: str = "") -> None:
    """Save skills as a GitHub-flavoured Markdown table."""
    rows = list(_iter_rows(data, data_type))
    lines = []

    if char_name:
        lines.append(f"# Skill Export — {char_name}\n")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    lines.append(f"| Skill Name | Level |")
    lines.append(f"|------------|-------|")
    for name, level in rows:
        lines.append(f"| {name} | {level} |")

    lines.append(f"\n*Total: {len(rows)} skills*")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ── HTML ──────────────────────────────────────────────────────────────────────

def export_to_html(path: str | Path, data: list[dict], data_type: str = "skills",
                   char_name: str = "") -> None:
    """Save skills as a standalone HTML page with an EVE-styled table."""
    rows  = list(_iter_rows(data, data_type))
    title = f"Skill Export — {char_name}" if char_name else "Skill Export"
    ts    = datetime.now().strftime("%Y-%m-%d %H:%M")

    row_html = "\n".join(
        f"    <tr><td>{name}</td><td class='lvl'>{level}</td></tr>"
        for name, level in rows
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    body {{
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #0d1117;
      color: #c9d1d9;
      margin: 40px auto;
      max-width: 720px;
    }}
    h1 {{ color: #3aa8d0; margin-bottom: 4px; }}
    .meta {{ color: #8b949e; font-size: 0.85em; margin-bottom: 24px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.95em;
    }}
    th {{
      background: #161b22;
      color: #3aa8d0;
      padding: 10px 14px;
      text-align: left;
      border-bottom: 2px solid #30363d;
    }}
    td {{
      padding: 8px 14px;
      border-bottom: 1px solid #21262d;
    }}
    td.lvl {{ text-align: center; font-weight: bold; color: #58a6ff; }}
    tr:hover td {{ background: #161b22; }}
    .footer {{ margin-top: 16px; color: #8b949e; font-size: 0.8em; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div class="meta">Generated: {ts} &nbsp;|&nbsp; {len(rows)} skills</div>
  <table>
    <thead><tr><th>Skill Name</th><th>Level</th></tr></thead>
    <tbody>
{row_html}
    </tbody>
  </table>
  <div class="footer">Personal Skill Monitor — EVE Online</div>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


# ── ExportManager ─────────────────────────────────────────────────────────────

class ExportManager:
    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir) if output_dir else PathManager.get_export_dir()
        self.output_dir.mkdir(exist_ok=True)

    def export(self, char_name: str, data_type: str, format: str,
               data: list[dict], tk_root=None, full_path: str | None = None) -> str:
        fmt = format.lower()

        # ── Clipboard ──
        if fmt == "clipboard":
            if tk_root:
                return export_to_eve_clipboard(tk_root, data, data_type)
            return "No window available for clipboard"

        # ── Resolve output path ──
        if full_path:
            path = Path(full_path)
        else:
            ext_map = {"csv": "csv", "markdown": "md", "html": "html"}
            ext = ext_map.get(fmt, fmt)
            filename = f"{char_name}_{data_type}.{ext}"
            path = self.output_dir / filename

        # ── Write file ──
        if fmt == "csv":
            export_to_eve_csv(path, data, data_type)
        elif fmt == "markdown":
            export_to_markdown(path, data, data_type, char_name=char_name)
        elif fmt == "html":
            export_to_html(path, data, data_type, char_name=char_name)
        else:
            return f"Unsupported format: {fmt}"

        return f"Saved to {path}"

    def backup_tokens(self, tokens_path: Path) -> str | None:
        """Create a dated backup of tokens.json next to the original."""
        if not tokens_path.exists():
            return None
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = tokens_path.parent / f"backup_tokens_{ts}.json"
        shutil.copy2(tokens_path, dest)
        return str(dest)
