"""
Tooltip (підказка) widgets for tkinter.
- Tooltip: simple hover tooltip for any widget
- TreeviewTooltip: row-aware tooltip for ttk.Treeview
"""
import tkinter as tk
from tkinter import ttk


class Tooltip:
    """Attach a tooltip to any tkinter widget."""

    DELAY_MS = 600
    WRAP_LENGTH = 280

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
        try:
            tw.attributes("-topmost", True)
        except Exception:
            pass

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
    text_func(item_values) -> str | (title, description) | None
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
        self._mouse_x = 0
        self._mouse_y = 0

        treeview.bind("<Motion>", self._on_motion, add="+")
        treeview.bind("<Leave>", self._on_leave, add="+")
        treeview.bind("<ButtonPress>", self._on_leave, add="+")
        treeview.bind("<MouseWheel>", self._on_leave, add="+")

    def _on_motion(self, event):
        # Save mouse position as integers (event object may be recycled)
        mx = int(event.x_root)
        my = int(event.y_root)
        wy = int(event.y)
        self._mouse_x = mx
        self._mouse_y = my

        try:
            row_id = self.tree.identify_row(wy)
        except Exception:
            row_id = ""

        if row_id != self._current_row:
            self._hide()
            self._cancel_timer()
            self._current_row = row_id
            if row_id:
                self._after_id = self.tree.after(
                    self.DELAY_MS, self._try_show)

    def _on_leave(self, event=None):
        self._current_row = None
        self._cancel_timer()
        self._hide()

    def _cancel_timer(self):
        if self._after_id:
            try:
                self.tree.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _try_show(self):
        """Called after delay. Show tooltip if still on the same row."""
        self._after_id = None
        row_id = self._current_row
        if not row_id:
            return

        try:
            item = self.tree.item(row_id)
        except Exception:
            return

        values = item.get("values", ())
        if not values:
            # For tree-mode treeviews, try the text
            text = item.get("text", "")
            if text:
                values = (text,)
            else:
                return

        try:
            result = self.text_func(values)
        except Exception:
            return

        if not result:
            return

        if isinstance(result, tuple) and len(result) == 2:
            title, description = result
        else:
            title = None
            description = str(result)

        if not description:
            return

        self._show_popup(title, description)

    def _show_popup(self, title, description):
        if self._tw:
            return

        self._tw = tw = tk.Toplevel(self.tree)
        tw.wm_overrideredirect(True)
        try:
            tw.attributes("-topmost", True)
        except Exception:
            pass

        outer = tk.Frame(tw, bg="#2a3044", padx=1, pady=1)
        outer.pack()
        inner = tk.Frame(outer, bg=self.bg)
        inner.pack()

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

        # Position near the mouse
        tw.update_idletasks()
        tw_w = tw.winfo_reqwidth()
        tw_h = tw.winfo_reqheight()

        # Try to get current pointer position
        try:
            px = self.tree.winfo_pointerx()
            py = self.tree.winfo_pointery()
        except Exception:
            px = self._mouse_x
            py = self._mouse_y

        x = px + 16
        y = py + 16

        # Keep on screen
        screen_w = self.tree.winfo_screenwidth()
        screen_h = self.tree.winfo_screenheight()
        if x + tw_w > screen_w:
            x = px - tw_w - 8
        if y + tw_h > screen_h:
            y = py - tw_h - 8

        tw.wm_geometry(f"+{x}+{y}")

    def _hide(self):
        if self._tw:
            try:
                self._tw.destroy()
            except Exception:
                pass
            self._tw = None
