import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path

def export_to_csv(path, data, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(data)

def export_to_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def export_to_text(path, data):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(f"{item}\n")

def export_to_xml(path, data, root_name="root"):
    root = ET.Element(root_name)
    for item in data:
        child = ET.SubElement(root, "item")
        for k, v in item.items():
            sub = ET.SubElement(child, str(k))
            sub.text = str(v)
    tree = ET.ElementTree(root)
    # Using encode to get a string if path is None, or write to file
    if path:
        tree.write(path, encoding="utf-8", xml_declaration=True)
    else:
        return ET.tostring(root, encoding='unicode')

def export_to_clipboard(root, text):
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update() 

def export_to_python_list(path, data):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"data = {repr(data)}")

class ExportManager:
    def __init__(self, output_dir="exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def export(self, char_name, data_type, format, data, tk_root=None, full_path=None):
        if full_path:
            path = Path(full_path)
        else:
            filename = f"{char_name}_{data_type}.{format.lower()}"
            path = self.output_dir / filename
        
        # Define fieldnames based on data_type
        if data_type.startswith("skills"):
            fieldnames = ["skill_id", "name", "group", "category", "trained_skill_level", "skillpoints_in_skill"]
        elif data_type == "queue":
            fieldnames = ["skill_id", "name", "category", "queue_position", "finished_level", "start_date", "finish_date"]
        else:
            fieldnames = data[0].keys() if data else []

        # Filter data to only include these fields
        prepared_data = []
        for item in data:
            row = {k: item.get(k, "") for k in fieldnames}
            prepared_data.append(row)

        fmt = format.lower()
        if fmt == "csv":
            export_to_csv(path, prepared_data, fieldnames)
        elif fmt == "json":
            export_to_json(path, prepared_data)
        elif fmt in ("text", "txt"):
            export_to_text(path, prepared_data)
        elif fmt == "xml":
            export_to_xml(path, prepared_data, root_name=data_type)
        elif fmt == "python":
            export_to_python_list(path, prepared_data)
        elif fmt == "clipboard" and tk_root:
            # Human readable representation for clipboard
            if data_type.startswith("skills"):
                text = "Skill ID | Name | Group | Category | Level | SP\n"
                text += "-" * 80 + "\n"
                for s in prepared_data:
                    text += f"{s['skill_id']} | {s['name']} | {s['group']} | {s['category']} | {s['trained_skill_level']} | {s['skillpoints_in_skill']}\n"
            else:
                text = json.dumps(prepared_data, indent=2)
            
            export_to_clipboard(tk_root, text)
            return "Copied to clipboard"
            
        return f"Saved to {path}"
