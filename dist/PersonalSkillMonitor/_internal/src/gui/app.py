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
    BORDER, FG_DEFAULT, FG_BRIGHT, FG_TEAL, FG_DIM, BG_SELECT, BORDER_LIGHT
from src.ui.tooltip import Tooltip
from src.utils.paths import PathManager


class EVEApp(tk.Tk):
    def __init__(self, config):
        super().__init__()
        self.app_config = config
        self.auth_manager = AuthManager(config)
        self.esi_client = ESIClient(self.auth_manager, config)
        self.export_manager = ExportManager()

        self.title("Personal Skill Monitor")
        self.geometry("1200x780")
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
        # ╔══════════════════╤═══════════════════════════════╗
        # ║     SIDEBAR      │       CONTENT AREA            ║
        # ║  (resizable)     │  Title bar + Export           ║
        # ║                  │  Stats                        ║
        # ║  PSM branding    │  ┌────────────────────────┐   ║
        # ║  ────────        │  │ Skill Table            │   ║
        # ║  CHARACTERS      │  ├────────────────────────┤   ║
        # ║   · Kobi         │  │ Skill Queue            │   ║
        # ║   · Orli         │  └────────────────────────┘   ║
        # ║  ────────        │                               ║
        # ║  Nav buttons     │                               ║
        # ╚══════════════════╧═══════════════════════════════╝

        # ── Main horizontal PanedWindow for resizable sidebar ──
        self.main_pw = tk.PanedWindow(self, orient=tk.HORIZONTAL,
                                      sashwidth=4,
                                      sashrelief=tk.FLAT,
                                      bg=BORDER_LIGHT,
                                      borderwidth=0,
                                      opaqueresize=True)
        self.main_pw.pack(fill=tk.BOTH, expand=True)

        # ── LEFT: Sidebar ──
        self.sidebar = tk.Frame(self.main_pw, bg=BG_SIDEBAR)

        # Branding
        brand = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        brand.pack(fill=tk.X, pady=(0, 2))

        tk.Label(brand, text="PSM", font=("Segoe UI", 16, "bold"),
                 fg=FG_TEAL, bg=BG_SIDEBAR, anchor="w").pack(padx=14, pady=(14, 0))
        tk.Label(brand, text="Personal Skill Monitor",
                 font=("Segoe UI", 8), fg=FG_DIM, bg=BG_SIDEBAR,
                 anchor="w").pack(padx=14, pady=(0, 10))

        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill=tk.X, padx=10)

        # Section header
        tk.Label(self.sidebar, text="CHARACTERS",
                 font=("Segoe UI", 8, "bold"), fg=FG_DIM,
                 bg=BG_SIDEBAR, anchor="w").pack(padx=14, pady=(10, 4))

        # Character list
        self.char_tree = ttk.Treeview(self.sidebar, show="tree",
                                      selectmode="browse",
                                      style="CharList.Treeview")
        self.char_tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))
        self.char_tree.bind("<<TreeviewSelect>>", self._on_char_select)
        Tooltip(self.char_tree,
                "Your EVE Online characters.\n"
                "Click a name to select and load skills.")

        # Divider
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill=tk.X, padx=10, pady=4)

        # Navigation buttons (bottom)
        nav = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        nav.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 10))

        nav_items = [
            ("＋  Add Character",  self._add_character,
             "Authorize a new EVE Online character\nvia SSO login in your browser."),
            ("－  Remove",         self._remove_character,
             "Remove the selected character and\ndelete its local tokens."),
            ("↻  Refresh Data",    self._refresh_data,
             "Fetch latest skills and queue\nfrom EVE ESI API."),
            ("📋  Skill Plans",     self._open_skill_plan,
             "Open the Skill Plan Manager to\ncreate custom training plans."),
            ("ℹ  About",           self._on_about_click,
             "Application info and version."),
            ("⏻  Quit",            self._on_quit,
             "Exit the application."),
        ]
        for text, cmd, tip in nav_items:
            btn = tk.Button(nav, text=text,
                            font=("Segoe UI", 10),
                            fg=FG_DEFAULT, bg=BG_SIDEBAR,
                            activeforeground=FG_TEAL, activebackground=BG_SIDEBAR,
                            bd=0, relief="flat", anchor="w",
                            padx=14, pady=6, cursor="hand2",
                            command=cmd)
            btn.pack(fill=tk.X)
            btn.bind("<Enter>", lambda e, b=btn: b.config(fg=FG_TEAL))
            btn.bind("<Leave>", lambda e, b=btn: b.config(fg=FG_DEFAULT))
            Tooltip(btn, tip)

        # ── RIGHT: Content Area ──
        content = tk.Frame(self.main_pw, bg=BG_MAIN)

        # Top strip (title + export)
        top_strip = tk.Frame(content, bg=BG_PANEL)
        top_strip.pack(fill=tk.X)

        top_inner = tk.Frame(top_strip, bg=BG_PANEL)
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
        Tooltip(scope_cb, "Choose which data to export:\n"
                "• All Skills — every skill on the character\n"
                "• Filtered Skills — only currently visible\n"
                "• Skill Queue — current training queue")

        btn_copy = ttk.Button(export_f, text="📋 Copy", style="Accent.TButton",
                              command=lambda: self._on_export("clipboard"))
        btn_copy.pack(side=tk.LEFT, padx=2)
        Tooltip(btn_copy, "Copy skills to clipboard in EVE format:\n"
                "\"Skill Name Level\"\n\n"
                "Paste directly into EVE Online skill queue.")

        btn_csv = ttk.Button(export_f, text="💾 CSV", style="Accent.TButton",
                             command=lambda: self._on_export("csv"))
        btn_csv.pack(side=tk.LEFT, padx=2)
        Tooltip(btn_csv, "Save skills to a CSV file.\n"
                "Format: Skill Name, Level")

        # Top-strip bottom border
        tk.Frame(content, bg=BORDER, height=1).pack(fill=tk.X)

        # Stats bar
        stats_f = tk.Frame(content, bg=BG_MAIN)
        stats_f.pack(fill=tk.X, padx=16, pady=(8, 4))

        self.total_sp_var = tk.StringVar(value="Total SP: 0")
        self.unallocated_sp_var = tk.StringVar(value="Unallocated SP: 0")
        self.cache_status_var = tk.StringVar(value="")

        lbl_sp = tk.Label(stats_f, textvariable=self.total_sp_var,
                          font=("Segoe UI", 9), fg=FG_TEAL, bg=BG_MAIN)
        lbl_sp.pack(side=tk.LEFT, padx=(0, 20))
        Tooltip(lbl_sp, "Total trained Skill Points\nacross all skills.")

        lbl_un = tk.Label(stats_f, textvariable=self.unallocated_sp_var,
                          font=("Segoe UI", 9), fg=FG_TEAL, bg=BG_MAIN)
        lbl_un.pack(side=tk.LEFT, padx=(0, 20))
        Tooltip(lbl_un, "Skill Points available to allocate\n(free SP from injectors, etc.).")

        tk.Label(stats_f, textvariable=self.cache_status_var,
                 font=("Segoe UI", 8, "italic"), fg=FG_DIM, bg=BG_MAIN).pack(side=tk.RIGHT)

        # Skill / Queue vertical PanedWindow
        self.paned = ttk.PanedWindow(content, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))

        self.skill_view = SkillView(self.paned)
        self.queue_view = QueueView(self.paned)

        self.paned.add(self.skill_view, weight=3)
        self.paned.add(self.queue_view, weight=1)

        # ── Add panes to main PanedWindow ──
        saved_w = self._load_setting("sidebar_width", 220)
        self.main_pw.add(self.sidebar, minsize=140, width=saved_w)
        self.main_pw.add(content, minsize=600)

        # Save sidebar width on sash drag
        self.main_pw.bind("<ButtonRelease-1>", self._on_sash_release)

    def _on_sash_release(self, event=None):
        """Persist sidebar width when user drags the sash."""
        try:
            coords = self.main_pw.sash_coord(0)
            if coords:
                self._save_setting("sidebar_width", coords[0])
        except Exception:
            pass

    # ── Character management ─────────────────────────────
    def _load_characters(self):
        for item in self.char_tree.get_children():
            self.char_tree.delete(item)

        self.chars = self.app_config.get_characters()
        for idx, char in enumerate(self.chars):
            self.char_tree.insert("", tk.END, iid=str(idx),
                                  text=f"  {char['name']}")

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
                cid = verify["CharacterID"]
                cname = verify["CharacterName"]
                self.app_config.update_character_token(cid, cname, token_data)
                self.after(0, self._load_characters)
                messagebox.showinfo("Success", f"Character {cname} added!")
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
        top = tk.Toplevel(self)
        top.title("About")
        top.resizable(True, True)
        
        # Apply theme colors roughly
        bg = "#1c2230" 
        fg = "#e0e0e0"
        accent = "#3aa8d0"
            
        top.configure(bg=bg)
        
        # Main container with padding
        main_f = tk.Frame(top, bg=bg, padx=30, pady=25)
        main_f.pack(fill=tk.BOTH, expand=True)
        
        # Header
        tk.Label(main_f, text="Personal Skill Monitor", 
                 font=("Segoe UI", 16, "bold"), fg=accent, bg=bg).pack(pady=(0, 5))
        
        tk.Label(main_f, text="v0.2.1", 
                 font=("Segoe UI", 10), fg="#888888", bg=bg).pack(pady=(0, 20))
        
        # Description
        desc = ("Lightweight EVE Online skill management tool.\n"
                "Track skills, view queue, and plan your training.")
        tk.Label(main_f, text=desc, font=("Segoe UI", 10), 
                 fg=fg, bg=bg, justify=tk.CENTER, wraplength=400).pack(pady=10)
                 
        # Links Frame
        links = tk.Frame(main_f, bg=bg)
        links.pack(pady=20)
        
        # GitHub
        def open_github(e=None):
            webbrowser.open("https://github.com/Fridman86/Personal-Skill-Monitor")
            
        lbl_git = tk.Label(links, text="GitHub Repository", 
                           font=("Segoe UI", 10, "underline"), 
                           fg=accent, bg=bg, cursor="hand2")
        lbl_git.pack(pady=5)
        lbl_git.bind("<Button-1>", open_github)
        
        # Buy Me a Coffee
        def open_coffee(e=None):
            webbrowser.open("https://buymeacoffee.com/ifridman")
            
        # Coffee container
        coffee_frame = tk.Frame(links, bg="#FFDD00", padx=15, pady=8, cursor="hand2")
        coffee_frame.pack(pady=(15, 0))
        
        lbl_coffee = tk.Label(coffee_frame, text="☕ Buy me a coffee",
                              font=("Cookie", 12, "bold") if "Cookie" in tk.font.families() else ("Segoe UI", 11, "bold"),
                              fg="#000000", bg="#FFDD00", cursor="hand2")
        lbl_coffee.pack()
        
        coffee_frame.bind("<Button-1>", open_coffee)
        lbl_coffee.bind("<Button-1>", open_coffee)
        
        # Close button at the bottom
        btn_close = tk.Button(main_f, text="Close", command=top.destroy,
                              bg="#2a3044", fg=fg, bd=0, padx=20, pady=5, cursor="hand2")
        btn_close.pack(pady=(30, 0))

        # Center on screen
        top.update_idletasks()
        top.minsize(top.winfo_reqwidth(), top.winfo_reqheight())
        
        w = top.winfo_reqwidth()
        h = top.winfo_reqheight()
        x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        top.geometry(f"+{x}+{y}")

    def _on_quit(self):
        if messagebox.askyesno("Exit", "Exit Personal Skill Monitor?"):
            self.destroy()

