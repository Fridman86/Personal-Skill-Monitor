"""
Tooltip (подказка) widget for tkinter.
Shows a small popup with description text when the user hovers
over a widget for a configurable delay.
"""
import tkinter as tk


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
        self._tw = None       # Toplevel window
        self._after_id = None

        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._cancel, add="+")
        widget.bind("<ButtonPress>", self._cancel, add="+")

    # ── internal ──────────────────────────────────────
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
        # Position below and to the right of the cursor
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4

        self._tw = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)

        # Outer frame for border effect
        frame = tk.Frame(tw, bg="#2a3044", padx=1, pady=1)
        frame.pack()
        label = tk.Label(frame,
                         text=self.text,
                         justify=tk.LEFT,
                         background=self.bg,
                         foreground=self.fg,
                         relief="flat",
                         borderwidth=0,
                         font=self.font,
                         wraplength=self.WRAP_LENGTH,
                         padx=8, pady=5)
        label.pack()

    def _hide(self):
        if self._tw:
            self._tw.destroy()
            self._tw = None

    def update_text(self, new_text):
        """Change the tooltip text dynamically."""
        self.text = new_text
