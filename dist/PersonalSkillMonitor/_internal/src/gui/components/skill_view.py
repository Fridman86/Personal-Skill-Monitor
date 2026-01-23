import tkinter as tk
from tkinter import ttk
from src.data import skills_db

class SkillView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.skills = []
        self._setup_ui()

    def _setup_ui(self):
        # Filter Bar (Polished)
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=10, pady=(10, 15))

        # Search
        ttk.Label(filter_frame, text="Search:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_skills())
        ttk.Entry(filter_frame, textvariable=self.search_var, width=25).grid(row=0, column=1, sticky=tk.W, padx=5)

        # Dropdowns
        ttk.Label(filter_frame, text="Group:").grid(row=0, column=2, padx=(15, 5), sticky=tk.W)
        self.group_var = tk.StringVar(value="All")
        self.group_cb = ttk.Combobox(filter_frame, textvariable=self.group_var, state="readonly", width=22)
        self.group_cb.grid(row=0, column=3, padx=5, sticky=tk.W)
        self.group_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_skills())

        ttk.Label(filter_frame, text="Category:").grid(row=0, column=4, padx=(15, 5), sticky=tk.W)
        self.cat_var = tk.StringVar(value="All")
        self.cat_cb = ttk.Combobox(filter_frame, textvariable=self.cat_var, state="readonly", 
                                   values=["All", "Combat", "Industry", "Resource", "Support", "Other"], width=12)
        self.cat_cb.grid(row=0, column=5, padx=5, sticky=tk.W)
        self.cat_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_skills())

        # Checkboxes
        check_frame = ttk.Frame(filter_frame)
        check_frame.grid(row=0, column=6, sticky=tk.W, padx=(20, 0))

        self.trained_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(check_frame, text="Only trained", variable=self.trained_only_var, 
                        command=self.filter_skills).pack(side=tk.LEFT, padx=(0, 15))

        self.show_level_0_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(check_frame, text="Level 0", variable=self.show_level_0_var, 
                        command=self.filter_skills).pack(side=tk.LEFT, padx=(0, 15))

        filter_frame.columnconfigure(6, weight=1)

        # Treeview
        self.tree_container = ttk.Frame(self)
        self.tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(self.tree_container, columns=("id", "name", "group", "category", "level", "sp"), show="headings")
        self.tree.heading("id", text="ID", command=lambda: self._sort_column("id", False))
        self.tree.heading("name", text="Skill Name", command=lambda: self._sort_column("name", False))
        self.tree.heading("group", text="Group", command=lambda: self._sort_column("group", False))
        self.tree.heading("category", text="Category", command=lambda: self._sort_column("category", False))
        self.tree.heading("level", text="Level", command=lambda: self._sort_column("level", False))
        self.tree.heading("sp", text="Skillpoints", command=lambda: self._sort_column("sp", False))
        
        self.tree.column("id", width=70, anchor=tk.CENTER)
        self.tree.column("name", width=300)
        self.tree.column("group", width=180)
        self.tree.column("category", width=120)
        self.tree.column("level", width=60, anchor=tk.CENTER)
        self.tree.column("sp", width=110, anchor=tk.E)

        scrollbar = ttk.Scrollbar(self.tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def set_skills(self, skills_data):
        self.skills = []
        groups = set()
        for s in skills_data:
            skill_id = s.get("skill_id")
            s["name"] = skills_db.get_skill_name(skill_id)
            s["group"] = skills_db.get_skill_group(skill_id) or "Unknown"
            s["category"] = skills_db.get_skill_category(skill_id) or "Other"
            
            # Heuristic for injected but untrained:
            # If level is 0 but it's in the character's skills list, it's injected.
            s["is_injected"] = s.get("trained_skill_level", 0) == 0
            
            self.skills.append(s)
            if s["group"] != "Unknown":
                groups.add(s["group"])
        
        # Update group dropdown
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
            
            # Combine filters
            if search_term and search_term not in name.lower():
                continue
            if selected_group != "All" and group != selected_group:
                continue
            if selected_cat != "All" and category != selected_cat:
                continue
            
            # Level 0 logic
            if level == 0:
                # If only trained is ON, always hide level 0
                if trained_only:
                    continue
                # If only trained is OFF, use show_level_0 checkbox
                if not show_level_0:
                    continue
            
            # If "Only trained" is ON, we must show only level >= 1
            # (level == 0 is already handled above, but this is a safeguard)
            if trained_only and level < 1:
                continue
            
            self.tree.insert("", tk.END, values=(skill_id, name, group, category, level, f"{sp:,}"))

    def _get_filtered_skills(self):
        """Returns the list of skills currently shown in the treeview (as dicts)."""
        filtered = []
        for child in self.tree.get_children():
            values = self.tree.item(child)["values"]
            # Convert back to dict format expected by export
            filtered.append({
                "skill_id": values[0],
                "name": values[1],
                "group": values[2],
                "category": values[3],
                "trained_skill_level": int(values[4]),
                "skillpoints_in_skill": int(str(values[5]).replace(",", ""))
            })
        return filtered

    def _sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        
        # Handle numeric sorting
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
