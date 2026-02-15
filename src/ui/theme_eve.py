import tkinter as tk
from tkinter import ttk

# ──────────────────────────────────────────────────
# EVE Online / RIFT Intel Fusion — Dark theme palette
# ──────────────────────────────────────────────────
BG_MAIN      = "#0b0e14"   # Deep space black
BG_SIDEBAR   = "#10131a"   # Sidebar background
BG_PANEL     = "#141820"   # Panel / toolbar background
BG_TABLE     = "#161a24"   # Table rows
BG_HEADER    = "#1c2030"   # Table header row
BG_SELECT    = "#1a4060"   # Selected row
BG_HOVER     = "#1e2636"   # Hover on buttons / rows
BG_INPUT     = "#181e2a"   # Input fields / search
BG_BTN       = "#1c2230"   # Button background
BG_BTN_ACC   = "#1a3e5c"   # Accent button background
BORDER       = "#1e2436"   # Subtle borders
BORDER_LIGHT = "#2a3044"   # Slightly visible borders

FG_DEFAULT   = "#b8bcc8"   # Normal text
FG_BRIGHT    = "#e0e4f0"   # Bright text (headers, selected)
FG_DIM       = "#606878"   # Dimmed text (hints, status)
FG_TEAL      = "#3aa8d0"   # Accent teal
FG_CYAN      = "#4ec8e8"   # Accent cyan (active items)
FG_GOLD      = "#c8a040"   # Gold highlights
FG_GREEN     = "#40c878"   # Success / online status


def setup_eve_dark_theme(style: ttk.Style):
    """Configures the ttk.Style for the EVE Dark / RIFT theme."""
    style.theme_use("clam")

    # ── Root ──
    style.configure(".",
                    background=BG_MAIN,
                    foreground=FG_DEFAULT,
                    bordercolor=BORDER,
                    font=("Segoe UI", 9))

    # ── Frames ──
    style.configure("TFrame", background=BG_MAIN)
    style.configure("Sidebar.TFrame", background=BG_SIDEBAR)
    style.configure("Toolbar.TFrame", background=BG_PANEL)
    style.configure("Separator.TFrame", background=BORDER_LIGHT)

    # ── Labels ──
    style.configure("TLabel",
                    background=BG_MAIN,
                    foreground=FG_DEFAULT)
    style.configure("Header.TLabel",
                    font=("Segoe UI", 11, "bold"),
                    foreground=FG_TEAL,
                    background=BG_SIDEBAR)
    style.configure("SidebarItem.TLabel",
                    font=("Segoe UI", 10),
                    foreground=FG_DEFAULT,
                    background=BG_SIDEBAR,
                    padding=(12, 6))
    style.configure("Title.TLabel",
                    font=("Segoe UI", 14, "bold"),
                    foreground=FG_BRIGHT,
                    background=BG_PANEL)
    style.configure("Stat.TLabel",
                    font=("Segoe UI", 9),
                    foreground=FG_TEAL,
                    background=BG_MAIN)
    style.configure("Dim.TLabel",
                    font=("Segoe UI", 8, "italic"),
                    foreground=FG_DIM,
                    background=BG_MAIN)
    style.configure("Toolbar.TLabel",
                    background=BG_PANEL,
                    foreground=FG_DEFAULT)

    # ── Buttons ──
    style.configure("TButton",
                    padding=(10, 5),
                    background=BG_BTN,
                    foreground=FG_DEFAULT,
                    borderwidth=1,
                    relief="flat",
                    font=("Segoe UI", 9))
    style.map("TButton",
              background=[("active", BG_HOVER), ("pressed", BG_MAIN)],
              foreground=[("active", FG_BRIGHT)])

    # Accent button (Export, Plan actions)
    style.configure("Accent.TButton",
                    padding=(12, 6),
                    background=BG_BTN_ACC,
                    foreground=FG_BRIGHT,
                    borderwidth=0,
                    relief="flat",
                    font=("Segoe UI", 9, "bold"))
    style.map("Accent.TButton",
              background=[("active", "#225580"), ("pressed", "#143050")],
              foreground=[("active", "#ffffff")])

    # Navigation buttons (sidebar)
    style.configure("Nav.TButton",
                    font=("Segoe UI", 10),
                    padding=(14, 8),
                    background=BG_SIDEBAR,
                    foreground=FG_DEFAULT,
                    borderwidth=0,
                    relief="flat",
                    anchor="w")
    style.map("Nav.TButton",
              background=[("active", BG_HOVER), ("pressed", BG_MAIN)],
              foreground=[("active", FG_CYAN)])

    # ── Treeview (Main tables) ──
    style.configure("Treeview",
                    background=BG_TABLE,
                    foreground=FG_DEFAULT,
                    fieldbackground=BG_TABLE,
                    rowheight=30,
                    borderwidth=0)
    style.configure("Treeview.Heading",
                    background=BG_HEADER,
                    foreground=FG_BRIGHT,
                    padding=(6, 4),
                    borderwidth=0,
                    relief="flat",
                    font=("Segoe UI", 9, "bold"))
    style.map("Treeview",
              background=[("selected", BG_SELECT)],
              foreground=[("selected", FG_BRIGHT)])
    style.map("Treeview.Heading",
              background=[("active", "#242a3a")])

    # Sidebar character list
    style.configure("CharList.Treeview",
                    background=BG_SIDEBAR,
                    foreground=FG_DEFAULT,
                    fieldbackground=BG_SIDEBAR,
                    rowheight=34,
                    borderwidth=0,
                    font=("Segoe UI", 10))
    style.map("CharList.Treeview",
              background=[("selected", BG_SELECT)],
              foreground=[("selected", FG_BRIGHT)])

    # ── Combobox ──
    style.configure("TCombobox",
                    fieldbackground=BG_INPUT,
                    background=BG_BTN,
                    foreground=FG_DEFAULT,
                    arrowcolor=FG_TEAL,
                    selectbackground=BG_SELECT,
                    selectforeground=FG_BRIGHT,
                    padding=3)
    style.map("TCombobox",
              foreground=[("readonly", FG_DEFAULT), ("disabled", FG_DIM)],
              fieldbackground=[("readonly", BG_INPUT), ("disabled", BG_SIDEBAR)])

    # ── Entry ──
    style.configure("TEntry",
                    fieldbackground=BG_INPUT,
                    foreground=FG_DEFAULT,
                    insertcolor=FG_TEAL,
                    padding=3)

    # ── Checkbutton ──
    style.configure("TCheckbutton",
                    background=BG_MAIN,
                    foreground=FG_DEFAULT)
    style.map("TCheckbutton",
              background=[("active", BG_MAIN)],
              foreground=[("active", FG_TEAL)])

    # ── Scrollbar (thin, dark) ──
    style.configure("Vertical.TScrollbar",
                    gripcount=0,
                    background=BG_HEADER,
                    troughcolor=BG_MAIN,
                    bordercolor=BG_MAIN,
                    arrowcolor=FG_TEAL,
                    width=8)
    style.map("Vertical.TScrollbar",
              background=[("active", BG_HOVER)])

    # ── PanedWindow ──
    style.configure("TPanedwindow", background=BG_MAIN)

    # ── Notebook (tabs) ──
    style.configure("TNotebook",
                    background=BG_MAIN,
                    borderwidth=0)
    style.configure("TNotebook.Tab",
                    background=BG_PANEL,
                    foreground=FG_DEFAULT,
                    padding=(16, 5),
                    borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", BG_TABLE), ("active", BG_HOVER)],
              foreground=[("selected", FG_BRIGHT), ("active", FG_TEAL)])

    # ── LabelFrame ──
    style.configure("TLabelframe",
                    background=BG_MAIN,
                    foreground=FG_DEFAULT,
                    bordercolor=BORDER_LIGHT)
    style.configure("TLabelframe.Label",
                    background=BG_MAIN,
                    foreground=FG_TEAL,
                    font=("Segoe UI", 9, "bold"))

    # ── Spinbox ──
    style.configure("TSpinbox",
                    fieldbackground=BG_INPUT,
                    foreground=FG_DEFAULT,
                    arrowcolor=FG_TEAL,
                    padding=3)
