import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import webbrowser
from datetime import datetime
from src.gui.components.skill_view import SkillView
from src.gui.components.queue_view import QueueView
from src.gui.components.skill_plan import SkillPlanManager
from src.core.auth import AuthManager
from src.core.esi import ESIClient
from src.utils.export import ExportManager
from src.data import skills_db
from src.ui.theme_eve import setup_eve_dark_theme, BG_SIDEBAR, BG_MAIN, BG_PANEL, \
    BORDER, FG_DEFAULT, FG_BRIGHT, FG_TEAL, FG_DIM, BG_SELECT
from src.utils.paths import PathManager


class EVEApp(tk.Tk):
    def __init__(self, config):
        super().__init__()
        self.app_config = config
        self.auth_manager = AuthManager(config)
        self.esi_client = ESIClient(self.auth_manager, config)
        self.export_manager = ExportManager()

        self.title("Personal Skill Monitor")
        self.geometry("1150x780")
        self.minsize(950, 650)

        # Window icon
        icon_path = PathManager.get_icon_path()
        if icon_path.exists():
            try:
                self.icon_photo = tk.PhotoImage(file=str(icon_path))
                self.wm_iconphoto(True, self.icon_photo)
            except Exception as e:
                print(f"[WARNING] Failed to load icon: {e}")

        self.current_char_id = None
        self.chars = []
        self.current_skills = []
        self.current_queue = []

        self.settings_file = PathManager.get_settings_path()
        self.theme_var = tk.StringVar(value=self._load_setting("theme", "EVE Dark"))

        self._setup_ui()
        self._apply_style()
        self._load_characters()

    # ── Settings ─────────────────────────────────────────
    def _load_setting(self, key, default):
        try:
            with open(self.settings_file, "r") as f:
                return json.load(f).get(key, default)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _save_setting(self, key, value):
        settings = {}
        try:
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        settings[key] = value
        with open(self.settings_file, "w") as f:
            json.dump(settings, f)

    # ── Theme ────────────────────────────────────────────
    def _apply_style(self):
        style = ttk.Style(self)
        theme = self.theme_var.get()

        if theme == "EVE Dark":
            setup_eve_dark_theme(style)
            self.configure(bg=BG_MAIN)
        elif theme == "Dark":
            style.theme_use("clam")
            bg = "#2d2d2d"
            fg = "#ffffff"
            style.configure("Treeview", background=bg, foreground=fg,
                            fieldbackground=bg, rowheight=25)
            style.configure("Treeview.Heading", background="#3d3d3d", foreground=fg)
            style.map("Treeview", background=[("selected", "#4a4a4a")])
            style.configure("TFrame", background=bg)
            style.configure("TLabel", background=bg, foreground=fg)
            style.configure("TButton", padding=5)
            style.configure("TCheckbutton", background=bg, foreground=fg)
            self.configure(bg=bg)
        else:
            style.theme_use("clam")
            style.configure("Treeview", rowheight=25)
            style.configure("TButton", padding=5)
            style.configure("TFrame", background="#f5f5f5")
            style.configure("TLabel", background="#f5f5f5")
            self.configure(bg="#f5f5f5")

    # ── UI Layout ────────────────────────────────────────
    def _setup_ui(self):
        # ╔═══════════════════════════════════════════════╗
        # ║  SIDEBAR  │          CONTENT AREA             ║
        # ║  (fixed)  │  Title + Export controls          ║
        # ║           │  Stats bar                        ║
        # ║  Chars    │  ┌─────────────────────────────┐  ║
        # ║  list     │  │  Skill Table                │  ║
        # ║           │  ├─────────────────────────────┤  ║
        # ║  ─────    │  │  Skill Queue                │  ║
        # ║  Buttons  │  └─────────────────────────────┘  ║
        # ╚═══════════════════════════════════════════════╝

        # ── Left Sidebar (RIFT-style, fixed width) ──
        self.sidebar = tk.Frame(self, bg=BG_SIDEBAR, width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Thin right border on sidebar
        sidebar_border = tk.Frame(self, bg=BORDER, width=1)
        sidebar_border.pack(side=tk.LEFT, fill=tk.Y)

        # -- App branding --
        brand_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        brand_frame.pack(fill=tk.X, padx=0, pady=(0, 4))

        tk.Label(brand_frame, text="PSM", font=("Segoe UI", 16, "bold"),
                 fg=FG_TEAL, bg=BG_SIDEBAR, anchor="w").pack(padx=14, pady=(14, 0))
        tk.Label(brand_frame, text="Personal Skill Monitor",
                 font=("Segoe UI", 8), fg=FG_DIM, bg=BG_SIDEBAR,
                 anchor="w").pack(padx=14, pady=(0, 8))

        # Divider
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill=tk.X, padx=12)

        # -- Character list header --
        tk.Label(self.sidebar, text="CHARACTERS",
                 font=("Segoe UI", 8, "bold"), fg=FG_DIM,
                 bg=BG_SIDEBAR, anchor="w").pack(padx=14, pady=(12, 4))

        # -- Character list --
        self.char_tree = ttk.Treeview(self.sidebar, show="tree",
                                      selectmode="browse",
                                      style="CharList.Treeview")
        self.char_tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))
        self.char_tree.bind("<<TreeviewSelect>>", self._on_char_select)

        # Divider
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill=tk.X, padx=12, pady=4)

        # -- Navigation buttons (RIFT-style) --
        nav_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        nav_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 10))

        nav_buttons = [
            ("＋  Add Character", self._add_character),
            ("－  Remove",        self._remove_character),
            ("↻  Refresh Data",   self._refresh_data),
            ("📋  Skill Plans",    self._open_skill_plan),
            ("ℹ  About",          self._on_about_click),
            ("⏻  Quit",           self._on_quit),
        ]
        for text, cmd in nav_buttons:
            btn = tk.Button(nav_frame, text=text,
                            font=("Segoe UI", 10),
                            fg=FG_DEFAULT, bg=BG_SIDEBAR,
                            activeforeground=FG_TEAL, activebackground=BG_SIDEBAR,
                            bd=0, relief="flat", anchor="w",
                            padx=14, pady=6,
                            cursor="hand2",
                            command=cmd)
            btn.pack(fill=tk.X)
            btn.bind("<Enter>", lambda e, b=btn: b.config(fg=FG_TEAL))
            btn.bind("<Leave>", lambda e, b=btn: b.config(fg=FG_DEFAULT))

        # ── Content Area ──
        content = ttk.Frame(self)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # -- Top strip (title + export) --
        self.top_strip = tk.Frame(content, bg=BG_PANEL)
        self.top_strip.pack(fill=tk.X)

        top_inner = tk.Frame(self.top_strip, bg=BG_PANEL)
        top_inner.pack(fill=tk.X, padx=16, pady=10)

        self.char_title_var = tk.StringVar(value="Select a character")
        tk.Label(top_inner, textvariable=self.char_title_var,
                 font=("Segoe UI", 14, "bold"),
                 fg=FG_BRIGHT, bg=BG_PANEL, anchor="w").pack(side=tk.LEFT)

        # Export controls
        export_f = tk.Frame(top_inner, bg=BG_PANEL)
        export_f.pack(side=tk.RIGHT)

        tk.Label(export_f, text="Scope:", font=("Segoe UI", 9),
                 fg=FG_DIM, bg=BG_PANEL).pack(side=tk.LEFT, padx=(0, 4))
        self.export_scope = tk.StringVar(value="All Skills")
        scope_cb = ttk.Combobox(export_f, textvariable=self.export_scope,
                                state="readonly",
                                values=["All Skills", "Filtered Skills", "Skill Queue"],
                                width=14)
        scope_cb.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(export_f, text="📋 Copy", style="Accent.TButton",
                   command=lambda: self._on_export("clipboard")).pack(side=tk.LEFT, padx=2)
        ttk.Button(export_f, text="💾 CSV", style="Accent.TButton",
                   command=lambda: self._on_export("csv")).pack(side=tk.LEFT, padx=2)

        # Thin top-strip bottom border
        tk.Frame(content, bg=BORDER, height=1).pack(fill=tk.X)

        # -- Stats bar --
        stats_f = tk.Frame(content, bg=BG_MAIN)
        stats_f.pack(fill=tk.X, padx=16, pady=(8, 4))

        self.total_sp_var = tk.StringVar(value="Total SP: 0")
        self.unallocated_sp_var = tk.StringVar(value="Unallocated SP: 0")
        self.cache_status_var = tk.StringVar(value="")

        tk.Label(stats_f, textvariable=self.total_sp_var,
                 font=("Segoe UI", 9), fg=FG_TEAL, bg=BG_MAIN).pack(side=tk.LEFT, padx=(0, 20))
        tk.Label(stats_f, textvariable=self.unallocated_sp_var,
                 font=("Segoe UI", 9), fg=FG_TEAL, bg=BG_MAIN).pack(side=tk.LEFT, padx=(0, 20))
        tk.Label(stats_f, textvariable=self.cache_status_var,
                 font=("Segoe UI", 8, "italic"), fg=FG_DIM, bg=BG_MAIN).pack(side=tk.RIGHT)

        # -- Skills / Queue PanedWindow --
        self.paned = ttk.PanedWindow(content, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))

        self.skill_view = SkillView(self.paned)
        self.queue_view = QueueView(self.paned)

        self.paned.add(self.skill_view, weight=3)
        self.paned.add(self.queue_view, weight=1)

    # ── Character management ─────────────────────────────
    def _load_characters(self):
        for item in self.char_tree.get_children():
            self.char_tree.delete(item)

        self.chars = self.app_config.get_characters()
        for idx, char in enumerate(self.chars):
            self.char_tree.insert("", tk.END, iid=str(idx),
                                  text=f"  {char['name']}")

        # Log unknowns
        if self.current_skills:
            unknowns = [f"{s.get('skill_id')}" for s in self.current_skills
                        if skills_db.is_unknown_skill(s.get("skill_id"))]
            if unknowns:
                print(f"[INFO] Unknown skill IDs: {', '.join(unknowns)}")

    def _on_char_select(self, event):
        sel = self.char_tree.selection()
        if sel:
            idx = int(sel[0])
            char = self.chars[idx]
            self.current_char_id = char["id"]
            self.char_title_var.set(char["name"])
            self._refresh_data()

    def _add_character(self):
        def on_auth_success(code):
            try:
                token_data = self.auth_manager.exchange_code(code)
                verify = self.auth_manager.verify_token(token_data["access_token"])
                char_id = verify["CharacterID"]
                char_name = verify["CharacterName"]
                self.app_config.update_character_token(char_id, char_name, token_data)
                self.after(0, self._load_characters)
                messagebox.showinfo("Success", f"Character {char_name} added!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add character: {e}")
        self.auth_manager.start_auth_flow(on_auth_success)

    def _remove_character(self):
        sel = self.char_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "No character selected")
            return
        idx = int(sel[0])
        char = self.chars[idx]
        if messagebox.askyesno("Confirm",
                               f"Remove '{char['name']}'?\n\n"
                               "Tokens and cached data will be deleted."):
            if self.app_config.remove_character(char["id"]):
                if self.current_char_id == char["id"]:
                    self.current_char_id = None
                    self.char_title_var.set("Select a character")
                    self.skill_view.set_skills([])
                    self.queue_view.set_queue([])
                    self.total_sp_var.set("Total SP: 0")
                    self.unallocated_sp_var.set("Unallocated SP: 0")
                    self.cache_status_var.set("")
                self._load_characters()
                messagebox.showinfo("Done", f"'{char['name']}' removed.")
            else:
                messagebox.showerror("Error", "Failed to remove character.")

    def _refresh_data(self):
        if not self.current_char_id:
            return
        try:
            skills_data = self.esi_client.get_skills(self.current_char_id)
            queue_data = self.esi_client.get_skill_queue(self.current_char_id)
            attr_data = self.esi_client.get_attributes(self.current_char_id)

            if skills_data:
                self.current_skills = skills_data.get("skills", [])
                self.skill_view.set_skills(self.current_skills)
                total = skills_data.get("total_sp", 0)
                unalloc = skills_data.get("unallocated_sp", 0)
                self.total_sp_var.set(f"Total SP: {total:,}")
                self.unallocated_sp_var.set(f"Unallocated SP: {unalloc:,}")

            if queue_data:
                self.current_queue = queue_data
                self.queue_view.set_queue(self.current_queue, attr_data)

            if attr_data:
                i = attr_data.get("intelligence", 0)
                m = attr_data.get("memory", 0)
                p = attr_data.get("perception", 0)
                w = attr_data.get("willpower", 0)
                c = attr_data.get("charisma", 0)
                self.queue_view.sp_min_var.set(
                    f"Attributes: INT:{i} MEM:{m} PER:{p} WIL:{w} CHA:{c}")

            self.cache_status_var.set("Data synced with ESI")
        except Exception as e:
            self.cache_status_var.set("Offline / Error")
            print(f"[ERROR] Refresh failed: {e}")

    # ── Export ───────────────────────────────────────────
    def _on_export(self, fmt):
        if not self.current_char_id:
            messagebox.showwarning("Warning", "Select a character first")
            return

        char_name = self.char_title_var.get().replace(" ", "_")
        scope = self.export_scope.get()
        scope_map = {
            "All Skills": "skills_all",
            "Filtered Skills": "skills_filtered",
            "Skill Queue": "queue"
        }
        data_type = scope_map.get(scope, "data")

        # Gather data
        if data_type == "skills_all":
            data = self.skill_view.skills
        elif data_type == "skills_filtered":
            data = self.skill_view._get_filtered_skills()
        elif data_type == "queue":
            data = []
            for q in self.current_queue:
                qc = q.copy()
                qc["name"] = skills_db.get_skill_name(q.get("skill_id"))
                qc["category"] = skills_db.get_skill_category(q.get("skill_id")) or "Other"
                data.append(qc)
        else:
            data = []

        if fmt == "clipboard":
            res = self.export_manager.export(char_name, data_type, "Clipboard",
                                             data, tk_root=self)
            if res:
                messagebox.showinfo("Export", res)
        elif fmt == "csv":
            ts = datetime.now().strftime("%Y%m%d")
            fname = f"{char_name}_{data_type}_{ts}"
            path = filedialog.asksaveasfilename(
                initialdir="exports",
                initialfile=f"{fname}.csv",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
                title="Save Export As")
            if path:
                res = self.export_manager.export(char_name, data_type, "CSV",
                                                 data, full_path=path)
                if res:
                    messagebox.showinfo("Export", res)

    # ── Misc ─────────────────────────────────────────────
    def _open_skill_plan(self):
        SkillPlanManager(self, self.current_skills)

    def _on_about_click(self):
        messagebox.showinfo("About",
                            "Personal Skill Monitor v0.2.0\n\n"
                            "Lightweight EVE Online skill management.\n\n"
                            "Author: Fridman86\n"
                            "GitHub: github.com/Fridman86/Personal-Skill-Monitor")

    def _on_quit(self):
        if messagebox.askyesno("Exit", "Exit Personal Skill Monitor?"):
            self.destroy()

    def _on_coffee_click(self):
        webbrowser.open("https://buymeacoffee.com/ifridman")
