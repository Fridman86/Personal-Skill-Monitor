import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import webbrowser
from datetime import datetime
from src.gui.components.skill_view import SkillView
from src.gui.components.queue_view import QueueView
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
        self.geometry("1100x750")
        self.minsize(1000, 700)

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
            # Treeview is styled via ttk.Style in setup_eve_dark_theme or manually
            pass
        elif theme == "EVE Dark":
            setup_eve_dark_theme(style)
            self.configure(bg="#101218")
            # Treeview is styled via ttk.Style in setup_eve_dark_theme
        else: # System / Default
            style.theme_use('clam')
            style.configure("Treeview", rowheight=25)
            style.configure("TButton", padding=5)
            style.configure("TFrame", background="#f5f5f5")
            style.configure("TLabel", background="#f5f5f5")
            self.configure(bg="#f5f5f5")

    def _setup_ui(self):
        # No top menu bar (minimalist sidebar-only navigation)
        # The OS title bar remains

        # Sidebar (RIFT-style)
        self.sidebar = ttk.Frame(self, width=220, style="Sidebar.TFrame")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        self.sidebar.pack_propagate(False) # Keep fixed width
        
        ttk.Label(self.sidebar, text="Characters", style="Header.TLabel", borderwidth=0).pack(pady=(20, 10), padx=10)
        
        # Action Bar (Vertical)
        self.action_bar = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        self.action_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 20))

        # Separator between list and buttons
        ttk.Frame(self.sidebar, height=1, style="Separator.TFrame").pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 15))

        ttk.Button(self.action_bar, text=" ＋  Add Character", style="Nav.TButton", command=self._add_character).pack(fill=tk.X)
        ttk.Button(self.action_bar, text=" －  Remove", style="Nav.TButton", command=self._remove_character).pack(fill=tk.X)
        ttk.Button(self.action_bar, text=" ↻  Refresh Data", style="Nav.TButton", command=self._refresh_data).pack(fill=tk.X)
        ttk.Button(self.action_bar, text=" ⏻  Quit", style="Nav.TButton", command=self._on_quit).pack(fill=tk.X)
        ttk.Button(self.action_bar, text=" ☕  Buy me a coffee", style="Nav.TButton", command=self._on_coffee_click).pack(fill=tk.X)

        self.char_tree = ttk.Treeview(self.sidebar, show="tree", selectmode="browse", height=10)
        self.char_tree.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.char_tree.bind("<<TreeviewSelect>>", self._on_char_select)
        
        # Main Area
        content_frame = ttk.Frame(self)
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Top Bar (Title & Export) - Polished
        self.top_strip = ttk.Frame(content_frame, style="Toolbar.TFrame")
        self.top_strip.pack(fill=tk.X, pady=(0, 15))
        
        top_bar = ttk.Frame(self.top_strip)
        top_bar.pack(fill=tk.X, padx=10, pady=10)
        
        self.char_title_var = tk.StringVar(value="No Character Selected")
        ttk.Label(top_bar, textvariable=self.char_title_var, font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)
        
        # Compact Export Toolbar
        export_frame = ttk.Frame(top_bar)
        export_frame.pack(side=tk.RIGHT)
        
        ttk.Label(export_frame, text="Format:").pack(side=tk.LEFT, padx=(10, 5))
        self.export_format = tk.StringVar(value="CSV")
        fmt_cb = ttk.Combobox(export_frame, textvariable=self.export_format, state="readonly", 
                               values=["CSV", "JSON", "TXT", "XML", "Python", "Clipboard"], width=10)
        fmt_cb.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(export_frame, text="Scope:").pack(side=tk.LEFT, padx=(10, 5))
        self.export_scope = tk.StringVar(value="All Skills")
        scope_cb = ttk.Combobox(export_frame, textvariable=self.export_scope, state="readonly", 
                                 values=["All Skills", "Filtered Skills", "Skill Queue"], width=15)
        scope_cb.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(export_frame, text="Export", command=self._on_export_click).pack(side=tk.LEFT, padx=10)
        
        self.append_date_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(export_frame, text="Append date", variable=self.append_date_var).pack(side=tk.LEFT, padx=(0, 5))

        # Paned Window for Skills and Queue
        self.paned = ttk.PanedWindow(content_frame, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        self.skill_view = SkillView(self.paned)
        self.queue_view = QueueView(self.paned)
        
        self.paned.add(self.skill_view, weight=3)
        self.paned.add(self.queue_view, weight=1)

    def _load_characters(self):
        # Clear existing items
        for item in self.char_tree.get_children():
            self.char_tree.delete(item)
            
        self.chars = self.app_config.get_characters()
        for idx, char in enumerate(self.chars):
            # Use character ID as the item ID for easy lookup
            self.char_tree.insert("", tk.END, iid=str(idx), text=f"  {char['name']}")
        
        # Log unknown skills on start
        unknowns = []
        if self.current_skills:
            for s in self.current_skills:
                if skills_db.is_unknown_skill(s.get("skill_id")):
                    unknowns.append(f"{s.get('skill_id')} ({s.get('name')})")
        
        if unknowns:
            print(f"[INFO] Unknown skills found: {', '.join(unknowns)}")

    def _on_quit(self):
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
            
            if skills_data:
                self.current_skills = skills_data.get("skills", [])
                self.skill_view.set_skills(self.current_skills)
                
                # Check for unknown skills after loading
                unknowns = [s.get("skill_id") for s in self.current_skills if skills_db.is_unknown_skill(s.get("skill_id"))]
                if unknowns:
                    print(f"[INFO] Unknown skills for {self.char_title_var.get()}: {unknowns}")
                
            if queue_data:
                self.current_queue = queue_data
                self.queue_view.set_queue(self.current_queue)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {e}")

    def _on_coffee_click(self):
        webbrowser.open("https://buymeacoffee.com/ifridman")

    def _on_export_click(self):
        if not self.current_char_id:
            messagebox.showwarning("Warning", "Select a character first")
            return
            
        char_name = self.char_title_var.get().replace(" ", "_")
        scope = self.export_scope.get()
        fmt = self.export_format.get().lower()
        
        # Map scope to filename part
        scope_map = {
            "All Skills": "skills_all",
            "Filtered Skills": "skills_filtered",
            "Skill Queue": "queue"
        }
        data_type = scope_map.get(scope, "data")
        
        # Construct default filename
        filename = f"{char_name}_{data_type}"
        if self.append_date_var.get():
            date_str = datetime.now().strftime("%Y%m%d")
            filename += f"_{date_str}"
        
        if fmt == "clipboard":
            self._export(data_type, None)
            return

        ext = fmt if fmt != "python" else "py"
        if fmt == "txt": ext = "txt"
        
        filetypes = [
            (f"{fmt.upper()} Files", f"*.{ext}"),
            ("All Files", "*.*")
        ]
        
        filepath = filedialog.asksaveasfilename(
            initialdir="exports",
            initialfile=f"{filename}.{ext}",
            defaultextension=f".{ext}",
            filetypes=filetypes,
            title="Save Export As"
        )
        
        if filepath:
            self._export(data_type, filepath)
        else:
            # User cancelled or closed the dialog
            pass

    def _export(self, data_type, full_path):
        char_name = self.char_title_var.get()
        fmt = self.export_format.get()
        
        if data_type == "skills_all":
            data = self.skill_view.skills 
            res = self.export_manager.export(char_name, "skills", fmt, data, tk_root=self, full_path=full_path)
        elif data_type == "skills_filtered":
            data = self.skill_view._get_filtered_skills()
            res = self.export_manager.export(char_name, "skills_filtered", fmt, data, tk_root=self, full_path=full_path)
        elif data_type == "queue":
            data = []
            for q in self.current_queue:
                q_copy = q.copy()
                q_copy["name"] = skills_db.get_skill_name(q.get("skill_id"))
                q_copy["category"] = skills_db.get_skill_category(q.get("skill_id")) or "Other"
                data.append(q_copy)
            res = self.export_manager.export(char_name, "queue", fmt, data, tk_root=self, full_path=full_path)
        
        if res:
            messagebox.showinfo("Export", res)
