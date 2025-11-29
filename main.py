# ===============================================
# FILE: main.py
# BCI Interface Application - Main Entry Point
# Fixed: Dark mode now applies to entire window
# ===============================================

import tkinter as tk
from tkinter import ttk, messagebox
from config import *
from controller import BCIController


class BCIApplication:
    """Main application class with proper dark mode support."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BCI Interface - Login")
        self.root.geometry(f"{600}x{300}")
        self.root.minsize(500, 300)

        self.current_theme_name = THEME_LIGHT
        
        # Apply initial theme to root
        self.root.configure(bg=get_color('bg'))

        # Show username overlay
        overlay = self._create_username_overlay()
        self.root.wait_window(overlay)

        if not getattr(self, "username", None):
            self.root.destroy()
            return

        # Build full UI
        self.root.title(f"BCI Interface - {self.username}")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT + CONTROL_PANEL_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._create_control_panel()
        self._create_canvas()

        self.controller = BCIController(
            self.canvas,
            self.username,
            status_callback=self._update_status
        )

        self._bind_events()
        self.controller.start_animation()
        self._animate()
        self.controller.set_phase(PHASE_TESTING)
        self._apply_theme(LIGHT_THEME)

    # ==================== Username Overlay ====================
    def _create_username_overlay(self):
        overlay = tk.Frame(self.root, bg=get_color('control_bg'))
        overlay.place(relx=0.5, rely=0.5, anchor="center")

        title_label = tk.Label(
            overlay,
            text="Welcome to BCI Interface",
            font=("Segoe UI", 16, "bold"),
            bg=get_color('control_bg'),
            fg=get_color('text_primary')
        )
        title_label.pack(pady=(10, 6))

        subtitle_label = tk.Label(
            overlay,
            text="Please enter your username to begin",
            font=("Segoe UI", 10),
            bg=get_color('control_bg'),
            fg=get_color('text_secondary')
        )
        subtitle_label.pack(pady=(0, 12))

        entry_frame = tk.Frame(overlay, bg=get_color('control_bg'))
        entry_frame.pack(padx=20, pady=(0, 10), fill="x")

        tk.Label(
            entry_frame,
            text="Username:",
            font=("Segoe UI", 10),
            bg=get_color('control_bg'),
            fg=get_color('text_primary')
        ).pack(side="left", padx=(0, 8))

        self._username_var = tk.StringVar()
        username_entry = tk.Entry(
            entry_frame,
            textvariable=self._username_var,
            font=("Segoe UI", 10),
            width=25,
            relief="solid",
            borderwidth=1
        )
        username_entry.pack(side="left", fill="x", expand=True)
        username_entry.focus()

        button_frame = tk.Frame(overlay, bg=get_color('control_bg'))
        button_frame.pack(pady=(6, 10))

        ok_button = tk.Button(
            button_frame,
            text="Continue",
            command=lambda: self._submit_username(overlay),
            bg='#4CAF50',
            fg='white',
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        ok_button.pack(side="left", padx=6)

        cancel_button = tk.Button(
            button_frame,
            text="Exit",
            command=lambda: self._cancel_username(overlay),
            bg='#f44336',
            fg='white',
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        cancel_button.pack(side="left", padx=6)

        username_entry.bind("<Return>", lambda e: self._submit_username(overlay))

        return overlay

    def _submit_username(self, overlay):
        username = self._username_var.get().strip()
        if username:
            if all(c.isalnum() or c == '_' for c in username):
                self.username = username
                overlay.destroy()
            else:
                messagebox.showerror(
                    "Invalid Username",
                    "Username can only contain letters, numbers, and underscores.",
                    parent=self.root
                )
        else:
            messagebox.showwarning(
                "Username Required",
                "Please enter a username to continue.",
                parent=self.root
            )

    def _cancel_username(self, overlay):
        self.username = None
        overlay.destroy()

    # ==================== UI Creation ====================
    def _create_control_panel(self):
        """Create control panel with dynamic dropdowns."""
        self.panel = tk.Frame(
            self.root,
            bg=get_color('control_bg'),
            height=CONTROL_PANEL_HEIGHT
        )
        self.panel.grid(row=0, column=0, sticky="ew")
        self.panel.grid_propagate(False)

        self._configure_ttk_style()

        container = tk.Frame(self.panel, bg=get_color('control_bg'))
        container.pack(side="top", fill="x", padx=CONTROL_PADDING, pady=10)

        # Theme buttons
        theme_frame = tk.Frame(container, bg=get_color('control_bg'))
        theme_frame.pack(side="left", padx=(0, 20))

        self.light_btn = tk.Button(
            theme_frame, text="☀",
            command=lambda: self._switch_theme(THEME_LIGHT),
            bg="#FFFFFF", fg="#2D3142",
            font=("Segoe UI", 12), relief="flat",
            width=3, height=1, cursor="hand2", borderwidth=2
        )
        self.light_btn.pack(side="left", padx=2)

        self.dark_btn = tk.Button(
            theme_frame, text="🌙",
            command=lambda: self._switch_theme(THEME_DARK),
            bg="#2D3748", fg="#E2E8F0",
            font=("Segoe UI", 12), relief="flat",
            width=3, height=1, cursor="hand2", borderwidth=2
        )
        self.dark_btn.pack(side="left", padx=2)

        self.colorblind_btn = tk.Button(
            theme_frame, text="👁",
            command=lambda: self._switch_theme(THEME_COLORBLIND),
            bg="#E0E0E0", fg="#1A1A1A",
            font=("Segoe UI", 12), relief="flat",
            width=3, height=1, cursor="hand2", borderwidth=2
        )
        self.colorblind_btn.pack(side="left", padx=2)

        sep1 = tk.Frame(container, bg=get_color('text_secondary'), width=2)
        sep1.pack(side="left", fill="y", padx=10)

        # Input Mode
        self.input_mode_var = self._create_dropdown(
            container, "Input:", INPUT_MODE_MOUSE, INPUT_MODES,
            self._on_input_mode_change, width=12
        )

        # Phase
        self.phase_var = self._create_dropdown(
            container, "Phase:", PHASE_TESTING, PHASES,
            self._on_phase_change, width=12
        )

        # Focus time
        self.focus_time_label = tk.Label(
            container,
            text="Focus:",
            bg=get_color('control_bg'),
            fg=get_color('text_primary'),
            font=LABEL_FONT
        )
        self.focus_time_label.pack(side="left", padx=(5, 3))

        self.focus_time_var = tk.StringVar(value=f"{DEFAULT_FOCUS_TIME}s")
        self.focus_time_dropdown = ttk.Combobox(
            container,
            textvariable=self.focus_time_var,
            values=[f"{t}s" for t in FOCUS_TIME_OPTIONS],
            state="readonly",
            width=6,
            font=DROPDOWN_FONT
        )
        self.focus_time_dropdown.pack(side="left", padx=(0, 10))
        self.focus_time_dropdown.bind("<<ComboboxSelected>>", self._on_focus_time_change)

        # Gap time
        self.gap_time_label = tk.Label(
            container,
            text="Gap:",
            bg=get_color('control_bg'),
            fg=get_color('text_primary'),
            font=LABEL_FONT
        )
        self.gap_time_label.pack(side="left", padx=(5, 3))

        self.gap_time_var = tk.StringVar(value=f"{DEFAULT_GAP_TIME}s")
        self.gap_time_dropdown = ttk.Combobox(
            container,
            textvariable=self.gap_time_var,
            values=[f"{t}s" for t in GAP_TIME_OPTIONS],
            state="readonly",
            width=6,
            font=DROPDOWN_FONT
        )
        self.gap_time_dropdown.pack(side="left", padx=(0, 10))
        self.gap_time_dropdown.bind("<<ComboboxSelected>>", self._on_gap_time_change)

        # Calibration rounds
        self.calibration_rounds_label = tk.Label(
            container,
            text="Rounds:",
            bg=get_color('control_bg'),
            fg=get_color('text_primary'),
            font=LABEL_FONT
        )
        self.calibration_rounds_label.pack(side="left", padx=(5, 3))

        self.calibration_rounds_var = tk.StringVar(value=str(DEFAULT_CALIBRATION_ROUNDS))
        self.calibration_rounds_dropdown = ttk.Combobox(
            container,
            textvariable=self.calibration_rounds_var,
            values=[str(r) for r in CALIBRATION_ROUNDS_OPTIONS],
            state="readonly",
            width=6,
            font=DROPDOWN_FONT
        )
        self.calibration_rounds_dropdown.pack(side="left", padx=(0, 10))
        self.calibration_rounds_dropdown.bind("<<ComboboxSelected>>", self._on_calibration_rounds_change)

        sep2 = tk.Frame(container, bg=get_color('text_secondary'), width=2)
        sep2.pack(side="left", fill="y", padx=10)

        # Start button
        self.start_button = tk.Button(
            container,
            text="▶ Start",
            command=self._on_start_calibration,
            bg="#4CAF50",
            fg="white",
            font=BUTTON_FONT,
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2"
        )
        self.start_button.pack(side="left", padx=(0, 15))
        self.start_button.pack_forget()

        # Status label
        self.status_label = tk.Label(
            container,
            text="Status: Ready",
            bg=get_color('control_bg'),
            fg=get_color('text_primary'),
            font=STATUS_FONT,
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True)

    def _configure_ttk_style(self):
        """Configure ttk combobox style with current theme."""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass

        style.configure(
            'TCombobox',
            fieldbackground=get_color('dropdown_bg'),
            background=get_color('dropdown_bg'),
            foreground=get_color('text_primary'),
            arrowcolor=get_color('text_primary'),
            borderwidth=1,
            relief="solid"
        )
        style.map('TCombobox',
            fieldbackground=[('readonly', get_color('dropdown_bg'))],
            selectbackground=[('readonly', get_color('dropdown_hover'))],
            selectforeground=[('readonly', get_color('text_primary'))]
        )

    def _create_dropdown(self, parent, label_text, default_value, values, callback, width=10):
        """Helper to create labeled dropdown - stores label reference."""
        label = tk.Label(
            parent,
            text=label_text,
            bg=get_color('control_bg'),
            fg=get_color('text_primary'),
            font=LABEL_FONT
        )
        label.pack(side="left", padx=(5, 3))
        
        # Store label reference for theme updates
        if not hasattr(self, '_dropdown_labels'):
            self._dropdown_labels = []
        self._dropdown_labels.append(label)

        var = tk.StringVar(value=default_value)
        dropdown = ttk.Combobox(
            parent,
            textvariable=var,
            values=values,
            state="readonly",
            width=width,
            font=DROPDOWN_FONT
        )
        dropdown.pack(side="left", padx=(0, 10))
        dropdown.bind("<<ComboboxSelected>>", callback)

        return var

    def _create_canvas(self):
        """Create main canvas."""
        self.canvas = tk.Canvas(
            self.root,
            bg=get_color('bg'),
            highlightthickness=0
        )
        self.canvas.grid(row=1, column=0, sticky="nsew")

    # ==================== Event Handlers ====================
    def _bind_events(self):
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_mouse_move(self, event):
        try:
            self.controller.on_mouse_move(event.x, event.y)
        except:
            pass

    def _on_canvas_resize(self, event):
        if event.widget == self.canvas:
            try:
                self.controller.resize(event.width, event.height)
            except:
                pass

    def _on_input_mode_change(self, event):
        """Handle input mode change with dynamic dropdown updates."""
        mode = self.input_mode_var.get()
        
        if mode == INPUT_MODE_EEG:
            self.focus_time_dropdown['values'] = [f"{t}s" for t in EEG_FOCUS_TIME_OPTIONS]
            self.focus_time_var.set(f"{EEG_DEFAULT_FOCUS_TIME}s")
            self.gap_time_dropdown['values'] = [f"{t}s" for t in EEG_GAP_TIME_OPTIONS]
            self.gap_time_var.set(f"{EEG_DEFAULT_GAP_TIME}s")
            
            try:
                self.controller.set_focus_time(EEG_DEFAULT_FOCUS_TIME)
                self.controller.set_gap_time(EEG_DEFAULT_GAP_TIME)
            except:
                pass
        else:
            self.focus_time_dropdown['values'] = [f"{t}s" for t in FOCUS_TIME_OPTIONS]
            self.focus_time_var.set(f"{DEFAULT_FOCUS_TIME}s")
            self.gap_time_dropdown['values'] = [f"{t}s" for t in GAP_TIME_OPTIONS]
            self.gap_time_var.set(f"{DEFAULT_GAP_TIME}s")
            
            try:
                self.controller.set_focus_time(DEFAULT_FOCUS_TIME)
                self.controller.set_gap_time(DEFAULT_GAP_TIME)
            except:
                pass
        
        try:
            self.controller.set_input_mode(mode)
        except:
            pass

    def _on_focus_time_change(self, event):
        time_str = self.focus_time_var.get().replace('s', '')
        try:
            time_val = float(time_str)
            self.controller.set_focus_time(time_val)
        except:
            pass

    def _on_gap_time_change(self, event):
        time_str = self.gap_time_var.get().replace('s', '')
        try:
            time_val = float(time_str)
            self.controller.set_gap_time(time_val)
        except:
            pass

    def _on_calibration_rounds_change(self, event):
        rounds_str = self.calibration_rounds_var.get()
        try:
            rounds_val = int(rounds_str)
            self.controller.set_calibration_rounds(rounds_val)
        except:
            pass

    def _on_phase_change(self, event):
        phase = self.phase_var.get()
        try:
            self.controller.set_phase(phase)
        except:
            pass

        if phase == PHASE_CALIBRATION:
            self.start_button.pack(side="left", padx=(0, 15), before=self.status_label)
        else:
            self.start_button.pack_forget()

    def _on_start_calibration(self):
        try:
            if self.controller.calibration_active:
                self.controller.stop_calibration()
                self.start_button.config(text="▶ Start", bg="#4CAF50")
            else:
                if self.controller.start_calibration():
                    self.start_button.config(text="■ Stop", bg="#f44336")
        except:
            pass

    def _on_closing(self):
        try:
            if hasattr(self, 'controller'):
                self.controller.cleanup()
        except:
            pass
        self.root.destroy()

    # ==================== Theme Management ====================
    def _switch_theme(self, theme_name):
        """Switch UI theme with full application recoloring."""
        self.current_theme_name = theme_name

        if theme_name == THEME_LIGHT:
            theme = LIGHT_THEME
        elif theme_name == THEME_DARK:
            theme = DARK_THEME
        elif theme_name == THEME_COLORBLIND:
            theme = COLORBLIND_THEME
        else:
            theme = LIGHT_THEME

        self._apply_theme(theme)
        self._update_theme_buttons()

    def _apply_theme(self, theme):
        """Apply theme colors to entire application - FIXED."""
        global CURRENT_THEME
        CURRENT_THEME = theme

        # Root window background
        self.root.config(bg=theme['bg'])
        
        # Canvas background
        self.canvas.config(bg=theme['bg'])
        
        # Control panel background
        self.panel.config(bg=theme['control_bg'])

        # Update all labels in control panel
        if hasattr(self, '_dropdown_labels'):
            for label in self._dropdown_labels:
                try:
                    label.config(bg=theme['control_bg'], fg=theme['text_primary'])
                except:
                    pass
        
        # Update specific labels
        try:
            self.focus_time_label.config(bg=theme['control_bg'], fg=theme['text_primary'])
            self.gap_time_label.config(bg=theme['control_bg'], fg=theme['text_primary'])
            self.calibration_rounds_label.config(bg=theme['control_bg'], fg=theme['text_primary'])
            self.status_label.config(bg=theme['control_bg'])
        except:
            pass

        # Update all frames recursively
        self._update_frame_colors(self.panel, theme)

        # Update ttk styles
        self._configure_ttk_style()

        # Update controller visuals
        try:
            self.controller.update_theme()
        except:
            pass

    def _update_frame_colors(self, widget, theme):
        """Recursively update frame and container colors."""
        try:
            widget_class = widget.winfo_class()
            
            if widget_class in ('Frame', 'Labelframe'):
                widget.config(bg=theme['control_bg'])
            
            # Recurse to children
            for child in widget.winfo_children():
                self._update_frame_colors(child, theme)
        except:
            pass

    def _update_theme_buttons(self):
        """Highlight active theme button."""
        try:
            self.light_btn.config(relief="flat", borderwidth=1)
            self.dark_btn.config(relief="flat", borderwidth=1)
            self.colorblind_btn.config(relief="flat", borderwidth=1)
        except:
            pass

        if self.current_theme_name == THEME_LIGHT:
            self.light_btn.config(relief="solid", borderwidth=3)
        elif self.current_theme_name == THEME_DARK:
            self.dark_btn.config(relief="solid", borderwidth=3)
        elif self.current_theme_name == THEME_COLORBLIND:
            self.colorblind_btn.config(relief="solid", borderwidth=3)

    # ==================== Status ====================
    def _update_status(self, message, level="info"):
        """Update status bar with color coding."""
        colors = {
            "info": "#2196F3",
            "success": "#4CAF50",
            "error": "#f44336",
            "warning": "#FF9800"
        }

        try:
            self.status_label.config(
                text=f"Status: {message}",
                fg=colors.get(level, get_color('text_primary'))
            )
        except:
            pass

    # ==================== Animation ====================
    def _animate(self):
        """Animation loop."""
        try:
            self.controller.update()
        except:
            pass

        self.root.after(FRAME_TIME, self._animate)

    # ==================== Run App ====================
    def run(self):
        """Start the GUI event loop."""
        if hasattr(self, 'root'):
            self.root.mainloop()


# ==================== Entry Point ====================
def main():
    """Application entry point."""
    print("=" * 50)
    print("BCI Interface - Eye Tracking & EEG Calibration System")
    print("=" * 50)
    print("Starting application...")

    app = BCIApplication()
    app.run()


if __name__ == "__main__":
    main()