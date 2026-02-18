import tkinter as tk
from tkinter import ttk
from src.data import skills_db
from src.data.skill_descriptions import get_skill_description
from src.ui.tooltip import Tooltip, TreeviewTooltip

try:
    from rapidfuzz import fuzz as _fuzz
    _FUZZY_AVAILABLE = True
except ImportError:
    _FUZZY_AVAILABLE = False


class SkillView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.skills = []
        self._setup_ui()

    def _setup_ui(self):
        # ── Filter Bar ──────────────────────────────────────────
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=10, pady=(10, 4))

        # Row 0: Search + Group + Category + checkboxes
        # Search
        ttk.Label(filter_frame, text="Search:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_skills())
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=25)
        search_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        Tooltip(search_entry,
                "Type to filter skills by name.\n"
                "Supports fuzzy/partial matching — e.g. 'dron' finds 'Drones'." if _FUZZY_AVAILABLE
                else "Type to filter skills by name.")

        # Group
        ttk.Label(filter_frame, text="Group:").grid(row=0, column=2, padx=(15, 5), sticky=tk.W)
        self.group_var = tk.StringVar(value="All")
        self.group_cb = ttk.Combobox(filter_frame, textvariable=self.group_var,
                                     state="readonly", width=22)
        self.group_cb.grid(row=0, column=3, padx=5, sticky=tk.W)
        self.group_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_skills())
        Tooltip(self.group_cb, "Filter by skill group\n(e.g. Gunnery, Missiles, Drones).")

        # Category
        ttk.Label(filter_frame, text="Category:").grid(row=0, column=4, padx=(15, 5), sticky=tk.W)
        self.cat_var = tk.StringVar(value="All")
        self.cat_cb = ttk.Combobox(filter_frame, textvariable=self.cat_var, state="readonly",
                                   values=["All", "Combat", "Industry", "Resource",
                                           "Support", "Other"],
                                   width=12)
        self.cat_cb.grid(row=0, column=5, padx=5, sticky=tk.W)
        self.cat_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_skills())
        Tooltip(self.cat_cb, "Filter by skill category:\nCombat, Industry, Resource, Support.")

        # Level filter
        ttk.Label(filter_frame, text="Level ≥:").grid(row=0, column=6, padx=(15, 5), sticky=tk.W)
        self.level_filter_var = tk.StringVar(value="Any")
        level_cb = ttk.Combobox(filter_frame, textvariable=self.level_filter_var,
                                state="readonly",
                                values=["Any", "1", "2", "3", "4", "5"],
                                width=5)
        level_cb.grid(row=0, column=7, padx=5, sticky=tk.W)
        level_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_skills())
        Tooltip(level_cb, "Show only skills at or above this level.\n"
                          "e.g. '≥ 4' shows skills trained to level 4 or 5.")

        # Checkboxes
        check_frame = ttk.Frame(filter_frame)
        check_frame.grid(row=0, column=8, sticky=tk.W, padx=(20, 0))

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

        filter_frame.columnconfigure(8, weight=1)

        # ── Fuzzy status label ───────────────────────────────────
        if _FUZZY_AVAILABLE:
            self._fuzzy_label_var = tk.StringVar(value="")
            ttk.Label(self, textvariable=self._fuzzy_label_var,
                      foreground="#888888").pack(anchor=tk.W, padx=12, pady=(0, 2))
        else:
            self._fuzzy_label_var = None

        # ── Treeview ─────────────────────────────────────────────
        self.tree_container = ttk.Frame(self)
        self.tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(self.tree_container,
                                 columns=("id", "name", "group", "level", "sp"),
                                 show="headings")
        self.tree.heading("id",    text="ID",         command=lambda: self._sort_column("id", False))
        self.tree.heading("name",  text="Skill Name", command=lambda: self._sort_column("name", False))
        self.tree.heading("group", text="Group",      command=lambda: self._sort_column("group", False))
        self.tree.heading("level", text="Level",      command=lambda: self._sort_column("level", False))
        self.tree.heading("sp",    text="Skillpoints", command=lambda: self._sort_column("sp", False))

        self.tree.column("id",    width=60,  anchor=tk.CENTER)
        self.tree.column("name",  width=280)
        self.tree.column("group", width=200)
        self.tree.column("level", width=60,  anchor=tk.CENTER)
        self.tree.column("sp",    width=120, anchor=tk.E)

        scrollbar = ttk.Scrollbar(self.tree_container, orient=tk.VERTICAL,
                                  command=self.tree.yview)
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

    # ── Data ─────────────────────────────────────────────────────
    def set_skills(self, skills_data):
        self.skills = []
        groups = set()
        for s in skills_data:
            skill_id = s.get("skill_id")
            s["name"]        = skills_db.get_skill_name(skill_id)
            s["group"]       = skills_db.get_skill_group(skill_id) or "Unknown"
            s["category"]    = skills_db.get_skill_category(skill_id) or "Other"
            s["is_injected"] = s.get("trained_skill_level", 0) == 0
            self.skills.append(s)
            if s["group"] != "Unknown":
                groups.add(s["group"])

        self.group_cb["values"] = ["All"] + sorted(list(groups))
        self.filter_skills()

    # ── Filtering ────────────────────────────────────────────────
    def filter_skills(self):
        search_term    = self.search_var.get().strip()
        search_lower   = search_term.lower()
        selected_group = self.group_var.get()
        selected_cat   = self.cat_var.get()
        trained_only   = self.trained_only_var.get()
        show_level_0   = self.show_level_0_var.get()
        level_filter   = self.level_filter_var.get()
        min_level      = int(level_filter) if level_filter != "Any" else None

        # Decide whether to use fuzzy matching
        use_fuzzy = _FUZZY_AVAILABLE and len(search_term) >= 2
        FUZZY_THRESHOLD = 72  # 0-100; lower = more permissive

        self.tree.delete(*self.tree.get_children())
        shown = 0

        for s in self.skills:
            name     = s.get("name", str(s.get("skill_id")))
            group    = s.get("group", "Unknown")
            category = s.get("category", "Other")
            level    = s.get("trained_skill_level", 0)
            sp       = s.get("skillpoints_in_skill", 0)
            skill_id = s.get("skill_id")

            # ── Search filter ──
            if search_term:
                if use_fuzzy:
                    score = _fuzz.partial_ratio(search_lower, name.lower())
                    if score < FUZZY_THRESHOLD:
                        continue
                else:
                    if search_lower not in name.lower():
                        continue

            # ── Group / Category filters ──
            if selected_group != "All" and group != selected_group:
                continue
            if selected_cat != "All" and category != selected_cat:
                continue

            # ── Level filters ──
            if level == 0:
                if trained_only:
                    continue
                if not show_level_0:
                    continue

            if trained_only and level < 1:
                continue

            if min_level is not None and level < min_level:
                continue

            self.tree.insert("", tk.END,
                             values=(skill_id, name, group, level, f"{sp:,}"))
            shown += 1

        # Update fuzzy status label
        if self._fuzzy_label_var is not None:
            if use_fuzzy and search_term:
                self._fuzzy_label_var.set(
                    f"🔍 Fuzzy search active — {shown} result(s) for \"{search_term}\"")
            else:
                self._fuzzy_label_var.set("")

    # ── Helpers ──────────────────────────────────────────────────
    def _get_filtered_skills(self):
        """Returns the list of skills currently shown in the treeview."""
        filtered = []
        for child in self.tree.get_children():
            values = self.tree.item(child)["values"]
            filtered.append({
                "skill_id":            values[0],
                "name":                values[1],
                "group":               values[2],
                "trained_skill_level": int(values[3]),
                "skillpoints_in_skill": int(str(values[4]).replace(",", ""))
            })
        return filtered

    def _sort_column(self, col, reverse):
        rows = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]

        if col in ("id", "level", "sp"):
            def sort_key(t):
                try:
                    return float(str(t[0]).replace(",", ""))
                except ValueError:
                    return 0
            rows.sort(key=sort_key, reverse=reverse)
        else:
            rows.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)

        for index, (val, k) in enumerate(rows):
            self.tree.move(k, "", index)

        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))
