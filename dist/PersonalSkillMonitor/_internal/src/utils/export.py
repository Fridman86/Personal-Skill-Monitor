import csv
from pathlib import Path
from src.utils.paths import PathManager
from src.data import skills_db


def export_to_eve_clipboard(root, data, data_type="skills"):
    """Export skills in EVE Online game format: 'Skill Name Level'"""
    lines = []
    if data_type.startswith("skills"):
        for s in data:
            name = s.get("name", skills_db.get_skill_name(s.get("skill_id", 0)))
            level = s.get("trained_skill_level", 0)
            if level > 0:
                lines.append(f"{name} {level}")
    elif data_type == "queue":
        for q in data:
            name = q.get("name", skills_db.get_skill_name(q.get("skill_id", 0)))
            level = q.get("finished_level", 0)
            lines.append(f"{name} {level}")
    elif data_type == "plan":
        for p in data:
            name = p.get("name", "")
            level = p.get("level", 0)
            lines.append(f"{name} {level}")

    text = "\n".join(lines)
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    return f"Copied {len(lines)} skills to clipboard"


def export_to_eve_csv(path, data, data_type="skills"):
    """Export skills in EVE-compatible CSV format: Skill Name, Level"""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Skill Name", "Level"])
        if data_type.startswith("skills"):
            for s in data:
                name = s.get("name", skills_db.get_skill_name(s.get("skill_id", 0)))
                level = s.get("trained_skill_level", 0)
                if level > 0:
                    writer.writerow([name, level])
        elif data_type == "queue":
            for q in data:
                name = q.get("name", skills_db.get_skill_name(q.get("skill_id", 0)))
                level = q.get("finished_level", 0)
                writer.writerow([name, level])
        elif data_type == "plan":
            for p in data:
                name = p.get("name", "")
                level = p.get("level", 0)
                writer.writerow([name, level])


class ExportManager:
    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir) if output_dir else PathManager.get_export_dir()
        self.output_dir.mkdir(exist_ok=True)

    def export(self, char_name, data_type, format, data, tk_root=None, full_path=None):
        fmt = format.lower()

        if fmt == "clipboard":
            if tk_root:
                return export_to_eve_clipboard(tk_root, data, data_type)
            return "No window available for clipboard"

        if fmt == "csv":
            if full_path:
                path = Path(full_path)
            else:
                filename = f"{char_name}_{data_type}.csv"
                path = self.output_dir / filename
            export_to_eve_csv(path, data, data_type)
            return f"Saved to {path}"

        return "Unsupported format"
