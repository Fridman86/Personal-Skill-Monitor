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
        
        # Training Speed Display
        self.sp_min_var = tk.StringVar(value="")
        ttk.Label(header_frame, textvariable=self.sp_min_var, font=("Segoe UI", 9, "italic")).pack(side=tk.RIGHT, padx=20)

        self.tree_container = ttk.Frame(self)
        self.tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(self.tree_container, columns=("pos", "name", "category", "level", "progress", "finish", "time_left"), show="headings")
        self.tree.heading("pos", text="#", command=lambda: self._sort_column("pos", False))
        self.tree.heading("name", text="Skill", command=lambda: self._sort_column("name", False))
        self.tree.heading("category", text="Category", command=lambda: self._sort_column("category", False))
        self.tree.heading("level", text="To Level", command=lambda: self._sort_column("level", False))
        self.tree.heading("progress", text="Progress", command=lambda: self._sort_column("progress", False))
        self.tree.heading("finish", text="Finish Date (UTC)", command=lambda: self._sort_column("finish", False))
        self.tree.heading("time_left", text="Time Left", command=lambda: self._sort_column("time_left", False))
        
        self.tree.column("pos", width=40, anchor=tk.CENTER)
        self.tree.column("name", width=220)
        self.tree.column("category", width=110)
        self.tree.column("level", width=70, anchor=tk.CENTER)
        self.tree.column("progress", width=120, anchor=tk.CENTER)
        self.tree.column("finish", width=140)
        self.tree.column("time_left", width=90, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(self.tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def set_queue(self, queue_data, attributes_data=None):
        self.queue = queue_data
        self.tree.delete(*self.tree.get_children())
        
        now = datetime.utcnow()
        
        # Display training speed if available
        if attributes_data:
            # We don't know the exact skill's attributes easily without more data,
            # so we'll show a range or just character stats.
            # Base SP/min = Primary + Secondary/2
            # For now, let's just show character attributes as a tooltip or similar.
            pass

        for i, q in enumerate(self.queue):
            skill_id = q.get("skill_id")
            pos = q.get("queue_position", 0)
            name = skills_db.get_skill_name(skill_id)
            category = skills_db.get_skill_category(skill_id) or "Other"
            level = q.get("finished_level", 0)
            
            # Progress calculation
            start_sp = q.get("training_start_sp", 0)
            end_sp = q.get("level_end_sp", q.get("training_end_sp", 0))
            # Note: ESI doesn't give us current SP in the queue request.
            # For the currently training skill (pos 0), we can only estimate 
            # or wait for the next skills fetch.
            
            progress_str = ""
            if i == 0: # Currently training
                progress_str = "⌛ [In Progress]"
            else:
                progress_str = "○ [Pending]"

            finish_raw = q.get("finish_date")
            finish_str = "N/A"
            time_left_str = "N/A"
            
            if finish_raw:
                try:
                    finish_dt = datetime.strptime(finish_raw.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
                    finish_str = finish_dt.strftime("%Y-%m-%d %H:%M")
                    
                    diff = finish_dt - now
                    if diff.total_seconds() <= 0:
                        time_left_str = "Completed"
                        progress_str = "● [100%]"
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

            self.tree.insert("", tk.END, values=(pos, name, category, level, progress_str, finish_str, time_left_str))

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
