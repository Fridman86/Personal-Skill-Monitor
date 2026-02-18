from __future__ import annotations

import json
import logging
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font as tkfont

from src.core.controller import AppController, CharacterData
from src.core.notifications import NotificationMonitor
from src.gui.components.skill_view import SkillView
from src.gui.components.queue_view import QueueView
from src.gui.components.skill_plan import SkillPlanManager
from src.utils.export import ExportManager
from src.utils.calculator import (
    training_time, plan_total_time, format_duration,
    get_skill_rank, _SP_PER_LEVEL,
)
from src.data import skills_db
from src.ui.theme_eve import (
    setup_eve_dark_theme,
    BG_SIDEBAR, BG_MAIN, BG_PANEL,
    BORDER, FG_DEFAULT, FG_BRIGHT, FG_TEAL, FG_DIM, BG_SELECT, BORDER_LIGHT,
    DARK_THEME, LIGHT_THEME,
)
from src.ui.tooltip import Tooltip
from src.utils.paths import PathManager
from src.utils.config import Config

logger = logging.getLogger(__name__)


class EVEApp(tk.Tk):
    """Main application window — thin GUI layer that delegates to AppController."""

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.controller     = AppController(config)
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
            except tk.TclError as e:
                logger.warning("Failed to load icon: %s", e)

        self.current_skills: list[dict] = []
        self.current_queue:  list[dict] = []
        self.current_attrs:  dict       = {}

        self.settings_file: Path = PathManager.get_settings_path()
        self.theme_var = tk.StringVar(value=self._load_setting("theme", "EVE Dark"))

        # Notification monitor
        notif_enabled = self._load_setting("notifications_enabled", True)
        self._notif_monitor = NotificationMonitor(
            self.controller, interval_minutes=5, threshold_minutes=5,
            enabled=notif_enabled,
        )
        self._notif_monitor.start()

        self._setup_ui()
        self._apply_style()
        self._load_characters()

        # Stop monitor on close
        self.protocol("WM_DELETE_WINDOW", self._on_quit)

    # ── Settings ─────────────────────────────────────────────────────────────
    def _load_setting(self, key: str, default: Any = None) -> Any:
        try:
            with open(self.settings_file, "r") as f:
                return json.load(f).get(key, default)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _save_setting(self, key: str, value: Any) -> None:
        settings: dict = {}
        try:
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        settings[key] = value
        with open(self.settings_file, "w") as f:
            json.dump(settings, f)

    # ── Theme ─────────────────────────────────────────────────────────────────
    def _apply_style(self) -> None:
        style = ttk.Style(self)
        theme = self.theme_var.get()

        if theme == "EVE Dark":
            setup_eve_dark_theme(style)
            self.configure(bg=BG_MAIN)
        elif theme == "Dark":
            t = DARK_THEME
            style.theme_use("clam")
            style.configure("Treeview", background=t["bg"], foreground=t["fg"],
                            fieldbackground=t["bg"], rowheight=25)
            style.configure("Treeview.Heading", background=t["heading_bg"],
                            foreground=t["fg"])
            style.map("Treeview", background=[("selected", t["select_bg"])])
            style.configure("TFrame",      background=t["bg"])
            style.configure("TLabel",      background=t["bg"], foreground=t["fg"])
            style.configure("TButton",     padding=5)
            style.configure("TCheckbutton", background=t["bg"], foreground=t["fg"])
            self.configure(bg=t["bg"])
        else:
            t = LIGHT_THEME
            style.theme_use("clam")
            style.configure("Treeview", rowheight=25)
            style.configure("TButton",  padding=5)
            style.configure("TFrame",   background=t["bg"])
            style.configure("TLabel",   background=t["bg"])
            self.configure(bg=t["bg"])

    # ── UI Layout ─────────────────────────────────────────────────────────────
    def _setup_ui(self):
        # ── Main horizontal PanedWindow for resizable sidebar ──
        self.main_pw = tk.PanedWindow(self, orient=tk.HORIZONTAL,
                                      sashwidth=4, sashrelief=tk.FLAT,
                                      bg=BORDER_LIGHT, borderwidth=0,
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
            ("⏱  Calculator",      self._open_calculator,
             "Training time calculator.\nEstimate how long a skill takes to train."),
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
                "\"Skill Name Level\"\n\nPaste directly into EVE Online skill queue.")

        btn_csv = ttk.Button(export_f, text="💾 CSV", style="Accent.TButton",
                             command=lambda: self._on_export("csv"))
        btn_csv.pack(side=tk.LEFT, padx=2)
        Tooltip(btn_csv, "Save skills to a CSV file.\nFormat: Skill Name, Level")

        btn_md = ttk.Button(export_f, text="📄 MD", style="Accent.TButton",
                            command=lambda: self._on_export("markdown"))
        btn_md.pack(side=tk.LEFT, padx=2)
        Tooltip(btn_md, "Save skills as a Markdown table.\nGreat for GitHub / Notion.")

        btn_html = ttk.Button(export_f, text="🌐 HTML", style="Accent.TButton",
                              command=lambda: self._on_export("html"))
        btn_html.pack(side=tk.LEFT, padx=2)
        Tooltip(btn_html, "Save skills as a styled HTML page.\nOpen in any browser.")

        # Top-strip bottom border
        tk.Frame(content, bg=BORDER, height=1).pack(fill=tk.X)

        # Stats bar
        stats_f = tk.Frame(content, bg=BG_MAIN)
        stats_f.pack(fill=tk.X, padx=16, pady=(8, 4))

        self.total_sp_var       = tk.StringVar(value="Total SP: 0")
        self.unallocated_sp_var = tk.StringVar(value="Unallocated SP: 0")
        self.cache_status_var   = tk.StringVar(value="")

        lbl_sp = tk.Label(stats_f, textvariable=self.total_sp_var,
                          font=("Segoe UI", 9), fg=FG_TEAL, bg=BG_MAIN)
        lbl_sp.pack(side=tk.LEFT, padx=(0, 20))
        Tooltip(lbl_sp, "Total trained Skill Points\nacross all skills.")

        lbl_un = tk.Label(stats_f, textvariable=self.unallocated_sp_var,
                          font=("Segoe UI", 9), fg=FG_TEAL, bg=BG_MAIN)
        lbl_un.pack(side=tk.LEFT, padx=(0, 20))
        Tooltip(lbl_un, "Skill Points available to allocate\n(free SP from injectors, etc.).")

        # Notification toggle in stats bar
        self._notif_var = tk.BooleanVar(
            value=self._load_setting("notifications_enabled", True))
        notif_cb = ttk.Checkbutton(stats_f, text="🔔 Notifications",
                                   variable=self._notif_var,
                                   command=self._on_notif_toggle)
        notif_cb.pack(side=tk.LEFT, padx=(0, 10))
        Tooltip(notif_cb, "Enable/disable desktop notifications\n"
                          "when a skill is about to finish training.")

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

        self.main_pw.bind("<ButtonRelease-1>", self._on_sash_release)

    def _on_sash_release(self, event=None):
        try:
            coords = self.main_pw.sash_coord(0)
            if coords:
                self._save_setting("sidebar_width", coords[0])
        except Exception:
            pass

    # ── Notification toggle ───────────────────────────────────────────────────
    def _on_notif_toggle(self) -> None:
        enabled = self._notif_var.get()
        self._notif_monitor.set_enabled(enabled)
        self._save_setting("notifications_enabled", enabled)

    # ── Character management ──────────────────────────────────────────────────
    def _load_characters(self) -> None:
        for item in self.char_tree.get_children():
            self.char_tree.delete(item)

        chars = self.controller.load_characters()
        for idx, char in enumerate(chars):
            self.char_tree.insert("", tk.END, iid=str(idx),
                                  text=f"  {char['name']}")

        unknowns = self.controller.get_unknown_skill_ids()
        if unknowns:
            logger.info("Unknown skill IDs: %s", ", ".join(unknowns))

    def _on_char_select(self, event: tk.Event) -> None:
        sel = self.char_tree.selection()
        if sel:
            idx   = int(sel[0])
            chars = self.controller.characters
            if idx < len(chars):
                char = chars[idx]
                self.controller.select_character(char["id"])
                self.char_title_var.set(char["name"])
                self._refresh_data()

    def _add_character(self) -> None:
        def on_auth_success(code: str) -> None:
            try:
                cname = self.controller.finish_add_character(code)
                self.after(0, self._load_characters)
                self.after(0, lambda: messagebox.showinfo(
                    "Success", f"Character {cname} added!"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(
                    "Error", f"Failed to add character: {e}"))
        self.controller.start_add_character(on_auth_success)

    def _remove_character(self) -> None:
        sel = self.char_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "No character selected")
            return
        idx   = int(sel[0])
        chars = self.controller.characters
        if idx >= len(chars):
            return
        char = chars[idx]
        if messagebox.askyesno("Confirm",
                               f"Remove '{char['name']}'?\n\n"
                               "Tokens and cached data will be deleted."):
            if self.controller.remove_character(char["id"]):
                if self.controller.current_char_id is None:
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

    def _refresh_data(self) -> None:
        if not self.controller.current_char_id:
            return
        self.cache_status_var.set("Syncing…")

        def _on_success(data: CharacterData) -> None:
            self.after(0, lambda: self._apply_refresh_result(data))

        def _on_error(msg: str) -> None:
            self.after(0, lambda: self._apply_refresh_error(msg))

        self.controller.refresh_data_async(_on_success, _on_error)

    def _apply_refresh_result(self, data: CharacterData) -> None:
        if data.skills:
            self.current_skills = data.skills
            self.skill_view.set_skills(self.current_skills)
            self.total_sp_var.set(f"Total SP: {data.total_sp:,}")
            self.unallocated_sp_var.set(f"Unallocated SP: {data.unallocated_sp:,}")

        if data.queue:
            self.current_queue = data.queue
            self.queue_view.set_queue(self.current_queue, data.attributes or None)

        if data.attributes:
            self.current_attrs = data.attributes
            a = data.attributes
            i = a.get("intelligence", 0)
            m = a.get("memory",       0)
            p = a.get("perception",   0)
            w = a.get("willpower",    0)
            c = a.get("charisma",     0)
            self.queue_view.sp_min_var.set(
                f"Attributes: INT:{i} MEM:{m} PER:{p} WIL:{w} CHA:{c}")

        self.cache_status_var.set("Data synced with ESI")

    def _apply_refresh_error(self, msg: str) -> None:
        self.cache_status_var.set("Offline / Error")
        logger.error("Refresh failed: %s", msg)

    # ── Export ────────────────────────────────────────────────────────────────
    def _on_export(self, fmt: str) -> None:
        if not self.controller.current_char_id:
            messagebox.showwarning("Warning", "Select a character first")
            return

        char_name = self.char_title_var.get().replace(" ", "_")
        scope     = self.export_scope.get()
        scope_map = {
            "All Skills":      "skills_all",
            "Filtered Skills": "skills_filtered",
            "Skill Queue":     "queue",
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
                qc["name"]     = skills_db.get_skill_name(q.get("skill_id"))
                qc["category"] = skills_db.get_skill_category(q.get("skill_id")) or "Other"
                data.append(qc)
        else:
            data = []

        if fmt == "clipboard":
            res = self.export_manager.export(char_name, data_type, "Clipboard",
                                             data, tk_root=self)
            if res:
                messagebox.showinfo("Export", res)
            return

        # File-based formats
        ext_map = {"csv": ("CSV Files", "*.csv"), "markdown": ("Markdown", "*.md"),
                   "html": ("HTML Files", "*.html")}
        file_desc, file_ext = ext_map.get(fmt, ("All Files", "*.*"))
        ts    = datetime.now().strftime("%Y%m%d")
        fname = f"{char_name}_{data_type}_{ts}"
        path  = filedialog.asksaveasfilename(
            initialdir=str(PathManager.get_export_dir()),
            initialfile=f"{fname}.{fmt if fmt != 'markdown' else 'md'}",
            defaultextension=f".{fmt if fmt != 'markdown' else 'md'}",
            filetypes=[(file_desc, file_ext), ("All Files", "*.*")],
            title="Save Export As",
        )
        if path:
            res = self.export_manager.export(char_name, data_type, fmt,
                                             data, full_path=path)
            if res:
                messagebox.showinfo("Export", res)

    # ── Calculator popup ──────────────────────────────────────────────────────
    def _open_calculator(self) -> None:
        CalcWindow(self, self.current_attrs)

    # ── Misc ──────────────────────────────────────────────────────────────────
    def _open_skill_plan(self) -> None:
        SkillPlanManager(self, self.current_skills)

    def _on_about_click(self) -> None:
        top = tk.Toplevel(self)
        top.title("About")
        top.resizable(True, True)

        bg     = "#1c2230"
        fg     = "#e0e0e0"
        accent = "#3aa8d0"

        top.configure(bg=bg)
        main_f = tk.Frame(top, bg=bg, padx=30, pady=25)
        main_f.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_f, text="Personal Skill Monitor",
                 font=("Segoe UI", 16, "bold"), fg=accent, bg=bg).pack(pady=(0, 5))
        tk.Label(main_f, text="v0.3.0",
                 font=("Segoe UI", 10), fg="#888888", bg=bg).pack(pady=(0, 20))

        desc = ("Lightweight EVE Online skill management tool.\n"
                "Track skills, view queue, and plan your training.")
        tk.Label(main_f, text=desc, font=("Segoe UI", 10),
                 fg=fg, bg=bg, justify=tk.CENTER, wraplength=400).pack(pady=10)

        links = tk.Frame(main_f, bg=bg)
        links.pack(pady=20)

        def open_github(e=None):
            webbrowser.open("https://github.com/Fridman86/Personal-Skill-Monitor")

        lbl_git = tk.Label(links, text="GitHub Repository",
                           font=("Segoe UI", 10, "underline"),
                           fg=accent, bg=bg, cursor="hand2")
        lbl_git.pack(pady=5)
        lbl_git.bind("<Button-1>", open_github)

        def open_coffee(e=None):
            webbrowser.open("https://buymeacoffee.com/ifridman")

        coffee_frame = tk.Frame(links, bg="#FFDD00", padx=15, pady=8, cursor="hand2")
        coffee_frame.pack(pady=(15, 0))
        lbl_coffee = tk.Label(coffee_frame, text="☕ Buy me a coffee",
                              font=("Cookie", 12, "bold") if "Cookie" in tkfont.families()
                              else ("Segoe UI", 11, "bold"),
                              fg="#000000", bg="#FFDD00", cursor="hand2")
        lbl_coffee.pack()
        coffee_frame.bind("<Button-1>", open_coffee)
        lbl_coffee.bind("<Button-1>", open_coffee)

        btn_close = tk.Button(main_f, text="Close", command=top.destroy,
                              bg="#2a3044", fg=fg, bd=0, padx=20, pady=5,
                              cursor="hand2")
        btn_close.pack(pady=(30, 0))

        top.update_idletasks()
        top.minsize(top.winfo_reqwidth(), top.winfo_reqheight())
        w = top.winfo_reqwidth()
        h = top.winfo_reqheight()
        x = self.winfo_x() + (self.winfo_width()  // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        top.geometry(f"+{x}+{y}")

    def _on_quit(self) -> None:
        if messagebox.askyesno("Exit", "Exit Personal Skill Monitor?"):
            self._notif_monitor.stop()
            self.destroy()


# ── Training Time Calculator Window ──────────────────────────────────────────

class CalcWindow(tk.Toplevel):
    """
    Popup calculator for estimating skill training time.

    Shows:
      • Skill selector (searchable combobox)
      • From / To level spinboxes
      • Live attribute display (from last ESI fetch)
      • Calculated time per level and cumulative total
    """

    _ALL_SKILLS: list[str] | None = None  # cached sorted list

    def __init__(self, parent: EVEApp, attributes: dict) -> None:
        super().__init__(parent)
        self.parent_app = parent
        self.attributes = attributes or {}

        self.title("Training Time Calculator")
        self.geometry("520x480")
        self.minsize(460, 400)
        self.resizable(True, True)
        self.configure(bg=BG_MAIN)

        if CalcWindow._ALL_SKILLS is None:
            CalcWindow._ALL_SKILLS = sorted(
                name for sid, (name, grp, cat) in skills_db.SKILLS.items()
                if name != str(sid)
            )

        self._build_ui()
        self.transient(parent)
        self.focus_set()

    def _build_ui(self) -> None:
        # ── Header ──
        hdr = tk.Frame(self, bg=BG_PANEL)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="⏱  Training Time Calculator",
                 font=("Segoe UI", 13, "bold"),
                 fg=FG_BRIGHT, bg=BG_PANEL).pack(side=tk.LEFT, padx=15, pady=12)
        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X)

        body = tk.Frame(self, bg=BG_MAIN, padx=20, pady=15)
        body.pack(fill=tk.BOTH, expand=True)

        # ── Skill selector ──
        tk.Label(body, text="Skill:", font=("Segoe UI", 10),
                 fg=FG_DEFAULT, bg=BG_MAIN).grid(row=0, column=0, sticky=tk.W, pady=6)
        self._skill_var = tk.StringVar()
        skill_cb = ttk.Combobox(body, textvariable=self._skill_var,
                                values=CalcWindow._ALL_SKILLS, width=34)
        skill_cb.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=8, pady=6)
        skill_cb.bind("<<ComboboxSelected>>", lambda e: self._recalc())
        skill_cb.bind("<KeyRelease>", self._on_skill_key)
        Tooltip(skill_cb, "Start typing to filter skills.\nSelect to calculate training time.")

        # ── From / To levels ──
        tk.Label(body, text="From level:", font=("Segoe UI", 10),
                 fg=FG_DEFAULT, bg=BG_MAIN).grid(row=1, column=0, sticky=tk.W, pady=6)
        self._from_var = tk.IntVar(value=0)
        from_spin = ttk.Spinbox(body, from_=0, to=4, textvariable=self._from_var,
                                width=5, state="readonly",
                                command=self._recalc)
        from_spin.grid(row=1, column=1, sticky=tk.W, padx=8)

        tk.Label(body, text="To level:", font=("Segoe UI", 10),
                 fg=FG_DEFAULT, bg=BG_MAIN).grid(row=1, column=2, sticky=tk.W, padx=(20, 0))
        self._to_var = tk.IntVar(value=5)
        to_spin = ttk.Spinbox(body, from_=1, to=5, textvariable=self._to_var,
                              width=5, state="readonly",
                              command=self._recalc)
        to_spin.grid(row=1, column=3, sticky=tk.W, padx=8)

        # ── Attributes display ──
        tk.Frame(body, bg=BORDER, height=1).grid(
            row=2, column=0, columnspan=4, sticky=tk.EW, pady=12)

        tk.Label(body, text="Character Attributes",
                 font=("Segoe UI", 9, "bold"), fg=FG_TEAL, bg=BG_MAIN).grid(
            row=3, column=0, columnspan=4, sticky=tk.W)

        self._attr_var = tk.StringVar(value=self._fmt_attrs())
        tk.Label(body, textvariable=self._attr_var,
                 font=("Segoe UI", 9), fg=FG_DIM, bg=BG_MAIN).grid(
            row=4, column=0, columnspan=4, sticky=tk.W, pady=(2, 12))

        if not self.attributes:
            tk.Label(body, text="⚠  No attributes loaded — refresh data first.",
                     font=("Segoe UI", 9, "italic"), fg="#e08040", bg=BG_MAIN).grid(
                row=5, column=0, columnspan=4, sticky=tk.W)

        # ── Results ──
        tk.Frame(body, bg=BORDER, height=1).grid(
            row=6, column=0, columnspan=4, sticky=tk.EW, pady=8)

        tk.Label(body, text="Results",
                 font=("Segoe UI", 9, "bold"), fg=FG_TEAL, bg=BG_MAIN).grid(
            row=7, column=0, columnspan=4, sticky=tk.W)

        self._result_frame = tk.Frame(body, bg=BG_MAIN)
        self._result_frame.grid(row=8, column=0, columnspan=4, sticky=tk.EW, pady=4)

        self._result_var = tk.StringVar(value="Select a skill to calculate.")
        tk.Label(body, textvariable=self._result_var,
                 font=("Segoe UI", 10), fg=FG_BRIGHT, bg=BG_MAIN,
                 justify=tk.LEFT, wraplength=440).grid(
            row=9, column=0, columnspan=4, sticky=tk.W, pady=4)

        # ── SP/min info ──
        self._spm_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self._spm_var,
                 font=("Segoe UI", 9, "italic"), fg=FG_DIM, bg=BG_MAIN).grid(
            row=10, column=0, columnspan=4, sticky=tk.W)

        body.columnconfigure(1, weight=1)

    def _fmt_attrs(self) -> str:
        if not self.attributes:
            return "Not loaded"
        a = self.attributes
        return (f"INT:{a.get('intelligence',0)}  MEM:{a.get('memory',0)}  "
                f"PER:{a.get('perception',0)}  WIL:{a.get('willpower',0)}  "
                f"CHA:{a.get('charisma',0)}")

    def _on_skill_key(self, event: tk.Event) -> None:
        """Filter combobox list as user types."""
        typed = self._skill_var.get().lower()
        if not typed:
            filtered = CalcWindow._ALL_SKILLS
        else:
            filtered = [s for s in CalcWindow._ALL_SKILLS if typed in s.lower()]
        event.widget["values"] = filtered
        self._recalc()

    def _recalc(self) -> None:
        skill_name = self._skill_var.get().strip()
        from_lvl   = self._from_var.get()
        to_lvl     = self._to_var.get()

        if not skill_name or skill_name not in (CalcWindow._ALL_SKILLS or []):
            self._result_var.set("Select a valid skill.")
            self._spm_var.set("")
            return

        if from_lvl >= to_lvl:
            self._result_var.set("'From' level must be less than 'To' level.")
            self._spm_var.set("")
            return

        attrs = self.attributes
        if not attrs:
            # Use default 20 for all attributes if not loaded
            attrs = {k: 20 for k in
                     ("intelligence", "memory", "perception", "willpower", "charisma")}

        # Per-level breakdown
        lines = []
        total_secs = 0.0
        rank = get_skill_rank(skill_name)

        for lvl in range(from_lvl + 1, to_lvl + 1):
            secs = training_time(skill_name, lvl - 1, lvl, attrs)
            total_secs += secs
            sp_needed = (_SP_PER_LEVEL.get(lvl, 0) - _SP_PER_LEVEL.get(lvl - 1, 0)) * rank
            sp_needed = max(0, sp_needed)
            lines.append(
                f"  Level {lvl - 1} → {lvl}:  {format_duration(secs)}"
                f"  ({sp_needed:,} SP)"
            )

        lines.append(f"\n  ─────────────────────────────")
        lines.append(f"  Total:  {format_duration(total_secs)}")

        self._result_var.set("\n".join(lines))

        # SP/min info
        from src.utils.calculator import sp_per_minute
        spm = sp_per_minute(attrs, skill_name)
        self._spm_var.set(
            f"SP/min: {spm:.1f}  |  Rank: {rank}  |  "
            f"Attributes used: {self._fmt_attrs()}"
        )
