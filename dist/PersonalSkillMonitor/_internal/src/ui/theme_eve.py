import tkinter as tk
from tkinter import ttk

# EVE / RIFT style color palette
BG_MAIN = "#101218"  # Near black
BG_PANEL = "#151820" # Slightly lighter dark gray
BG_TABLE = "#1a1d26" # Table background
BG_SELECT = "#2a4a5e" # Selected row highlight (slightly brighter teal)
FG_DEFAULT = "#D0D0D0" # Light gray
FG_BRIGHT = "#FFFFFF" # Pure white for headers/active
FG_TEAL = "#3AA6D0"   # Accent teal
FG_BLUE = "#4EC3E0"   # Accent blue
BORDER_SUBTLE = "#2a2e38"

def setup_eve_dark_theme(style: ttk.Style):
    """Configures the ttk.Style for the EVE Dark theme."""
    style.theme_use('clam')
    
    # Common styles
    style.configure(".", background=BG_MAIN, foreground=FG_DEFAULT, bordercolor=BORDER_SUBTLE, font=("Segoe UI", 9))
    
    # Frames
    style.configure("TFrame", background=BG_MAIN)
    style.configure("Sidebar.TFrame", background=BG_PANEL)
    style.configure("Toolbar.TFrame", background=BG_PANEL)
    style.configure("Separator.TFrame", background="#2a2e38")
    
    # Labels
    style.configure("TLabel", background=BG_MAIN, foreground=FG_DEFAULT)
    style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground=FG_BRIGHT)
    style.configure("Sidebar.TLabel", background=BG_PANEL, foreground=FG_DEFAULT)
    
    # Buttons
    style.configure("TButton", padding=5, background="#2a2e38", foreground=FG_DEFAULT)
    style.map("TButton",
              background=[('active', "#3a3f4b"), ('pressed', "#1a1d26")],
              foreground=[('active', FG_BRIGHT)])
    
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
              background=[('active', "#2a2e38"), ('pressed', BG_MAIN)],
              foreground=[('active', FG_BLUE)])

    # Treeview (Tables)
    style.configure("Treeview", 
                    background=BG_TABLE, 
                    foreground=FG_DEFAULT, 
                    fieldbackground=BG_TABLE, 
                    rowheight=28, 
                    borderwidth=0)
    style.configure("Treeview.Heading", 
                    background="#252932", 
                    foreground=FG_BRIGHT, 
                    padding=5, 
                    borderwidth=1, 
                    relief="flat")
    style.map("Treeview", 
              background=[('selected', BG_SELECT)],
              foreground=[('selected', FG_BRIGHT)])

    # Combobox
    style.configure("TCombobox", 
                    fieldbackground=BG_TABLE, 
                    background="#252932", 
                    foreground="#E0E0E0", 
                    arrowcolor=FG_TEAL,
                    selectbackground=BG_SELECT,
                    selectforeground=FG_BRIGHT)
    
    style.map("TCombobox",
              foreground=[('readonly', "#E0E0E0"), ('disabled', "#707070")],
              fieldbackground=[('readonly', BG_TABLE), ('disabled', BG_PANEL)])
    
    # Entry
    style.configure("TEntry", 
                    fieldbackground=BG_TABLE, 
                    foreground=FG_DEFAULT, 
                    insertcolor=FG_TEAL)
    
    # Checkbutton
    style.configure("TCheckbutton", background=BG_MAIN, foreground=FG_DEFAULT)
    style.map("TCheckbutton",
              background=[('active', BG_MAIN)],
              foreground=[('active', FG_TEAL)])

    # Scrollbar
    style.configure("Vertical.TScrollbar", 
                    gripcount=0, 
                    background="#252932", 
                    troughcolor=BG_MAIN, 
                    bordercolor=BG_MAIN, 
                    arrowcolor=FG_TEAL)
    style.map("Vertical.TScrollbar",
              background=[('active', "#3a3f4b")])
