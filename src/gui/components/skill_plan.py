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
from src.ui.tooltip import Tooltip, TreeviewTooltip
from src.data.skill_descriptions import get_skill_description
from src.ui.theme_eve import BG_MAIN, BG_PANEL, BG_SIDEBAR, BORDER, BORDER_LIGHT, \
    FG_DEFAULT, FG_BRIGHT, FG_TEAL, FG_DIM


class SkillPlanManager(tk.Toplevel):
    """A separate window for creating and managing skill training plans."""

    def __init__(self, parent, current_skills=None):
        super().__init__(parent)
        self.parent_app = parent
        self.title("Skill Plan Manager")
        self.geometry("1050x680")
        self.minsize(850, 520)
        self.configure(bg=BG_MAIN)

        self.current_skills = current_skills or []
        self.plans_dir = PathManager.get_app_data_dir() / "skill_plans"
        self.plans_dir.mkdir(exist_ok=True)
        self.current_plan_name = None
        self.plan_skills = []  # list of {"name": str, "level": int}

        self._build_skill_catalog()
        self._setup_ui()
        self._load_plan_list()

        self.transient(parent)
        self.focus_set()

    def _build_skill_catalog(self):
        """Build a sorted list of all skills from the database."""
        self.all_skills = {}
        for sid, (name, group, category) in skills_db.SKILLS.items():
            if name == str(sid):
                continue
            self.all_skills[name] = {
                "skill_id": sid,
                "name": name,
                "group": group,
                "category": category
            }

    def _setup_ui(self):
        # ── Top bar ──
        top = tk.Frame(self, bg=BG_PANEL)
        top.pack(fill=tk.X)
        tk.Label(top, text="⚙  Skill Plan Manager",
                 font=("Segoe UI", 14, "bold"),
                 fg=FG_BRIGHT, bg=BG_PANEL).pack(side=tk.LEFT, padx=15, pady=12)
        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X)

        # ── 3-column PanedWindow (all resizable) ──
        self.col_pw = tk.PanedWindow(self, orient=tk.HORIZONTAL,
                                     sashwidth=4,
                                     sashrelief=tk.FLAT,
                                     bg=BORDER_LIGHT,
                                     borderwidth=0,
                                     opaqueresize=True)
        self.col_pw.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # === Column 1: Saved Plans ===
        col1 = tk.Frame(self.col_pw, bg=BG_MAIN)

        tk.Label(col1, text="SAVED PLANS",
                 font=("Segoe UI", 8, "bold"), fg=FG_DIM,
                 bg=BG_MAIN, anchor="w").pack(padx=6, pady=(6, 4))

        self.plan_listbox = tk.Listbox(col1, font=("Segoe UI", 10),
                                        bg="#161a24", fg=FG_DEFAULT,
                                        selectbackground=BG_SIDEBAR,
                                        selectforeground=FG_BRIGHT,
                                        borderwidth=0, highlightthickness=0,
                                        activestyle="none")
        self.plan_listbox.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.plan_listbox.bind("<<ListboxSelect>>", self._on_plan_select)
        Tooltip(self.plan_listbox,
                "Your saved skill plans.\n"
                "Click a plan to load it into the editor.")

        btn_row1 = tk.Frame(col1, bg=BG_MAIN)
        btn_row1.pack(fill=tk.X, padx=4, pady=(0, 6))

        b_new = ttk.Button(btn_row1, text="＋ New", command=self._new_plan, width=8)
        b_new.pack(side=tk.LEFT, padx=2)
        Tooltip(b_new, "Create a new empty skill plan.")

        b_ren = ttk.Button(btn_row1, text="✎ Rename", command=self._rename_plan, width=9)
        b_ren.pack(side=tk.LEFT, padx=2)
        Tooltip(b_ren, "Rename the selected plan.")

        b_del = ttk.Button(btn_row1, text="✕ Delete", command=self._delete_plan, width=9)
        b_del.pack(side=tk.LEFT, padx=2)
        Tooltip(b_del, "Delete the selected plan permanently.")

        # === Column 2: Skill Catalog ===
        col2 = tk.Frame(self.col_pw, bg=BG_MAIN)

        tk.Label(col2, text="SKILL CATALOG",
                 font=("Segoe UI", 8, "bold"), fg=FG_DIM,
                 bg=BG_MAIN, anchor="w").pack(padx=6, pady=(6, 4))

        # Search + filter
        search_bar = tk.Frame(col2, bg=BG_MAIN)
        search_bar.pack(fill=tk.X, padx=4, pady=(0, 4))

        tk.Label(search_bar, text="Search:", font=("Segoe UI", 9),
                 fg=FG_DIM, bg=BG_MAIN).pack(side=tk.LEFT, padx=(0, 4))
        self.catalog_search_var = tk.StringVar()
        self.catalog_search_var.trace_add("write", lambda *a: self._filter_catalog())
        search_entry = ttk.Entry(search_bar, textvariable=self.catalog_search_var, width=18)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        Tooltip(search_entry, "Type to filter skills by name.\nMatches any part of the skill name.")

        tk.Label(search_bar, text="  Group:", font=("Segoe UI", 9),
                 fg=FG_DIM, bg=BG_MAIN).pack(side=tk.LEFT, padx=(6, 4))
        self.catalog_group_var = tk.StringVar(value="All")
        groups = sorted(set(s["group"] for s in self.all_skills.values()))
        group_cb = ttk.Combobox(search_bar, textvariable=self.catalog_group_var,
                                state="readonly", values=["All"] + groups, width=16)
        group_cb.pack(side=tk.LEFT, padx=2)
        group_cb.bind("<<ComboboxSelected>>", lambda e: self._filter_catalog())
        Tooltip(group_cb, "Filter the catalog by skill group\n(e.g. Spaceship Command, Drones, etc.).")

        # Catalog treeview
        cat_frame = tk.Frame(col2, bg=BG_MAIN)
        cat_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        self.catalog_tree = ttk.Treeview(cat_frame,
                                          columns=("name", "group", "category"),
                                          show="headings", height=15)
        self.catalog_tree.heading("name", text="Skill Name")
        self.catalog_tree.heading("group", text="Group")
        self.catalog_tree.heading("category", text="Category")
        self.catalog_tree.column("name", width=180, minwidth=100)
        self.catalog_tree.column("group", width=130, minwidth=80)
        self.catalog_tree.column("category", width=80, minwidth=60)

        cat_scroll = ttk.Scrollbar(cat_frame, orient=tk.VERTICAL,
                                   command=self.catalog_tree.yview)
        self.catalog_tree.configure(yscrollcommand=cat_scroll.set)
        self.catalog_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cat_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Skill description tooltip on row hover
        def _cat_tip(values):
            if not values:
                return None
            skill_name = str(values[0])
            desc = get_skill_description(skill_name)
            if desc:
                return (skill_name, desc)
            return None

        TreeviewTooltip(self.catalog_tree, _cat_tip)

        # Level + Add buttons
        add_bar = tk.Frame(col2, bg=BG_MAIN)
        add_bar.pack(fill=tk.X, padx=4, pady=(0, 6))

        tk.Label(add_bar, text="Level:", font=("Segoe UI", 9),
                 fg=FG_DIM, bg=BG_MAIN).pack(side=tk.LEFT, padx=(0, 4))
        self.add_level_var = tk.IntVar(value=5)
        level_spin = ttk.Spinbox(add_bar, from_=1, to=5,
                                  textvariable=self.add_level_var,
                                  width=4, state="readonly")
        level_spin.pack(side=tk.LEFT, padx=(0, 8))
        Tooltip(level_spin, "Target skill level (1-5).")

        b_add = ttk.Button(add_bar, text="→ Add to Plan",
                           style="Accent.TButton", command=self._add_to_plan)
        b_add.pack(side=tk.LEFT, padx=4)
        Tooltip(b_add, "Add the selected skill at the\nchosen level to the current plan.")

        b_add5 = ttk.Button(add_bar, text="→ Add 1→5",
                            style="Accent.TButton", command=self._add_range_to_plan)
        b_add5.pack(side=tk.LEFT, padx=4)
        Tooltip(b_add5, "Add the selected skill at levels\n1 through 5 to the plan.")

        # === Column 3: Current Plan ===
        col3 = tk.Frame(self.col_pw, bg=BG_MAIN)

        tk.Label(col3, text="CURRENT PLAN",
                 font=("Segoe UI", 8, "bold"), fg=FG_DIM,
                 bg=BG_MAIN, anchor="w").pack(padx=6, pady=(6, 4))

        plan_frame = tk.Frame(col3, bg=BG_MAIN)
        plan_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        self.plan_tree = ttk.Treeview(plan_frame,
                                       columns=("name", "level"),
                                       show="headings", height=15)
        self.plan_tree.heading("name", text="Skill Name")
        self.plan_tree.heading("level", text="Lvl")
        self.plan_tree.column("name", width=200, minwidth=120)
        self.plan_tree.column("level", width=50, minwidth=35, anchor=tk.CENTER)

        plan_scroll = ttk.Scrollbar(plan_frame, orient=tk.VERTICAL,
                                    command=self.plan_tree.yview)
        self.plan_tree.configure(yscrollcommand=plan_scroll.set)
        self.plan_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        plan_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        Tooltip(self.plan_tree,
                "Skills in the current training plan.\n"
                "Use ↑/↓ to reorder, ✕ to remove.")

        # Reorder / remove controls
        ctrl_bar = tk.Frame(col3, bg=BG_MAIN)
        ctrl_bar.pack(fill=tk.X, padx=4, pady=(0, 4))

        b_up = ttk.Button(ctrl_bar, text="↑", command=self._move_up, width=3)
        b_up.pack(side=tk.LEFT, padx=2)
        Tooltip(b_up, "Move selected skill up in the plan.")

        b_dn = ttk.Button(ctrl_bar, text="↓", command=self._move_down, width=3)
        b_dn.pack(side=tk.LEFT, padx=2)
        Tooltip(b_dn, "Move selected skill down in the plan.")

        b_rm = ttk.Button(ctrl_bar, text="✕ Remove", command=self._remove_from_plan, width=9)
        b_rm.pack(side=tk.LEFT, padx=5)
        Tooltip(b_rm, "Remove selected skill from the plan.")

        b_cl = ttk.Button(ctrl_bar, text="Clear All", command=self._clear_plan, width=8)
        b_cl.pack(side=tk.LEFT, padx=2)
        Tooltip(b_cl, "Remove all skills from the current plan.")

        # Export bar
        export_bar = tk.Frame(col3, bg=BG_MAIN)
        export_bar.pack(fill=tk.X, padx=4, pady=(0, 6))

        b_clip = ttk.Button(export_bar, text="📋 Copy to Clipboard",
                            style="Accent.TButton", command=self._export_clipboard)
        b_clip.pack(side=tk.LEFT, padx=2)
        Tooltip(b_clip, "Copy the plan to clipboard in EVE format:\n"
                "\"Skill Name Level\"\n\n"
                "Paste into EVE Online → Character Sheet →\n"
                "Skill Queue → Import.")

        b_txt = ttk.Button(export_bar, text="💾 Save as TXT",
                           style="Accent.TButton", command=self._export_txt)
        b_txt.pack(side=tk.LEFT, padx=2)
        Tooltip(b_txt, "Save the plan as a .txt file\nin EVE-importable format.")

        b_imp = ttk.Button(export_bar, text="📂 Import from Clipboard",
                           command=self._import_clipboard)
        b_imp.pack(side=tk.LEFT, padx=2)
        Tooltip(b_imp, "Import skills from clipboard.\n"
                "Expects EVE format: \"Skill Name Level\"\n"
                "(one per line).")

        # ── Add columns to PanedWindow ──
        self.col_pw.add(col1, minsize=150, width=200)
        self.col_pw.add(col2, minsize=250, width=420)
        self.col_pw.add(col3, minsize=200, width=380)

        # Populate catalog
        self._filter_catalog()

    # ── Catalog ──────────────────────────────────────────
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
            self.catalog_tree.insert("", tk.END,
                                     values=(name, info["group"], info["category"]))

    # ── Plan list ────────────────────────────────────────
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

    # ── Plan CRUD ────────────────────────────────────────
    def _new_plan(self):
        name = simpledialog.askstring("New Plan", "Plan name:", parent=self)
        if name and name.strip():
            name = name.strip()
            self.current_plan_name = name
            self.plan_skills = []
            self._save_plan()
            self._load_plan_list()
            self._refresh_plan_tree()
            for i in range(self.plan_listbox.size()):
                if self.plan_listbox.get(i).strip() == name:
                    self.plan_listbox.selection_set(i)
                    break

    def _rename_plan(self):
        if not self.current_plan_name:
            messagebox.showinfo("Info", "Select a plan first")
            return
        new_name = simpledialog.askstring("Rename Plan", "New name:",
                                          initialvalue=self.current_plan_name,
                                          parent=self)
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
        if messagebox.askyesno("Confirm",
                               f"Delete plan '{self.current_plan_name}'?",
                               parent=self):
            path = self.plans_dir / f"{self.current_plan_name}.json"
            if path.exists():
                path.unlink()
            self.current_plan_name = None
            self.plan_skills = []
            self._load_plan_list()
            self._refresh_plan_tree()

    # ── Add skills ───────────────────────────────────────
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
            exists = any(s["name"] == name and s["level"] == level
                         for s in self.plan_skills)
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
                exists = any(s["name"] == name and s["level"] == lvl
                             for s in self.plan_skills)
                if not exists:
                    self.plan_skills.append({"name": name, "level": lvl})
        self._save_plan()
        self._refresh_plan_tree()

    # ── Modify plan ──────────────────────────────────────
    def _remove_from_plan(self):
        sel = self.plan_tree.selection()
        if not sel:
            return
        indices = sorted([self.plan_tree.index(i) for i in sel], reverse=True)
        for idx in indices:
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
            self.plan_skills[idx], self.plan_skills[idx - 1] = \
                self.plan_skills[idx - 1], self.plan_skills[idx]
            self._save_plan()
            self._refresh_plan_tree()
            children = self.plan_tree.get_children()
            if children:
                self.plan_tree.selection_set(children[idx - 1])

    def _move_down(self):
        sel = self.plan_tree.selection()
        if not sel:
            return
        idx = self.plan_tree.index(sel[0])
        if idx < len(self.plan_skills) - 1:
            self.plan_skills[idx], self.plan_skills[idx + 1] = \
                self.plan_skills[idx + 1], self.plan_skills[idx]
            self._save_plan()
            self._refresh_plan_tree()
            children = self.plan_tree.get_children()
            if children:
                self.plan_tree.selection_set(children[idx + 1])

    def _clear_plan(self):
        if not self.plan_skills:
            return
        if messagebox.askyesno("Confirm", "Clear all skills from this plan?",
                               parent=self):
            self.plan_skills = []
            self._save_plan()
            self._refresh_plan_tree()

    # ── Export / Import ──────────────────────────────────
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
                            "You can paste this directly into EVE Online's\n"
                            "skill queue import.",
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
            parent=self)
        if filepath:
            lines = [f"{s['name']} {s['level']}" for s in self.plan_skills]
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            messagebox.showinfo("Saved", f"Plan saved to:\n{filepath}",
                                parent=self)

    def _import_clipboard(self):
        """Import skills from clipboard in EVE format: 'Skill Name Level'"""
        try:
            text = self.clipboard_get()
        except tk.TclError:
            messagebox.showwarning("Warning", "Clipboard is empty", parent=self)
            return

        if not self.current_plan_name:
            name = simpledialog.askstring("Import",
                                          "Create a plan name for imported skills:",
                                          parent=self)
            if not name or not name.strip():
                return
            self.current_plan_name = name.strip()
            self.plan_skills = []

        imported = 0
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.rsplit(" ", 1)
            if len(parts) == 2:
                name_part = parts[0].strip()
                try:
                    level = int(parts[1])
                    if 1 <= level <= 5:
                        exists = any(s["name"] == name_part and s["level"] == level
                                     for s in self.plan_skills)
                        if not exists:
                            self.plan_skills.append({"name": name_part,
                                                     "level": level})
                            imported += 1
                except ValueError:
                    continue

        self._save_plan()
        self._load_plan_list()
        self._refresh_plan_tree()
        messagebox.showinfo("Imported",
                            f"Imported {imported} skill entries.",
                            parent=self)
