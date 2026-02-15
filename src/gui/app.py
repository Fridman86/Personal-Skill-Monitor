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
from src.ui.theme_eve import setup_eve_dark_theme
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

        # Set window icon
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

    def _load_setting(self, key, default):
        try:
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
                return settings.get(key, default)
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

    def _apply_style(self):
        style = ttk.Style(self)
        theme = self.theme_var.get()
        
        if theme == "Dark":
            style.theme_use('clam')
            bg_color = "#2d2d2d"
            fg_color = "#ffffff"
            header_bg = "#3d3d3d"
            select_bg = "#4a4a4a"
            
            style.configure("Treeview", background=bg_color, foreground=fg_color, fieldbackground=bg_color, rowheight=25)
            style.configure("Treeview.Heading", background=header_bg, foreground=fg_color)
            style.map("Treeview", background=[('selected', select_bg)])
            
            style.configure("TFrame", background=bg_color)
            style.configure("TLabel", background=bg_color, foreground=fg_color)
            style.configure("TButton", padding=5)
            style.configure("TCheckbutton", background=bg_color, foreground=fg_color)
            style.configure("TCombobox", fieldbackground="#3d3d3d", background="#3d3d3d", foreground=fg_color)
            style.configure("TEntry", fieldbackground="#3d3d3d", foreground=fg_color)
            
            self.configure(bg=bg_color)
        elif theme == "EVE Dark":
            setup_eve_dark_theme(style)
            self.configure(bg="#0e1017")
        else:  # System / Default
            style.theme_use('clam')
            style.configure("Treeview", rowheight=25)
            style.configure("TButton", padding=5)
            style.configure("TFrame", background="#f5f5f5")
            style.configure("TLabel", background="#f5f5f5")
            self.configure(bg="#f5f5f5")

    def _setup_ui(self):
        # ── Main PanedWindow (horizontal) for resizable sidebar ──
        self.main_pw = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_pw.pack(fill=tk.BOTH, expand=True)

        # ── Sidebar ──
        self.sidebar = ttk.Frame(self.main_pw, style="Sidebar.TFrame")

        # Characters header
        ttk.Label(self.sidebar, text="Characters",
                  style="Header.TLabel",
                  borderwidth=0).pack(pady=(18, 8), padx=12)

        # Character list
        self.char_tree = ttk.Treeview(self.sidebar, show="tree",
                                       selectmode="browse",
                                       style="CharList.Treeview")
        self.char_tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 5))
        self.char_tree.bind("<<TreeviewSelect>>", self._on_char_select)

        # Separator
        ttk.Frame(self.sidebar, height=1,
                  style="Separator.TFrame").pack(fill=tk.X, padx=10, pady=8)

        # Action buttons
        self.action_bar = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        self.action_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 15))

        buttons = [
            (" ＋  Add Character", self._add_character),
            (" －  Remove", self._remove_character),
            (" ↻  Refresh Data", self._refresh_data),
            (" 📋  Skill Plans", self._open_skill_plan),
            (" ℹ  About", self._on_about_click),
            (" ⏻  Quit", self._on_quit),
        ]
        for text, cmd in buttons:
            ttk.Button(self.action_bar, text=text, style="Nav.TButton",
                       command=cmd).pack(fill=tk.X)

        # ── Content Area ──
        content_frame = ttk.Frame(self.main_pw)

        # Top strip (title + export)
        self.top_strip = ttk.Frame(content_frame, style="Toolbar.TFrame")
        self.top_strip.pack(fill=tk.X, pady=(0, 2))

        top_bar = ttk.Frame(self.top_strip, style="Toolbar.TFrame")
        top_bar.pack(fill=tk.X, padx=14, pady=8)

        self.char_title_var = tk.StringVar(value="No Character Selected")
        ttk.Label(top_bar, textvariable=self.char_title_var,
                  style="Title.TLabel",
                  background="#141820").pack(side=tk.LEFT)

        # Export controls (simplified: Clipboard + CSV only)
        export_frame = ttk.Frame(top_bar, style="Toolbar.TFrame")
        export_frame.pack(side=tk.RIGHT)

        ttk.Label(export_frame, text="Scope:",
                  background="#141820").pack(side=tk.LEFT, padx=(0, 5))
        self.export_scope = tk.StringVar(value="All Skills")
        scope_cb = ttk.Combobox(export_frame, textvariable=self.export_scope,
                                 state="readonly",
                                 values=["All Skills", "Filtered Skills", "Skill Queue"],
                                 width=14)
        scope_cb.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(export_frame, text="📋 Copy",
                   style="Accent.TButton",
                   command=lambda: self._on_export("clipboard")).pack(side=tk.LEFT, padx=3)
        ttk.Button(export_frame, text="💾 CSV",
                   style="Accent.TButton",
                   command=lambda: self._on_export("csv")).pack(side=tk.LEFT, padx=3)

        # Stats bar
        self.stats_frame = ttk.Frame(content_frame)
        self.stats_frame.pack(fill=tk.X, padx=14, pady=(4, 2))

        self.total_sp_var = tk.StringVar(value="Total SP: 0")
        self.unallocated_sp_var = tk.StringVar(value="Unallocated SP: 0")
        self.cache_status_var = tk.StringVar(value="")

        ttk.Label(self.stats_frame, textvariable=self.total_sp_var,
                  style="Stat.TLabel").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(self.stats_frame, textvariable=self.unallocated_sp_var,
                  style="Stat.TLabel").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(self.stats_frame, textvariable=self.cache_status_var,
                  style="Dim.TLabel").pack(side=tk.RIGHT)

        # Paned Window for Skills and Queue (vertical)
        self.paned = ttk.PanedWindow(content_frame, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))

        self.skill_view = SkillView(self.paned)
        self.queue_view = QueueView(self.paned)

        self.paned.add(self.skill_view, weight=3)
        self.paned.add(self.queue_view, weight=1)

        # Add to main PanedWindow
        self.main_pw.add(self.sidebar, weight=0)
        self.main_pw.add(content_frame, weight=1)

        # Set initial sidebar width after widget is mapped
        self.after(50, lambda: self._set_initial_sash())

    def _set_initial_sash(self):
        """Set the initial sidebar width via sash position."""
        try:
            saved_width = self._load_setting("sidebar_width", 200)
            self.main_pw.sashpos(0, saved_width)
        except Exception:
            pass

    def _load_characters(self):
        for item in self.char_tree.get_children():
            self.char_tree.delete(item)
            
        self.chars = self.app_config.get_characters()
        for idx, char in enumerate(self.chars):
            self.char_tree.insert("", tk.END, iid=str(idx), text=f"  {char['name']}")
        
        # Log unknown skills on start
        unknowns = []
        if self.current_skills:
            for s in self.current_skills:
                if skills_db.is_unknown_skill(s.get("skill_id")):
                    unknowns.append(f"{s.get('skill_id')} ({s.get('name')})")
        
        if unknowns:
            print(f"[INFO] Unknown skills found: {', '.join(unknowns)}")

    def _on_about_click(self):
        messagebox.showinfo("About",
                            "Personal Skill Monitor v0.2.0\n\n"
                            "A lightweight desktop application for\n"
                            "EVE Online skill management.\n\n"
                            "Author: Fridman86\n"
                            "GitHub: https://github.com/Fridman86/Personal-Skill-Monitor")

    def _on_quit(self):
        # Save sidebar width before exiting
        try:
            sash_pos = self.main_pw.sashpos(0)
            self._save_setting("sidebar_width", sash_pos)
        except Exception:
            pass
        if messagebox.askyesno("Exit", "Exit Personal Skill Monitor?"):
            self.destroy()

    def _on_char_select(self, event):
        selection = self.char_tree.selection()
        if selection:
            char_index = int(selection[0])
            char_data = self.chars[char_index]
            self.current_char_id = char_data["id"]
            self.char_title_var.set(char_data["name"])
            self._refresh_data()

    def _add_character(self):
        def on_auth_success(code):
            try:
                token_data = self.auth_manager.exchange_code(code)
                verify_data = self.auth_manager.verify_token(token_data["access_token"])
                char_id = verify_data["CharacterID"]
                char_name = verify_data["CharacterName"]
                
                self.app_config.update_character_token(char_id, char_name, token_data)
                self.after(0, self._load_characters)
                messagebox.showinfo("Success", f"Character {char_name} added!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add character: {e}")

        self.auth_manager.start_auth_flow(on_auth_success)

    def _remove_character(self):
        selection = self.char_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "No character selected")
            return
            
        char_index = int(selection[0])
        char_data = self.chars[char_index]
        
        confirm = messagebox.askyesno("Confirm Removal", 
                                     f"Remove character '{char_data['name']}' from this app?\n\n"
                                     "Tokens and cached data for this character will be deleted from local storage.")
        if confirm:
            if self.app_config.remove_character(char_data["id"]):
                if self.current_char_id == char_data["id"]:
                    self.current_char_id = None
                    self.char_title_var.set("No Character Selected")
                    self.skill_view.set_skills([])
                    self.queue_view.set_queue([])
                    self.total_sp_var.set("Total SP: 0")
                    self.unallocated_sp_var.set("Unallocated SP: 0")
                    self.cache_status_var.set("")
                self._load_characters()
                messagebox.showinfo("Success", f"Character '{char_data['name']}' removed.")
            else:
                messagebox.showerror("Error", "Failed to remove character.")

    def _refresh_data(self):
        if not self.current_char_id:
            return
            
        try:
            skills_data = self.esi_client.get_skills(self.current_char_id)
            queue_data = self.esi_client.get_skill_queue(self.current_char_id)
            attr_data = self.esi_client.get_attributes(self.current_char_id)
            
            status_text = "Data synced with ESI"
            
            if skills_data:
                self.current_skills = skills_data.get("skills", [])
                self.skill_view.set_skills(self.current_skills)
                
                total_sp = skills_data.get("total_sp", 0)
                unallocated_sp = skills_data.get("unallocated_sp", 0)
                self.total_sp_var.set(f"Total SP: {total_sp:,}")
                self.unallocated_sp_var.set(f"Unallocated SP: {unallocated_sp:,}")
                
            if queue_data:
                self.current_queue = queue_data
                self.queue_view.set_queue(self.current_queue, attr_data)
                
            if attr_data:
                int_ = attr_data.get("intelligence", 0)
                mem = attr_data.get("memory", 0)
                per = attr_data.get("perception", 0)
                wil = attr_data.get("willpower", 0)
                cha = attr_data.get("charisma", 0)
                
                attr_str = f"INT:{int_} MEM:{mem} PER:{per} WIL:{wil} CHA:{cha}"
                self.queue_view.sp_min_var.set(f"Attributes: {attr_str}")
            
            self.cache_status_var.set(status_text)
            
        except Exception as e:
            self.cache_status_var.set("Offline Mode / Error")
            print(f"[ERROR] Refresh failed: {e}")

    def _on_coffee_click(self):
        webbrowser.open("https://buymeacoffee.com/ifridman")

    def _open_skill_plan(self):
        SkillPlanManager(self, self.current_skills)

    def _on_export(self, fmt):
        """Unified export handler for both clipboard and CSV."""
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
        
        # Get the data
        if data_type == "skills_all":
            data = self.skill_view.skills
        elif data_type == "skills_filtered":
            data = self.skill_view._get_filtered_skills()
        elif data_type == "queue":
            data = []
            for q in self.current_queue:
                q_copy = q.copy()
                q_copy["name"] = skills_db.get_skill_name(q.get("skill_id"))
                q_copy["category"] = skills_db.get_skill_category(q.get("skill_id")) or "Other"
                data.append(q_copy)

        if fmt == "clipboard":
            res = self.export_manager.export(char_name, data_type, "Clipboard", data, tk_root=self)
            if res:
                messagebox.showinfo("Export", res)
        elif fmt == "csv":
            filename = f"{char_name}_{data_type}"
            date_str = datetime.now().strftime("%Y%m%d")
            filename += f"_{date_str}"

            filepath = filedialog.asksaveasfilename(
                initialdir="exports",
                initialfile=f"{filename}.csv",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
                title="Save Export As"
            )
            if filepath:
                res = self.export_manager.export(char_name, data_type, "CSV", data, full_path=filepath)
                if res:
                    messagebox.showinfo("Export", res)
