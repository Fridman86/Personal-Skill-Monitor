"""
Skill Plan Manager — allows creating custom training plans
that can be exported in EVE Online game-importable format.

EVE Online import format:
  Skill Name 1
  Skill Name 2
  ...
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
from pathlib import Path
from src.data import skills_db
from src.utils.paths import PathManager


class SkillPlanManager(tk.Toplevel):
    """A separate window for creating and managing skill training plans."""

    def __init__(self, parent, current_skills=None):
        super().__init__(parent)
        self.parent_app = parent
        self.title("Skill Plan Manager")
        self.geometry("900x650")
        self.minsize(750, 500)
        self.configure(bg="#0e1017")

        self.current_skills = current_skills or []
        self.plans_dir = PathManager.get_app_data_dir() / "skill_plans"
        self.plans_dir.mkdir(exist_ok=True)
        self.current_plan_name = None
        self.plan_skills = []  # list of {"name": str, "level": int}

        self._build_skill_catalog()
        self._setup_ui()
        self._load_plan_list()

        # Make this window modal-like but allow interaction with parent
        self.transient(parent)
        self.focus_set()

    def _build_skill_catalog(self):
        """Build a sorted list of all skills from the database."""
        self.all_skills = {}
        for sid, (name, group, category) in skills_db.SKILLS.items():
            if name == str(sid):
                continue  # skip placeholder/unknown
            self.all_skills[name] = {
                "skill_id": sid,
                "name": name,
                "group": group,
                "category": category
            }

    def _setup_ui(self):
        # Top bar
        top = ttk.Frame(self, style="Toolbar.TFrame")
        top.pack(fill=tk.X, padx=0, pady=0)

        ttk.Label(top, text="⚙  Skill Plan Manager",
                  style="Title.TLabel",
                  background="#141820").pack(side=tk.LEFT, padx=15, pady=12)

        # Main content — 3-column layout
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        main.columnconfigure(1, weight=1)
        main.columnconfigure(2, weight=1)
        main.rowconfigure(0, weight=1)

        # === Left Column: Plan list ===
        left_frame = ttk.LabelFrame(main, text=" Saved Plans ", style="TLabelframe")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)

        self.plan_listbox = tk.Listbox(left_frame, width=22, font=("Segoe UI", 9),
                                        bg="#181c26", fg="#c8ccd4",
                                        selectbackground="#1a4a6a",
                                        selectforeground="#e8ecf4",
                                        borderwidth=0, highlightthickness=0,
                                        activestyle="none")
        self.plan_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.plan_listbox.bind("<<ListboxSelect>>", self._on_plan_select)

        plan_btn_frame = ttk.Frame(left_frame)
        plan_btn_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        ttk.Button(plan_btn_frame, text="＋ New", command=self._new_plan, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(plan_btn_frame, text="✎ Rename", command=self._rename_plan, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(plan_btn_frame, text="✕ Delete", command=self._delete_plan, width=8).pack(side=tk.LEFT, padx=2)

        # === Middle Column: Skill catalog ===
        mid_frame = ttk.LabelFrame(main, text=" Skill Catalog ", style="TLabelframe")
        mid_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=0)
        mid_frame.columnconfigure(0, weight=1)
        mid_frame.rowconfigure(1, weight=1)

        # Search bar
        search_bar = ttk.Frame(mid_frame)
        search_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ttk.Label(search_bar, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.catalog_search_var = tk.StringVar()
        self.catalog_search_var.trace_add("write", lambda *a: self._filter_catalog())
        ttk.Entry(search_bar, textvariable=self.catalog_search_var, width=20).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Group filter
        ttk.Label(search_bar, text="  Group:").pack(side=tk.LEFT, padx=(10, 5))
        self.catalog_group_var = tk.StringVar(value="All")
        groups = sorted(set(s["group"] for s in self.all_skills.values()))
        self.catalog_group_cb = ttk.Combobox(search_bar, textvariable=self.catalog_group_var,
                                              state="readonly", values=["All"] + groups, width=16)
        self.catalog_group_cb.pack(side=tk.LEFT, padx=2)
        self.catalog_group_cb.bind("<<ComboboxSelected>>", lambda e: self._filter_catalog())

        # Catalog treeview
        cat_tree_frame = ttk.Frame(mid_frame)
        cat_tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))

        self.catalog_tree = ttk.Treeview(cat_tree_frame,
                                          columns=("name", "group", "category"),
                                          show="headings", height=15)
        self.catalog_tree.heading("name", text="Skill Name")
        self.catalog_tree.heading("group", text="Group")
        self.catalog_tree.heading("category", text="Category")
        self.catalog_tree.column("name", width=180)
        self.catalog_tree.column("group", width=120)
        self.catalog_tree.column("category", width=80)

        cat_scroll = ttk.Scrollbar(cat_tree_frame, orient=tk.VERTICAL, command=self.catalog_tree.yview)
        self.catalog_tree.configure(yscrollcommand=cat_scroll.set)
        self.catalog_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cat_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Level selector + Add button
        add_bar = ttk.Frame(mid_frame)
        add_bar.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))

        ttk.Label(add_bar, text="Level:").pack(side=tk.LEFT, padx=(0, 5))
        self.add_level_var = tk.IntVar(value=5)
        level_spin = ttk.Spinbox(add_bar, from_=1, to=5, textvariable=self.add_level_var,
                                  width=4, state="readonly")
        level_spin.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(add_bar, text="→ Add to Plan", style="Accent.TButton",
                   command=self._add_to_plan).pack(side=tk.LEFT, padx=5)
        ttk.Button(add_bar, text="→ Add 1→5", style="Accent.TButton",
                   command=self._add_range_to_plan).pack(side=tk.LEFT, padx=5)

        # === Right Column: Current plan ===
        right_frame = ttk.LabelFrame(main, text=" Current Plan ", style="TLabelframe")
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=0)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        plan_tree_frame = ttk.Frame(right_frame)
        plan_tree_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.plan_tree = ttk.Treeview(plan_tree_frame,
                                       columns=("name", "level"),
                                       show="headings", height=15)
        self.plan_tree.heading("name", text="Skill Name")
        self.plan_tree.heading("level", text="Level")
        self.plan_tree.column("name", width=200)
        self.plan_tree.column("level", width=50, anchor=tk.CENTER)

        plan_scroll = ttk.Scrollbar(plan_tree_frame, orient=tk.VERTICAL, command=self.plan_tree.yview)
        self.plan_tree.configure(yscrollcommand=plan_scroll.set)
        self.plan_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        plan_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Plan action buttons
        plan_actions = ttk.Frame(right_frame)
        plan_actions.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))

        ttk.Button(plan_actions, text="↑", command=self._move_up, width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(plan_actions, text="↓", command=self._move_down, width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(plan_actions, text="✕ Remove", command=self._remove_from_plan, width=9).pack(side=tk.LEFT, padx=5)
        ttk.Button(plan_actions, text="Clear All", command=self._clear_plan, width=8).pack(side=tk.LEFT, padx=2)

        # Bottom export bar
        export_bar = ttk.Frame(right_frame)
        export_bar.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 8))

        ttk.Button(export_bar, text="📋 Copy to Clipboard",
                   style="Accent.TButton",
                   command=self._export_clipboard).pack(side=tk.LEFT, padx=3)
        ttk.Button(export_bar, text="💾 Save as TXT",
                   style="Accent.TButton",
                   command=self._export_txt).pack(side=tk.LEFT, padx=3)
        ttk.Button(export_bar, text="📂 Import from Clipboard",
                   command=self._import_clipboard).pack(side=tk.LEFT, padx=3)

        # Populate catalog
        self._filter_catalog()

    def _filter_catalog(self):
        search = self.catalog_search_var.get().lower()
        group = self.catalog_group_var.get()

        self.catalog_tree.delete(*self.catalog_tree.get_children())
        for name in sorted(self.all_skills.keys()):
            info = self.all_skills[name]
            if search and search not in name.lower():
                continue
            if group != "All" and info["group"] != group:
                continue
            self.catalog_tree.insert("", tk.END, values=(name, info["group"], info["category"]))

    def _load_plan_list(self):
        self.plan_listbox.delete(0, tk.END)
        if self.plans_dir.exists():
            for f in sorted(self.plans_dir.glob("*.json")):
                self.plan_listbox.insert(tk.END, f"  {f.stem}")

    def _on_plan_select(self, event=None):
        sel = self.plan_listbox.curselection()
        if not sel:
            return
        plan_name = self.plan_listbox.get(sel[0]).strip()
        self._load_plan(plan_name)

    def _load_plan(self, name):
        path = self.plans_dir / f"{name}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                self.plan_skills = json.load(f)
        else:
            self.plan_skills = []
        self.current_plan_name = name
        self._refresh_plan_tree()

    def _save_plan(self):
        if not self.current_plan_name:
            return
        path = self.plans_dir / f"{self.current_plan_name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.plan_skills, f, indent=2, ensure_ascii=False)

    def _refresh_plan_tree(self):
        self.plan_tree.delete(*self.plan_tree.get_children())
        for s in self.plan_skills:
            self.plan_tree.insert("", tk.END, values=(s["name"], s["level"]))

    def _new_plan(self):
        name = simpledialog.askstring("New Plan", "Plan name:", parent=self)
        if name and name.strip():
            name = name.strip()
            self.current_plan_name = name
            self.plan_skills = []
            self._save_plan()
            self._load_plan_list()
            self._refresh_plan_tree()
            # Select the new plan in the list
            for i in range(self.plan_listbox.size()):
                if self.plan_listbox.get(i).strip() == name:
                    self.plan_listbox.selection_set(i)
                    break

    def _rename_plan(self):
        if not self.current_plan_name:
            messagebox.showinfo("Info", "Select a plan first")
            return
        new_name = simpledialog.askstring("Rename Plan", "New name:",
                                           initialvalue=self.current_plan_name, parent=self)
        if new_name and new_name.strip():
            old_path = self.plans_dir / f"{self.current_plan_name}.json"
            new_name = new_name.strip()
            new_path = self.plans_dir / f"{new_name}.json"
            if old_path.exists():
                old_path.rename(new_path)
            self.current_plan_name = new_name
            self._load_plan_list()

    def _delete_plan(self):
        if not self.current_plan_name:
            messagebox.showinfo("Info", "Select a plan first")
            return
        if messagebox.askyesno("Confirm", f"Delete plan '{self.current_plan_name}'?", parent=self):
            path = self.plans_dir / f"{self.current_plan_name}.json"
            if path.exists():
                path.unlink()
            self.current_plan_name = None
            self.plan_skills = []
            self._load_plan_list()
            self._refresh_plan_tree()

    def _add_to_plan(self):
        if not self.current_plan_name:
            messagebox.showinfo("Info", "Create or select a plan first")
            return
        sel = self.catalog_tree.selection()
        if not sel:
            return
        level = self.add_level_var.get()
        for item_id in sel:
            name = self.catalog_tree.item(item_id)["values"][0]
            # Check if already in plan at this level
            exists = any(s["name"] == name and s["level"] == level for s in self.plan_skills)
            if not exists:
                self.plan_skills.append({"name": name, "level": level})
        self._save_plan()
        self._refresh_plan_tree()

    def _add_range_to_plan(self):
        """Add skill levels 1 through 5 for selected skill."""
        if not self.current_plan_name:
            messagebox.showinfo("Info", "Create or select a plan first")
            return
        sel = self.catalog_tree.selection()
        if not sel:
            return
        for item_id in sel:
            name = self.catalog_tree.item(item_id)["values"][0]
            for lvl in range(1, 6):
                exists = any(s["name"] == name and s["level"] == lvl for s in self.plan_skills)
                if not exists:
                    self.plan_skills.append({"name": name, "level": lvl})
        self._save_plan()
        self._refresh_plan_tree()

    def _remove_from_plan(self):
        sel = self.plan_tree.selection()
        if not sel:
            return
        indices = []
        for item_id in sel:
            idx = self.plan_tree.index(item_id)
            indices.append(idx)
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self.plan_skills):
                self.plan_skills.pop(idx)
        self._save_plan()
        self._refresh_plan_tree()

    def _move_up(self):
        sel = self.plan_tree.selection()
        if not sel:
            return
        idx = self.plan_tree.index(sel[0])
        if idx > 0:
            self.plan_skills[idx], self.plan_skills[idx - 1] = self.plan_skills[idx - 1], self.plan_skills[idx]
            self._save_plan()
            self._refresh_plan_tree()
            # Re-select item
            children = self.plan_tree.get_children()
            if children:
                self.plan_tree.selection_set(children[idx - 1])

    def _move_down(self):
        sel = self.plan_tree.selection()
        if not sel:
            return
        idx = self.plan_tree.index(sel[0])
        if idx < len(self.plan_skills) - 1:
            self.plan_skills[idx], self.plan_skills[idx + 1] = self.plan_skills[idx + 1], self.plan_skills[idx]
            self._save_plan()
            self._refresh_plan_tree()
            children = self.plan_tree.get_children()
            if children:
                self.plan_tree.selection_set(children[idx + 1])

    def _clear_plan(self):
        if not self.plan_skills:
            return
        if messagebox.askyesno("Confirm", "Clear all skills from this plan?", parent=self):
            self.plan_skills = []
            self._save_plan()
            self._refresh_plan_tree()

    def _export_clipboard(self):
        if not self.plan_skills:
            messagebox.showinfo("Info", "Plan is empty")
            return
        lines = [f"{s['name']} {s['level']}" for s in self.plan_skills]
        text = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        messagebox.showinfo("Exported",
                            f"Copied {len(lines)} skills to clipboard.\n\n"
                            "You can paste this directly into EVE Online's\nskill queue import.",
                            parent=self)

    def _export_txt(self):
        if not self.plan_skills:
            messagebox.showinfo("Info", "Plan is empty")
            return
        name = self.current_plan_name or "skill_plan"
        filepath = filedialog.asksaveasfilename(
            initialdir=str(self.plans_dir),
            initialfile=f"{name}.txt",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save Skill Plan",
            parent=self
        )
        if filepath:
            lines = [f"{s['name']} {s['level']}" for s in self.plan_skills]
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            messagebox.showinfo("Saved", f"Plan saved to:\n{filepath}", parent=self)

    def _import_clipboard(self):
        """Import skills from clipboard in EVE format: 'Skill Name Level'"""
        try:
            text = self.clipboard_get()
        except tk.TclError:
            messagebox.showwarning("Warning", "Clipboard is empty", parent=self)
            return

        if not self.current_plan_name:
            name = simpledialog.askstring("Import", "Create a plan name for imported skills:", parent=self)
            if not name or not name.strip():
                return
            self.current_plan_name = name.strip()
            self.plan_skills = []

        imported = 0
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            # Parse "Skill Name Level" - the last token is the level
            parts = line.rsplit(" ", 1)
            if len(parts) == 2:
                name_part = parts[0].strip()
                try:
                    level = int(parts[1])
                    if 1 <= level <= 5:
                        exists = any(s["name"] == name_part and s["level"] == level for s in self.plan_skills)
                        if not exists:
                            self.plan_skills.append({"name": name_part, "level": level})
                            imported += 1
                except ValueError:
                    continue

        self._save_plan()
        self._load_plan_list()
        self._refresh_plan_tree()
        messagebox.showinfo("Imported", f"Imported {imported} skill entries.", parent=self)
