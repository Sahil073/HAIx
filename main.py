# -*- coding: utf-8 -*-
# ===============================================
# FILE: main.py
# BCI Interface - Sleek Black & White Design
# with Collapsible Dropdown Controls
# ===============================================

import tkinter as tk
from tkinter import ttk, messagebox
from config import *
from controller import BCIController


class CollapsibleSection:
    """Collapsible section with smooth animation."""
    
    def __init__(self, parent, title, bg_color, fg_color):
        self.parent = parent
        self.is_open = False
        
        # Main container
        self.container = tk.Frame(parent, bg=bg_color)
        
        # Toggle button with arrow (using simple ASCII characters)
        self.toggle_btn = tk.Button(
            self.container,
            text=f"> {title}",
            command=self.toggle,
            bg=bg_color,
            fg=fg_color,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            anchor="w",
            cursor="hand2",
            padx=10,
            pady=5,
            activebackground="#1A1A1A",
            activeforeground=fg_color
        )
        self.toggle_btn.pack(fill="x")
        
        # Content frame (hidden by default)
        self.content = tk.Frame(self.container, bg=bg_color)
        self.title = title
        self.bg_color = bg_color
        self.fg_color = fg_color
    
    def toggle(self):
        """Toggle section open/closed."""
        if self.is_open:
            self.content.pack_forget()
            self.toggle_btn.config(text=f"> {self.title}")
            self.is_open = False
        else:
            self.content.pack(fill="x", padx=10, pady=(0, 10))
            self.toggle_btn.config(text=f"v {self.title}")
            self.is_open = True
    
    def pack(self, **kwargs):
        """Pack the container."""
        self.container.pack(**kwargs)


class BCIApplication:
    """Main application with sleek black & white design."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BCI Interface - Login")
        self.root.geometry(f"{600}x{350}")
        self.root.minsize(500, 300)
        self.root.configure(bg=get_color('bg'))

        # Show username overlay
        overlay = self._create_username_overlay()
        self.root.wait_window(overlay)

        if not getattr(self, "username", None):
            self.root.destroy()
            return

        # Build full UI
        self.root.title(f"BCI Interface - {self.username}")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT + 100}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._create_control_panel()
        self._create_canvas()

        self.controller = BCIController(
            self.canvas,
            self.username,
            status_callback=self._update_status,
            completion_callback=self._on_calibration_complete
        )
        
        # Set hardware status callback
        self.controller.set_hardware_status_callback(self._on_hardware_status_change)

        self._bind_events()
        self.controller.start_animation()
        self._animate()
        self.controller.set_phase(PHASE_TESTING)

    # ==================== Username Overlay ====================
    def _create_username_overlay(self):
        overlay = tk.Frame(self.root, bg=get_color('control_bg'), relief="flat", bd=2)
        overlay.place(relx=0.5, rely=0.5, anchor="center")

        # Add border effect
        border_frame = tk.Frame(overlay, bg=get_color('text_primary'), bd=2)
        border_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        content = tk.Frame(border_frame, bg=get_color('control_bg'))
        content.pack(fill="both", expand=True, padx=15, pady=15)

        title_label = tk.Label(
            content,
            text="BCI INTERFACE",
            font=("Segoe UI", 20, "bold"),
            bg=get_color('control_bg'),
            fg=get_color('text_primary')
        )
        title_label.pack(pady=(10, 5))

        subtitle_label = tk.Label(
            content,
            text="Enter your username to begin",
            font=("Segoe UI", 10),
            bg=get_color('control_bg'),
            fg=get_color('text_secondary')
        )
        subtitle_label.pack(pady=(0, 20))

        entry_frame = tk.Frame(content, bg=get_color('control_bg'))
        entry_frame.pack(padx=20, pady=(0, 20), fill="x")

        tk.Label(
            entry_frame,
            text="Username:",
            font=("Segoe UI", 10, "bold"),
            bg=get_color('control_bg'),
            fg=get_color('text_primary')
        ).pack(side="left", padx=(0, 10))

        self._username_var = tk.StringVar()
        username_entry = tk.Entry(
            entry_frame,
            textvariable=self._username_var,
            font=("Segoe UI", 11),
            width=25,
            relief="solid",
            borderwidth=2,
            bg=get_color('dropdown_bg'),
            fg=get_color('text_primary'),
            insertbackground=get_color('text_primary')
        )
        username_entry.pack(side="left", fill="x", expand=True, ipady=5)
        username_entry.focus()

        button_frame = tk.Frame(content, bg=get_color('control_bg'))
        button_frame.pack(pady=(10, 10))

        ok_button = tk.Button(
            button_frame,
            text="CONTINUE",
            command=lambda: self._submit_username(overlay),
            bg=get_color('button_bg'),
            fg=get_color('button_fg'),
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=25,
            pady=10,
            cursor="hand2",
            activebackground=get_color('button_hover'),
            activeforeground=get_color('button_fg')
        )
        ok_button.pack(side="left", padx=5)

        cancel_button = tk.Button(
            button_frame,
            text="EXIT",
            command=lambda: self._cancel_username(overlay),
            bg=get_color('control_bg'),
            fg=get_color('text_primary'),
            font=("Segoe UI", 10, "bold"),
            relief="solid",
            borderwidth=2,
            padx=25,
            pady=10,
            cursor="hand2",
            activebackground=get_color('dropdown_hover'),
            activeforeground=get_color('text_primary')
        )
        cancel_button.pack(side="left", padx=5)

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
        """Create modern collapsible control panel."""
        self.panel = tk.Frame(
            self.root,
            bg=get_color('control_bg'),
            height=100
        )
        self.panel.grid(row=0, column=0, sticky="ew")
        self.panel.grid_propagate(False)

        self._configure_ttk_style()

        # Main container with border
        container = tk.Frame(self.panel, bg=get_color('control_bg'))
        container.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # Top row - Status, Hardware Toggle, and Start button
        top_row = tk.Frame(container, bg=get_color('control_bg'))
        top_row.pack(fill="x", pady=(0, 10))

        # Status label (left)
        self.status_label = tk.Label(
            top_row,
            text="[*] Ready",
            bg=get_color('control_bg'),
            fg=get_color('text_primary'),
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        # Hardware toggle button (hidden by default)
        self.hardware_toggle_var = tk.BooleanVar(value=False)
        self.hardware_toggle = tk.Checkbutton(
            top_row,
            text="Allow Without Hardware",
            variable=self.hardware_toggle_var,
            command=self._on_hardware_toggle,
            bg=get_color('control_bg'),
            fg=get_color('text_primary'),
            selectcolor=get_color('dropdown_bg'),
            activebackground=get_color('control_bg'),
            activeforeground=get_color('text_primary'),
            font=("Segoe UI", 9),
            cursor="hand2"
        )
        # Hidden by default - will show when hardware is not detected
        
        # Start button (right)
        self.start_button = tk.Button(
            top_row,
            text="[>] START CALIBRATION",
            command=self._on_start_calibration,
            bg=get_color('button_bg'),
            fg=get_color('button_fg'),
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            activebackground=get_color('button_hover'),
            activeforeground=get_color('button_fg')
        )
        self.start_button.pack(side="right")
        self.start_button.pack_forget()

        # Separator
        sep = tk.Frame(container, bg=get_color('text_primary'), height=1)
        sep.pack(fill="x", pady=(0, 10))

        # Bottom row - Collapsible sections
        sections_row = tk.Frame(container, bg=get_color('control_bg'))
        sections_row.pack(fill="x")

        # Input Mode Section
        self.input_section = CollapsibleSection(
            sections_row, "Input Mode", 
            get_color('control_bg'), get_color('text_primary')
        )
        self.input_section.pack(side="left", fill="both", expand=True, padx=5)
        
        self.input_mode_var = self._create_dropdown_in_section(
            self.input_section.content, "Mode:", INPUT_MODE_MOUSE, INPUT_MODES,
            self._on_input_mode_change
        )

        # Phase Section
        self.phase_section = CollapsibleSection(
            sections_row, "Phase", 
            get_color('control_bg'), get_color('text_primary')
        )
        self.phase_section.pack(side="left", fill="both", expand=True, padx=5)
        
        self.phase_var = self._create_dropdown_in_section(
            self.phase_section.content, "Phase:", PHASE_TESTING, PHASES,
            self._on_phase_change
        )

        # Timing Section
        self.timing_section = CollapsibleSection(
            sections_row, "Timing", 
            get_color('control_bg'), get_color('text_primary')
        )
        self.timing_section.pack(side="left", fill="both", expand=True, padx=5)
        
        timing_content = self.timing_section.content
        
        # Focus time
        focus_frame = tk.Frame(timing_content, bg=get_color('control_bg'))
        focus_frame.pack(fill="x", pady=2)
        
        self.focus_time_var = self._create_dropdown_in_section(
            focus_frame, "Focus:", f"{DEFAULT_FOCUS_TIME}s",
            [f"{t}s" for t in FOCUS_TIME_OPTIONS],
            self._on_focus_time_change
        )
        
        # Gap time
        gap_frame = tk.Frame(timing_content, bg=get_color('control_bg'))
        gap_frame.pack(fill="x", pady=2)
        
        self.gap_time_var = self._create_dropdown_in_section(
            gap_frame, "Gap:", f"{DEFAULT_GAP_TIME}s",
            [f"{t}s" for t in GAP_TIME_OPTIONS],
            self._on_gap_time_change
        )

        # Calibration Section
        self.calibration_section = CollapsibleSection(
            sections_row, "Calibration", 
            get_color('control_bg'), get_color('text_primary')
        )
        self.calibration_section.pack(side="left", fill="both", expand=True, padx=5)
        
        self.calibration_rounds_var = self._create_dropdown_in_section(
            self.calibration_section.content, "Rounds:", str(DEFAULT_CALIBRATION_ROUNDS),
            [str(r) for r in CALIBRATION_ROUNDS_OPTIONS],
            self._on_calibration_rounds_change
        )

    def _configure_ttk_style(self):
        """Configure ttk combobox style."""
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

    def _create_dropdown_in_section(self, parent, label_text, default_value, values, callback):
        """Create labeled dropdown in collapsible section."""
        frame = tk.Frame(parent, bg=get_color('control_bg'))
        frame.pack(fill="x", pady=2)
        
        label = tk.Label(
            frame,
            text=label_text,
            bg=get_color('control_bg'),
            fg=get_color('text_secondary'),
            font=("Segoe UI", 9),
            anchor="w",
            width=8
        )
        label.pack(side="left", padx=(5, 5))

        var = tk.StringVar(value=default_value)
        dropdown = ttk.Combobox(
            frame,
            textvariable=var,
            values=values,
            state="readonly",
            width=12,
            font=("Segoe UI", 9)
        )
        dropdown.pack(side="left", fill="x", expand=True)
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
        self.root.bind("<Escape>", self._on_escape_key)  # ESC key to stop calibration
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_escape_key(self, event):
        """Handle ESC key to stop calibration."""
        try:
            if self.controller.calibration_active:
                self.controller.stop_calibration()
                self.start_button.config(text="[>] START CALIBRATION")
                self._show_control_panel()
                self._update_status("Calibration stopped (ESC pressed)", "warning")
        except:
            pass

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

    def _on_hardware_status_change(self, hardware_connected):
        """Callback when hardware connection status changes."""
        if hardware_connected:
            # Hardware is connected - hide toggle button
            self.hardware_toggle.pack_forget()
            self.hardware_toggle_var.set(False)
            self.controller.set_allow_without_hardware(False)
        else:
            # Hardware NOT connected - show toggle button
            self.hardware_toggle.pack(side="right", padx=10)

    def _on_hardware_toggle(self):
        """Handle hardware toggle button."""
        allow = self.hardware_toggle_var.get()
        try:
            self.controller.set_allow_without_hardware(allow)
        except:
            pass

    def _on_input_mode_change(self, event):
        """Handle input mode change."""
        mode = self.input_mode_var.get()
        
        # Update timing dropdowns based on mode
        if mode == INPUT_MODE_EEG:
            try:
                self.controller.set_focus_time(EEG_DEFAULT_FOCUS_TIME)
                self.controller.set_gap_time(EEG_DEFAULT_GAP_TIME)
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
            self.start_button.pack(side="right")
        else:
            self.start_button.pack_forget()

    def _on_start_calibration(self):
        try:
            if self.controller.calibration_active:
                self.controller.stop_calibration()
                self.start_button.config(text="[>] START CALIBRATION")
                self._show_control_panel()
            else:
                if self.controller.start_calibration():
                    self.start_button.config(text="[X] STOP CALIBRATION")
                    self._hide_control_panel()
                    self._update_status("Calibration running... Press ESC to stop", "info")
        except:
            pass

    def _on_calibration_complete(self):
        """Called when calibration completes automatically."""
        self.start_button.config(text="[>] START CALIBRATION")
        self._show_control_panel()
        self._update_status("Calibration Complete!", "success")

    def _hide_control_panel(self):
        """Hide the entire control panel during calibration."""
        self.panel.grid_remove()

    def _show_control_panel(self):
        """Show the control panel when calibration stops."""
        self.panel.grid()

    def _on_closing(self):
        try:
            if hasattr(self, 'controller'):
                self.controller.cleanup()
        except:
            pass
        self.root.destroy()

    # ==================== Status ====================
    def _update_status(self, message, level="info"):
        """Update status with modern indicators."""
        indicators = {
            "info": "[*]",
            "success": "[+]",
            "error": "[!]",
            "warning": "[-]"
        }

        try:
            indicator = indicators.get(level, "[*]")
            self.status_label.config(text=f"{indicator} {message}")
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
    print("=" * 60)
    print("         BCI INTERFACE - BLACK & WHITE EDITION")
    print("    Eye Tracking & EEG Calibration System")
    print("=" * 60)
    print("Starting application...")

    app = BCIApplication()
    app.run()


if __name__ == "__main__":
    main()