"""
Tooltip (підказка) widgets for tkinter.
- Tooltip: simple hover tooltip for any widget
- TreeviewTooltip: row-aware tooltip for ttk.Treeview (always-on polling)
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

    Uses always-on polling (every POLL_MS) to check mouse position.
    """

    DELAY_MS = 500       # hover time before showing tooltip
    POLL_MS = 150        # polling interval
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
        self._current_row = None
        self._dwell_ms = 0
        self._alive = True
        
        self._log("Initialized TreeviewTooltip")

        # Cleanup on widget destroy
        treeview.bind("<Destroy>", self._on_destroy, add="+")

        # Start polling immediately (delayed by 1s)
        treeview.after(1000, self._poll)

    def _log(self, msg):
        try:
            with open("/tmp/psm_debug.log", "a") as f:
                import datetime
                f.write(f"{datetime.datetime.now()} {msg}\n")
        except Exception:
            pass

    def _on_destroy(self, event=None):
        self._alive = False
        self._hide()

    def _poll(self):
        """Periodically check if mouse is over a treeview row."""
        if not self._alive:
            return

        try:
            # Is the tree widget visible and mapped?
            if not self.tree.winfo_ismapped():
                self.tree.after(self.POLL_MS, self._poll)
                return

            # Get mouse position relative to the treeview
            px = self.tree.winfo_pointerx()
            py = self.tree.winfo_pointery()
            rx = self.tree.winfo_rootx()
            ry = self.tree.winfo_rooty()
            tw = self.tree.winfo_width()
            th = self.tree.winfo_height()

            rel_x = px - rx
            rel_y = py - ry
            
            # self._log(f"Poll: ptr=({px},{py}) rel=({rel_x},{rel_y}) size=({tw},{th})")

            # Check if mouse is over the treeview area
            if 0 <= rel_x <= tw and 0 <= rel_y <= th:
                row_id = self.tree.identify_row(rel_y)

                if row_id:
                    if row_id == self._current_row:
                        # Still on the same row
                        self._dwell_ms += self.POLL_MS
                        if self._dwell_ms >= self.DELAY_MS and self._tw is None:
                            self._log(f"Triggering tooltip for row {row_id}")
                            self._show_tooltip(row_id, px, py)
                    else:
                        # Moved to a different row
                        self._hide()
                        self._current_row = row_id
                        self._dwell_ms = 0
                else:
                    # On heading or empty area
                    if self._current_row is not None:
                        self._hide()
                        self._current_row = None
                        self._dwell_ms = 0
            else:
                # Mouse not over the treeview
                if self._current_row is not None or self._tw is not None:
                    self._hide()
                    self._current_row = None
                    self._dwell_ms = 0

        except (tk.TclError, RuntimeError) as e:
            self._log(f"Poll error: {e}")
            self._alive = False
            return

        # Schedule next poll
        if self._alive:
            try:
                self.tree.after(self.POLL_MS, self._poll)
            except (tk.TclError, RuntimeError):
                self._alive = False

    def _show_tooltip(self, row_id, mouse_x, mouse_y):
        """Create and display the tooltip."""
        if self._tw is not None:
            return

        try:
            item = self.tree.item(row_id)
        except (tk.TclError, RuntimeError):
            return

        values = item.get("values", ())
        if not values:
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

        # Create tooltip window
        try:
            self._tw = tip = tk.Toplevel(self.tree)
            tip.wm_overrideredirect(True)
            try:
                tip.attributes("-topmost", True)
            except Exception:
                pass

            outer = tk.Frame(tip, bg="#2a3044", padx=1, pady=1)
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

            # Position tooltip near cursor
            tip.update_idletasks()
            tip_w = tip.winfo_reqwidth()
            tip_h = tip.winfo_reqheight()
            screen_w = self.tree.winfo_screenwidth()
            screen_h = self.tree.winfo_screenheight()

            x = mouse_x + 16
            y = mouse_y + 16
            if x + tip_w > screen_w:
                x = mouse_x - tip_w - 8
            if y + tip_h > screen_h:
                y = mouse_y - tip_h - 8

            tip.wm_geometry(f"+{x}+{y}")
        except (tk.TclError, RuntimeError):
            self._hide()

    def _hide(self):
        if self._tw is not None:
            try:
                self._tw.destroy()
            except Exception:
                pass
            self._tw = None
