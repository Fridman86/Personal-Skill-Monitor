import tkinter as tk
from tkinter import ttk

# EVE / RIFT style color palette — refined
BG_MAIN = "#0e1017"      # Deep space black
BG_PANEL = "#141820"      # Panel background
BG_TABLE = "#181c26"      # Table background
BG_HEADER = "#1e2230"     # Table header
BG_SELECT = "#1a4a6a"     # Selected row highlight (deep teal)
BG_HOVER = "#222838"      # Hover highlight
FG_DEFAULT = "#c8ccd4"    # Light gray text
FG_BRIGHT = "#e8ecf4"     # Bright white text
FG_DIM = "#707888"        # Dimmed text
FG_TEAL = "#38a8d0"       # Accent teal
FG_BLUE = "#4cc8e8"       # Accent bright blue
FG_GOLD = "#d4a844"       # Gold accent for highlights
BORDER_SUBTLE = "#252a36"
BORDER_ACCENT = "#2a3a4a" # Subtle teal border


def setup_eve_dark_theme(style: ttk.Style):
    """Configures the ttk.Style for the EVE Dark theme."""
    style.theme_use('clam')

    # Common styles
    style.configure(".",
                    background=BG_MAIN,
                    foreground=FG_DEFAULT,
                    bordercolor=BORDER_SUBTLE,
                    font=("Segoe UI", 9))

    # Frames
    style.configure("TFrame", background=BG_MAIN)
    style.configure("Sidebar.TFrame", background=BG_PANEL)
    style.configure("Toolbar.TFrame", background=BG_PANEL, relief="flat")
    style.configure("Separator.TFrame", background=BORDER_SUBTLE)
    style.configure("Accent.TFrame", background=BORDER_ACCENT)

    # Labels
    style.configure("TLabel", background=BG_MAIN, foreground=FG_DEFAULT)
    style.configure("Header.TLabel",
                    font=("Segoe UI", 12, "bold"),
                    foreground=FG_BRIGHT,
                    background=BG_PANEL)
    style.configure("Sidebar.TLabel", background=BG_PANEL, foreground=FG_DEFAULT)
    style.configure("Title.TLabel",
                    font=("Segoe UI", 15, "bold"),
                    foreground=FG_BRIGHT,
                    background=BG_MAIN)
    style.configure("Stat.TLabel",
                    font=("Segoe UI", 9),
                    foreground=FG_TEAL,
                    background=BG_MAIN)
    style.configure("Dim.TLabel",
                    font=("Segoe UI", 8, "italic"),
                    foreground=FG_DIM,
                    background=BG_MAIN)

    # Buttons
    style.configure("TButton",
                    padding=(10, 6),
                    background="#252a36",
                    foreground=FG_DEFAULT,
                    borderwidth=1,
                    relief="flat")
    style.map("TButton",
              background=[('active', "#323844"), ('pressed', "#1a1d26")],
              foreground=[('active', FG_BRIGHT)])

    # Accent button (Export, Plan actions)
    style.configure("Accent.TButton",
                    padding=(12, 7),
                    background="#1a4060",
                    foreground=FG_BRIGHT,
                    borderwidth=1,
                    relief="flat",
                    font=("Segoe UI", 9, "bold"))
    style.map("Accent.TButton",
              background=[('active', "#225580"), ('pressed', "#143050")],
              foreground=[('active', "#ffffff")])

    # Flat action buttons for sidebar
    style.configure("Nav.TButton",
                    font=("Segoe UI", 10),
                    padding=(14, 10),
                    background=BG_PANEL,
                    foreground=FG_DEFAULT,
                    borderwidth=0,
                    relief="flat",
                    anchor="w")
    style.map("Nav.TButton",
              background=[('active', "#1e2430"), ('pressed', BG_MAIN)],
              foreground=[('active', FG_BLUE)])

    # Treeview (Tables)
    style.configure("Treeview",
                    background=BG_TABLE,
                    foreground=FG_DEFAULT,
                    fieldbackground=BG_TABLE,
                    rowheight=28,
                    borderwidth=0)
    style.configure("Treeview.Heading",
                    background=BG_HEADER,
                    foreground=FG_BRIGHT,
                    padding=(8, 5),
                    borderwidth=0,
                    relief="flat",
                    font=("Segoe UI", 9, "bold"))
    style.map("Treeview",
              background=[('selected', BG_SELECT)],
              foreground=[('selected', FG_BRIGHT)])
    style.map("Treeview.Heading",
              background=[('active', "#262c3a")])

    # Character list treeview (sidebar)
    style.configure("CharList.Treeview",
                    background=BG_PANEL,
                    foreground=FG_DEFAULT,
                    fieldbackground=BG_PANEL,
                    rowheight=32,
                    borderwidth=0)
    style.map("CharList.Treeview",
              background=[('selected', BG_SELECT)],
              foreground=[('selected', FG_BRIGHT)])

    # Combobox
    style.configure("TCombobox",
                    fieldbackground=BG_TABLE,
                    background="#252932",
                    foreground="#E0E0E0",
                    arrowcolor=FG_TEAL,
                    selectbackground=BG_SELECT,
                    selectforeground=FG_BRIGHT,
                    padding=4)

    style.map("TCombobox",
              foreground=[('readonly', "#E0E0E0"), ('disabled', "#505868")],
              fieldbackground=[('readonly', BG_TABLE), ('disabled', BG_PANEL)])

    # Entry
    style.configure("TEntry",
                    fieldbackground=BG_TABLE,
                    foreground=FG_DEFAULT,
                    insertcolor=FG_TEAL,
                    padding=4)

    # Checkbutton
    style.configure("TCheckbutton",
                    background=BG_MAIN,
                    foreground=FG_DEFAULT,
                    indicatorbackground=BG_TABLE,
                    indicatorforeground=FG_TEAL)
    style.map("TCheckbutton",
              background=[('active', BG_MAIN)],
              foreground=[('active', FG_TEAL)])

    # Scrollbar
    style.configure("Vertical.TScrollbar",
                    gripcount=0,
                    background="#1e2230",
                    troughcolor=BG_MAIN,
                    bordercolor=BG_MAIN,
                    arrowcolor=FG_TEAL,
                    width=10)
    style.map("Vertical.TScrollbar",
              background=[('active', "#2a3040")])

    # PanedWindow
    style.configure("TPanedwindow",
                    background=BG_MAIN)
    style.configure("Sash",
                    sashthickness=4,
                    gripcount=0)

    # Notebook (for tabs if needed)
    style.configure("TNotebook",
                    background=BG_MAIN,
                    borderwidth=0)
    style.configure("TNotebook.Tab",
                    background=BG_PANEL,
                    foreground=FG_DEFAULT,
                    padding=(16, 6),
                    borderwidth=0)
    style.map("TNotebook.Tab",
              background=[('selected', BG_TABLE), ('active', BG_HOVER)],
              foreground=[('selected', FG_BRIGHT), ('active', FG_TEAL)])

    # LabelFrame
    style.configure("TLabelframe",
                    background=BG_MAIN,
                    foreground=FG_DEFAULT,
                    bordercolor=BORDER_SUBTLE)
    style.configure("TLabelframe.Label",
                    background=BG_MAIN,
                    foreground=FG_TEAL,
                    font=("Segoe UI", 9, "bold"))

    # Spinbox
    style.configure("TSpinbox",
                    fieldbackground=BG_TABLE,
                    foreground=FG_DEFAULT,
                    arrowcolor=FG_TEAL,
                    padding=3)
