import tkinter as tk
from tkinter import ttk
from src.data import skills_db
from src.data.skill_descriptions import get_skill_description
from src.ui.tooltip import Tooltip, TreeviewTooltip

class SkillView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.skills = []
        self._setup_ui()

    def _setup_ui(self):
        # Filter Bar
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=10, pady=(10, 15))

        # Search
        ttk.Label(filter_frame, text="Search:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_skills())
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=25)
        search_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        Tooltip(search_entry, "Type to filter skills by name.\nMatches any part of the skill name.")

        # Group
        ttk.Label(filter_frame, text="Group:").grid(row=0, column=2, padx=(15, 5), sticky=tk.W)
        self.group_var = tk.StringVar(value="All")
        self.group_cb = ttk.Combobox(filter_frame, textvariable=self.group_var, state="readonly", width=22)
        self.group_cb.grid(row=0, column=3, padx=5, sticky=tk.W)
        self.group_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_skills())
        Tooltip(self.group_cb, "Filter by skill group\n(e.g. Gunnery, Missiles, Drones).")

        # Category (filter only, not shown in table)
        ttk.Label(filter_frame, text="Category:").grid(row=0, column=4, padx=(15, 5), sticky=tk.W)
        self.cat_var = tk.StringVar(value="All")
        self.cat_cb = ttk.Combobox(filter_frame, textvariable=self.cat_var, state="readonly",
                                   values=["All", "Combat", "Industry", "Resource", "Support", "Other"], width=12)
        self.cat_cb.grid(row=0, column=5, padx=5, sticky=tk.W)
        self.cat_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_skills())
        Tooltip(self.cat_cb, "Filter by skill category:\nCombat, Industry, Resource, Support.")

        # Checkboxes
        check_frame = ttk.Frame(filter_frame)
        check_frame.grid(row=0, column=6, sticky=tk.W, padx=(20, 0))

        self.trained_only_var = tk.BooleanVar(value=False)
        cb_trained = ttk.Checkbutton(check_frame, text="Only trained",
                                     variable=self.trained_only_var,
                                     command=self.filter_skills)
        cb_trained.pack(side=tk.LEFT, padx=(0, 15))
        Tooltip(cb_trained, "Show only skills with level ≥ 1.\nHides injected but untrained skills.")

        self.show_level_0_var = tk.BooleanVar(value=True)
        cb_lv0 = ttk.Checkbutton(check_frame, text="Level 0",
                                 variable=self.show_level_0_var,
                                 command=self.filter_skills)
        cb_lv0.pack(side=tk.LEFT, padx=(0, 15))
        Tooltip(cb_lv0, "Show/hide skills at level 0\n(injected but not yet trained).")

        filter_frame.columnconfigure(6, weight=1)

        # Treeview (no Category column)
        self.tree_container = ttk.Frame(self)
        self.tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(self.tree_container,
                                 columns=("id", "name", "group", "level", "sp"),
                                 show="headings")
        self.tree.heading("id", text="ID", command=lambda: self._sort_column("id", False))
        self.tree.heading("name", text="Skill Name", command=lambda: self._sort_column("name", False))
        self.tree.heading("group", text="Group", command=lambda: self._sort_column("group", False))
        self.tree.heading("level", text="Level", command=lambda: self._sort_column("level", False))
        self.tree.heading("sp", text="Skillpoints", command=lambda: self._sort_column("sp", False))

        self.tree.column("id", width=60, anchor=tk.CENTER)
        self.tree.column("name", width=280)
        self.tree.column("group", width=200)
        self.tree.column("level", width=60, anchor=tk.CENTER)
        self.tree.column("sp", width=120, anchor=tk.E)

        scrollbar = ttk.Scrollbar(self.tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Skill description tooltip on row hover
        def _skill_tip(values):
            if not values or len(values) < 2:
                return None
            skill_name = str(values[1])
            desc = get_skill_description(skill_name)
            if desc:
                return (skill_name, desc)
            return None

        TreeviewTooltip(self.tree, _skill_tip)

    def set_skills(self, skills_data):
        self.skills = []
        groups = set()
        for s in skills_data:
            skill_id = s.get("skill_id")
            s["name"] = skills_db.get_skill_name(skill_id)
            s["group"] = skills_db.get_skill_group(skill_id) or "Unknown"
            s["category"] = skills_db.get_skill_category(skill_id) or "Other"
            s["is_injected"] = s.get("trained_skill_level", 0) == 0
            self.skills.append(s)
            if s["group"] != "Unknown":
                groups.add(s["group"])

        self.group_cb["values"] = ["All"] + sorted(list(groups))
        self.filter_skills()

    def filter_skills(self):
        search_term = self.search_var.get().lower()
        selected_group = self.group_var.get()
        selected_cat = self.cat_var.get()
        trained_only = self.trained_only_var.get()
        show_level_0 = self.show_level_0_var.get()

        self.tree.delete(*self.tree.get_children())

        for s in self.skills:
            name = s.get("name", str(s.get("skill_id")))
            group = s.get("group", "Unknown")
            category = s.get("category", "Other")
            level = s.get("trained_skill_level", 0)
            sp = s.get("skillpoints_in_skill", 0)
            skill_id = s.get("skill_id")

            if search_term and search_term not in name.lower():
                continue
            if selected_group != "All" and group != selected_group:
                continue
            if selected_cat != "All" and category != selected_cat:
                continue

            if level == 0:
                if trained_only:
                    continue
                if not show_level_0:
                    continue

            if trained_only and level < 1:
                continue

            self.tree.insert("", tk.END,
                             values=(skill_id, name, group, level, f"{sp:,}"))

    def _get_filtered_skills(self):
        """Returns the list of skills currently shown in the treeview."""
        filtered = []
        for child in self.tree.get_children():
            values = self.tree.item(child)["values"]
            filtered.append({
                "skill_id": values[0],
                "name": values[1],
                "group": values[2],
                "trained_skill_level": int(values[3]),
                "skillpoints_in_skill": int(str(values[4]).replace(",", ""))
            })
        return filtered

    def _sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]

        if col in ("id", "level", "sp"):
            def sort_key(t):
                try:
                    return float(str(t[0]).replace(",", ""))
                except ValueError:
                    return 0
            l.sort(key=sort_key, reverse=reverse)
        else:
            l.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, "", index)

        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))
