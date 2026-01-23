from datetime import datetime
import tkinter as tk
from tkinter import ttk
from src.data import skills_db

class QueueView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.queue = []
        self._setup_ui()

    def _setup_ui(self):
        header_frame = ttk.Frame(self, style="Toolbar.TFrame")
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        ttk.Label(header_frame, text="Skill Queue", style="Header.TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        
        self.tree_container = ttk.Frame(self)
        self.tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(self.tree_container, columns=("pos", "name", "category", "level", "finish", "time_left"), show="headings")
        self.tree.heading("pos", text="#", command=lambda: self._sort_column("pos", False))
        self.tree.heading("name", text="Skill", command=lambda: self._sort_column("name", False))
        self.tree.heading("category", text="Category", command=lambda: self._sort_column("category", False))
        self.tree.heading("level", text="To Level", command=lambda: self._sort_column("level", False))
        self.tree.heading("finish", text="Finish Date (UTC)", command=lambda: self._sort_column("finish", False))
        self.tree.heading("time_left", text="Time Left", command=lambda: self._sort_column("time_left", False))
        
        self.tree.column("pos", width=40, anchor=tk.CENTER)
        self.tree.column("name", width=250)
        self.tree.column("category", width=120)
        self.tree.column("level", width=80, anchor=tk.CENTER)
        self.tree.column("finish", width=150)
        self.tree.column("time_left", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(self.tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def set_queue(self, queue_data):
        self.queue = queue_data
        self.tree.delete(*self.tree.get_children())
        
        now = datetime.utcnow()
        
        for q in self.queue:
            skill_id = q.get("skill_id")
            pos = q.get("queue_position", 0)
            name = skills_db.get_skill_name(skill_id)
            category = skills_db.get_skill_category(skill_id) or "Other"
            level = q.get("finished_level", 0)
            
            finish_raw = q.get("finish_date")
            finish_str = "N/A"
            time_left_str = "N/A"
            
            if finish_raw:
                try:
                    # ESI dates are like "2023-10-27T12:34:56Z"
                    finish_dt = datetime.strptime(finish_raw.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
                    finish_str = finish_dt.strftime("%Y-%m-%d %H:%M")
                    
                    diff = finish_dt - now
                    if diff.total_seconds() <= 0:
                        time_left_str = "Completed"
                    else:
                        days = diff.days
                        hours, rem = divmod(diff.seconds, 3600)
                        minutes, _ = divmod(rem, 60)
                        
                        parts = []
                        if days > 0: parts.append(f"{days}d")
                        if hours > 0: parts.append(f"{hours}h")
                        if minutes > 0: parts.append(f"{minutes}m")
                        time_left_str = " ".join(parts) if parts else "< 1m"
                except Exception:
                    finish_str = finish_raw

            self.tree.insert("", tk.END, values=(pos, name, category, level, finish_str, time_left_str))

    def _sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        
        # Handle numeric sorting
        if col in ("pos", "level"):
            l.sort(key=lambda t: int(t[0]), reverse=reverse)
        elif col == "finish":
            l.sort(key=lambda t: t[0], reverse=reverse) # YYYY-MM-DD sort works naturally
        else:
            l.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, "", index)

        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))
