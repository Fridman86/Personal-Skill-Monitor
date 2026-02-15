"""
Tooltip (підказка) widgets for tkinter.
- Tooltip: simple hover tooltip for any widget
- TreeviewTooltip: row-aware tooltip for ttk.Treeview
"""
import tkinter as tk
from tkinter import ttk


class Tooltip:
    """Attach a tooltip to any tkinter widget."""

    DELAY_MS = 600       # ms before tooltip appears
    WRAP_LENGTH = 280    # max text width in pixels

    def __init__(self, widget, text,
                 bg="#1c2230", fg="#c8d0e0",
                 font=("Segoe UI", 9)):
        self.widget = widget
        self.text = text
        self.bg = bg
        self.fg = fg
        self.font = font
        self._tw = None
        self._after_id = None

        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._cancel, add="+")
        widget.bind("<ButtonPress>", self._cancel, add="+")

    def _schedule(self, event=None):
        self._cancel()
        self._after_id = self.widget.after(self.DELAY_MS, self._show)

    def _cancel(self, event=None):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        self._hide()

    def _show(self):
        if self._tw or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4

        self._tw = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)

        frame = tk.Frame(tw, bg="#2a3044", padx=1, pady=1)
        frame.pack()
        tk.Label(frame, text=self.text,
                 justify=tk.LEFT, background=self.bg,
                 foreground=self.fg, relief="flat",
                 borderwidth=0, font=self.font,
                 wraplength=self.WRAP_LENGTH,
                 padx=8, pady=5).pack()

    def _hide(self):
        if self._tw:
            self._tw.destroy()
            self._tw = None

    def update_text(self, new_text):
        self.text = new_text


class TreeviewTooltip:
    """
    Row-aware tooltip for ttk.Treeview.

    Shows a tooltip when the user hovers over a row for DELAY_MS.
    The tooltip text is provided by a callback function:
        text_func(item_values) -> str | None
    where item_values is the tuple of column values for the hovered row.
    Return None or "" to suppress the tooltip for that row.
    """

    DELAY_MS = 500
    WRAP_LENGTH = 340

    def __init__(self, treeview, text_func,
                 bg="#1c2230", fg="#c8d0e0",
                 title_fg="#3aa8d0",
                 font=("Segoe UI", 9),
                 title_font=("Segoe UI", 10, "bold")):
        self.tree = treeview
        self.text_func = text_func
        self.bg = bg
        self.fg = fg
        self.title_fg = title_fg
        self.font = font
        self.title_font = title_font
        self._tw = None
        self._after_id = None
        self._current_row = None

        treeview.bind("<Motion>", self._on_motion, add="+")
        treeview.bind("<Leave>", self._on_leave, add="+")
        treeview.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_motion(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id != self._current_row:
            self._current_row = row_id
            self._cancel()
            if row_id:
                self._after_id = self.tree.after(
                    self.DELAY_MS,
                    lambda: self._show(event.x_root, event.y_root, row_id))

    def _on_leave(self, event=None):
        self._current_row = None
        self._cancel()

    def _cancel(self):
        if self._after_id:
            self.tree.after_cancel(self._after_id)
            self._after_id = None
        self._hide()

    def _show(self, x_root, y_root, row_id):
        if self._tw:
            return
        # Check row still exists and is still hovered
        if self._current_row != row_id:
            return
        try:
            item = self.tree.item(row_id)
        except tk.TclError:
            return

        values = item.get("values", ())
        text_or_parts = self.text_func(values)

        if not text_or_parts:
            return

        # text_func can return a string or a tuple of (title, description)
        if isinstance(text_or_parts, tuple) and len(text_or_parts) == 2:
            title, description = text_or_parts
        else:
            title = None
            description = str(text_or_parts)

        if not description:
            return

        self._tw = tw = tk.Toplevel(self.tree)
        tw.wm_overrideredirect(True)
        tw.attributes("-topmost", True)

        # Position: slightly below and to the right of cursor
        tw.wm_geometry(f"+{x_root + 16}+{y_root + 12}")

        outer = tk.Frame(tw, bg="#2a3044", padx=1, pady=1)
        outer.pack()
        inner = tk.Frame(outer, bg=self.bg)
        inner.pack(padx=0, pady=0)

        if title:
            tk.Label(inner, text=title,
                     justify=tk.LEFT, background=self.bg,
                     foreground=self.title_fg, relief="flat",
                     borderwidth=0, font=self.title_font,
                     wraplength=self.WRAP_LENGTH,
                     padx=10, pady=(6, 0), anchor="w").pack(fill=tk.X)

        tk.Label(inner, text=description,
                 justify=tk.LEFT, background=self.bg,
                 foreground=self.fg, relief="flat",
                 borderwidth=0, font=self.font,
                 wraplength=self.WRAP_LENGTH,
                 padx=10, pady=(3 if title else 6, 6),
                 anchor="w").pack(fill=tk.X)

    def _hide(self):
        if self._tw:
            self._tw.destroy()
            self._tw = None
