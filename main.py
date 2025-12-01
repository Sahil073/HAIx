# -*- coding: utf-8 -*-
# ===============================================
# FILE: main.py (UPDATED WITH UI CHANGES)
# Splash screen, pause menu, numbered circles, improved flow
# ===============================================

import tkinter as tk
from tkinter import ttk, messagebox
from config import *
from controller import BCIController


class SplashScreen:
    """Splash screen shown before main application."""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("BCI Experiments")
        self.window.geometry("600x400")
        self.window.configure(bg=get_color('bg'))
        self.window.overrideredirect(True)  # Remove window decorations
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (400 // 2)
        self.window.geometry(f"600x400+{x}+{y}")
        
        # Main title
        title = tk.Label(
            self.window,
            text="BCI EXPERIMENTS",
            font=("Segoe UI", 36, "bold"),
            bg=get_color('bg'),
            fg=get_color('text_primary')
        )
        title.pack(pady=(120, 20))
        
        # Subtitle
        subtitle = tk.Label(
            self.window,
            text="Powered by HAIx LAB, IITGN",
            font=("Segoe UI", 14),
            bg=get_color('bg'),
            fg=get_color('text_secondary')
        )
        subtitle.pack(pady=(0, 20))
        
        # Auto-close after 2.5 seconds
        self.window.after(2500, self.close)
    
    def close(self):
        """Close splash screen."""
        self.window.destroy()


class BCIApplication:
    """Main application with updated UI flow."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide main window initially
        
        # Show splash screen
        splash = SplashScreen(self.root)
        self.root.wait_window(splash.window)
        
        # Show main window
        self.root.deiconify()
        self.root.title("BCI Interface - Login")
        self.root.geometry(f"{600}x{350}")
        self.root.minsize(500, 300)
        self.root.configure(bg=get_color('bg'))

        # Username overlay
        overlay = self._create_username_overlay()
        self.root.wait_window(overlay)

        if not getattr(self, "username", None):
            self.root.destroy()
            return

        # Build UI
        self.root.title(f"BCI Interface - {self.username}")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._create_control_panel()
        self._create_canvas()

        self.controller = BCIController(
            self.canvas,
            self.username,
            status_callback=self._update_status,
            completion_callback=self._on_calibration_complete,
            pause_callback=self._show_pause_menu
        )
        
        self.controller.set_hardware_status_callback(self._on_hardware_status_change)

        self._bind_events()
        self.controller.start_animation()
        self._animate()
        
        # Start with mouse
        self._update_ui_for_input_mode(INPUT_MODE_MOUSE)
        self.controller.set_phase(PHASE_TESTING)

    # =====================================================================
    # USERNAME UI
    # =====================================================================

    def _create_username_overlay(self):
        overlay = tk.Frame(self.root, bg=get_color('control_bg'), relief="flat", bd=2)
        overlay.place(relx=0.5, rely=0.5, anchor="center")

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

    # =====================================================================
    # PAUSE MENU
    # =====================================================================

    def _show_pause_menu(self):
        """Show pause menu when calibration is interrupted."""
        pause_overlay = tk.Frame(self.root, bg=get_color('control_bg'), relief="flat", bd=2)
        pause_overlay.place(relx=0.5, rely=0.5, anchor="center")

        border_frame = tk.Frame(pause_overlay, bg=get_color('text_primary'), bd=2)
        border_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        content = tk.Frame(border_frame, bg=get_color('control_bg'))
        content.pack(fill="both", expand=True, padx=30, pady=30)

        title_label = tk.Label(
            content,
            text="CALIBRATION PAUSED",
            font=("Segoe UI", 18, "bold"),
            bg=get_color('control_bg'),
            fg=get_color('text_primary')
        )
        title_label.pack(pady=(10, 20))

        button_frame = tk.Frame(content, bg=get_color('control_bg'))
        button_frame.pack(pady=(10, 10))

        continue_button = tk.Button(
            button_frame,
            text="CONTINUE",
            command=lambda: self._on_pause_continue(pause_overlay),
            bg=get_color('button_bg'),
            fg=get_color('button_fg'),
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            padx=30,
            pady=12,
            cursor="hand2",
            activebackground=get_color('button_hover'),
            activeforeground=get_color('button_fg')
        )
        continue_button.pack(side="left", padx=10)

        restart_button = tk.Button(
            button_frame,
            text="RESTART",
            command=lambda: self._on_pause_restart(pause_overlay),
            bg=get_color('control_bg'),
            fg=get_color('text_primary'),
            font=("Segoe UI", 12, "bold"),
            relief="solid",
            borderwidth=2,
            padx=30,
            pady=12,
            cursor="hand2",
            activebackground=get_color('dropdown_hover'),
            activeforeground=get_color('text_primary')
        )
        restart_button.pack(side="left", padx=10)

    def _on_pause_continue(self, overlay):
        """Resume calibration from pause."""
        overlay.destroy()
        self.controller.resume_calibration()
        self._update_status("Calibration resumed", "info")

    def _on_pause_restart(self, overlay):
        """Restart calibration from beginning."""
        overlay.destroy()
        self.controller.stop_calibration()
        self.start_button.config(text="[>] START CALIBRATION")
        self._show_control_panel()
        self._update_status("Calibration restarted", "warning")

    # =====================================================================
    # CONTROL PANEL
    # =====================================================================

    def _create_control_panel(self):
        self.panel = tk.Frame(
            self.root,
            bg=get_color('control_bg'),
            height=80
        )
        self.panel.grid(row=0, column=0, sticky="ew")
        self.panel.grid_propagate(False)

        self._configure_ttk_style()

        container = tk.Frame(self.panel, bg=get_color('control_bg'))
        container.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        top_row = tk.Frame(container, bg=get_color('control_bg'))
        top_row.pack(fill="x", pady=(0, 10))

        self.status_label = tk.Label(
            top_row,
            text="[*] Ready",
            bg=get_color('control_bg'),
            fg=get_color('text_primary'),
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True)

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

        sep = tk.Frame(container, bg=get_color('text_primary'), height=1)
        sep.pack(fill="x", pady=(0, 10))

        controls_row = tk.Frame(container, bg=get_color('control_bg'))
        controls_row.pack(fill="x")

        # Input mode
        input_frame = tk.Frame(controls_row, bg=get_color('control_bg'))
        input_frame.pack(side="left", padx=5)
        
        tk.Label(
            input_frame,
            text="Input Mode:",
            bg=get_color('control_bg'),
            fg=get_color('text_secondary'),
            font=("Segoe UI", 9)
        ).pack(side="left", padx=(0, 5))
        
        self.input_mode_var = tk.StringVar(value=INPUT_MODE_MOUSE)
        self.input_mode_dropdown = ttk.Combobox(
            input_frame,
            textvariable=self.input_mode_var,
            values=INPUT_MODES,
            state="readonly",
            width=15,
            font=("Segoe UI", 9)
        )
        self.input_mode_dropdown.pack(side="left")
        self.input_mode_dropdown.bind("<<ComboboxSelected>>", self._on_input_mode_change)

        # Phase dropdown
        self.phase_frame = tk.Frame(controls_row, bg=get_color('control_bg'))
        self.phase_frame.pack(side="left", padx=5)
        
        tk.Label(
            self.phase_frame,
            text="Phase:",
            bg=get_color('control_bg'),
            fg=get_color('text_secondary'),
            font=("Segoe UI", 9)
        ).pack(side="left", padx=(0, 5))
        
        self.phase_var = tk.StringVar(value=PHASE_TESTING)
        self.phase_dropdown = ttk.Combobox(
            self.phase_frame,
            textvariable=self.phase_var,
            values=MOUSE_PHASES,
            state="readonly",
            width=15,
            font=("Segoe UI", 9)
        )
        self.phase_dropdown.pack(side="left")
        self.phase_dropdown.bind("<<ComboboxSelected>>", self._on_phase_change)

        # Timing Controls
        self.timing_frame = tk.Frame(controls_row, bg=get_color('control_bg'))

        # Focus
        focus_container = tk.Frame(self.timing_frame, bg=get_color('control_bg'))
        focus_container.pack(side="left", padx=5)
        
        tk.Label(
            focus_container,
            text="Focus:",
            bg=get_color('control_bg'),
            fg=get_color('text_secondary'),
            font=("Segoe UI", 9)
        ).pack(side="left", padx=(0, 5))
        
        self.focus_time_var = tk.StringVar(value=f"{DEFAULT_FOCUS_TIME}s")
        self.focus_dropdown = ttk.Combobox(
            focus_container,
            textvariable=self.focus_time_var,
            values=[f"{t}s" for t in FOCUS_TIME_OPTIONS],
            state="readonly",
            width=8,
            font=("Segoe UI", 9)
        )
        self.focus_dropdown.pack(side="left")
        self.focus_dropdown.bind("<<ComboboxSelected>>", self._on_focus_time_change)

        # Gap
        gap_container = tk.Frame(self.timing_frame, bg=get_color('control_bg'))
        gap_container.pack(side="left", padx=5)
        
        tk.Label(
            gap_container,
            text="Gap:",
            bg=get_color('control_bg'),
            fg=get_color('text_secondary'),
            font=("Segoe UI", 9)
        ).pack(side="left", padx=(0, 5))
        
        self.gap_time_var = tk.StringVar(value=f"{DEFAULT_GAP_TIME}s")
        self.gap_dropdown = ttk.Combobox(
            gap_container,
            textvariable=self.gap_time_var,
            values=[f"{t}s" for t in GAP_TIME_OPTIONS],
            state="readonly",
            width=8,
            font=("Segoe UI", 9)
        )
        self.gap_dropdown.pack(side="left")
        self.gap_dropdown.bind("<<ComboboxSelected>>", self._on_gap_time_change)

        # Rounds
        self.calibration_frame = tk.Frame(controls_row, bg=get_color('control_bg'))
        
        tk.Label(
            self.calibration_frame,
            text="Rounds:",
            bg=get_color('control_bg'),
            fg=get_color('text_secondary'),
            font=("Segoe UI", 9)
        ).pack(side="left", padx=(0, 5))
        
        self.calibration_rounds_var = tk.StringVar(value=str(DEFAULT_CALIBRATION_ROUNDS))
        self.calibration_dropdown = ttk.Combobox(
            self.calibration_frame,
            textvariable=self.calibration_rounds_var,
            values=[str(r) for r in CALIBRATION_ROUNDS_OPTIONS],
            state="readonly",
            width=8,
            font=("Segoe UI", 9)
        )
        self.calibration_dropdown.pack(side="left")
        self.calibration_dropdown.bind("<<ComboboxSelected>>", self._on_calibration_rounds_change)

    def _configure_ttk_style(self):
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

    def _create_canvas(self):
        self.canvas = tk.Canvas(
            self.root,
            bg=get_color('bg'),
            highlightthickness=0
        )
        self.canvas.grid(row=1, column=0, sticky="nsew")

    def _update_ui_for_input_mode(self, mode):
        """Update UI based on mode (mouse / tobii / eeg)."""
        self.timing_frame.pack_forget()
        self.calibration_frame.pack_forget()
        self.start_button.pack_forget()

        if mode == INPUT_MODE_MOUSE:
            self.phase_dropdown.config(values=MOUSE_PHASES)
            self.phase_var.set(PHASE_TESTING)
        elif mode == INPUT_MODE_TOBII:
            self.phase_dropdown.config(values=TOBII_PHASES)
            self.phase_var.set(PHASE_TESTING)
        elif mode == INPUT_MODE_EEG:
            self.phase_dropdown.config(values=EEG_PHASES)
            self.phase_var.set(PHASE_CALIBRATION)

        self._update_ui_for_phase(self.phase_var.get())

    def _update_ui_for_phase(self, phase):
        """Update when switching Testing/Calibration."""
        self.timing_frame.pack_forget()
        self.calibration_frame.pack_forget()
        self.start_button.pack_forget()

        if phase == PHASE_TESTING:
            return

        if phase == PHASE_CALIBRATION:
            mode = self.input_mode_var.get()

            if mode == INPUT_MODE_EEG:
                self.focus_dropdown.config(values=[f"{t}s" for t in EEG_FOCUS_TIME_OPTIONS])
                self.gap_dropdown.config(values=[f"{t}s" for t in EEG_GAP_TIME_OPTIONS])
                self.focus_time_var.set(f"{EEG_DEFAULT_FOCUS_TIME}s")
                self.gap_time_var.set(f"{EEG_DEFAULT_GAP_TIME}s")
            else:
                self.focus_dropdown.config(values=[f"{t}s" for t in FOCUS_TIME_OPTIONS])
                self.gap_dropdown.config(values=[f"{t}s" for t in GAP_TIME_OPTIONS])

            self.timing_frame.pack(side="left", padx=5)
            self.calibration_frame.pack(side="left", padx=5)
            self.start_button.pack(side="right", in_=self.status_label.master)

    def _bind_events(self):
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.root.bind("<Escape>", self._on_escape_key)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_escape_key(self, event):
        try:
            if self.controller.calibration_active:
                self.controller.pause_calibration()
            elif self.controller.current_phase == PHASE_TESTING:
                self._show_control_panel()
        except:
            pass

    def _on_mouse_move(self, event):
        try:
            self.controller.on_mouse_move(event.x, event.y)
        except:
            pass

    def _on_canvas_resize(self, event):
        try:
            self.controller.resize(event.width, event.height)
        except:
            pass

    def _on_hardware_status_change(self, hardware_connected):
        """Show toggle only when hardware is disconnected."""
        if hardware_connected:
            self.hardware_toggle.pack_forget()
            self.hardware_toggle_var.set(False)
            self.controller.set_allow_without_hardware(False)
        else:
            self.hardware_toggle.pack(side="right", padx=10, in_=self.status_label.master)

    def _on_hardware_toggle(self):
        """Re-apply input mode after toggling hardware setting."""
        allow = self.hardware_toggle_var.get()
        self.controller.set_allow_without_hardware(allow)
        mode = self.input_mode_var.get()
        self.controller.set_input_mode(mode)

    def _on_input_mode_change(self, event):
        mode = self.input_mode_var.get()
        self._update_ui_for_input_mode(mode)

        if mode == INPUT_MODE_EEG:
            self.controller.set_focus_time(EEG_DEFAULT_FOCUS_TIME)
            self.controller.set_gap_time(EEG_DEFAULT_GAP_TIME)

        try:
            self.controller.set_input_mode(mode)
        except:
            pass

    def _on_phase_change(self, event):
        phase = self.phase_var.get()
        self._update_ui_for_phase(phase)

        if phase == PHASE_TESTING:
            self._hide_control_panel()
        else:
            self._show_control_panel()

        try:
            self.controller.set_phase(phase)
        except:
            pass

    def _on_focus_time_change(self, event):
        try:
            self.controller.set_focus_time(float(self.focus_time_var.get().replace("s", "")))
        except:
            pass

    def _on_gap_time_change(self, event):
        try:
            self.controller.set_gap_time(float(self.gap_time_var.get().replace("s", "")))
        except:
            pass

    def _on_calibration_rounds_change(self, event):
        try:
            self.controller.set_calibration_rounds(int(self.calibration_rounds_var.get()))
        except:
            pass

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
                    self._update_status("Calibration running.", "info")
        except:
            pass

    def _on_calibration_complete(self):
        self.start_button.config(text="[>] START CALIBRATION")
        self._show_control_panel()
        self._update_status("Calibration Complete", "success")

    def _hide_control_panel(self):
        """Hide control panel during calibration/testing."""
        self.timing_frame.pack_forget()
        self.calibration_frame.pack_forget()
        self.start_button.pack_forget()
        self.panel.grid_remove()

    def _show_control_panel(self):
        self.panel.grid()

    def _on_closing(self):
        try:
            self.controller.cleanup()
        except:
            pass
        self.root.destroy()

    def _update_status(self, message, level="info"):
        indicators = {
            "info": "[*]",
            "success": "[+]",
            "error": "[!]",
            "warning": "[-]"
        }
        self.status_label.config(text=f"{indicators.get(level,'[*]')} {message}")

    def _animate(self):
        try:
            self.controller.update()
        except:
            pass
        self.root.after(FRAME_TIME, self._animate)

    def run(self):
        self.root.mainloop()


def main():
    print("=" * 60)
    print("         BCI EXPERIMENTS")
    print("    Powered by HAIx LAB, IITGN")
    print("=" * 60)
    print("Starting application...")

    app = BCIApplication()
    app.run()


if __name__ == "__main__":
    main()