import time
import math
import random
from config import *
from ui_components import CenterCircle, StimulusCircle, Timer, RestScreen
from calibration_data_handler import CalibrationDataHandler
from eeg_data_handler import EEGDataHandler
from eeg_device import GNautilusDevice

# Safe optional tobii handler
try:
    from tobii_handler import TobiiHandler
except:
    class TobiiHandler:
        def is_available(self): return False
        def start_tracking(self, cb): pass
        def stop_tracking(self): pass


class BCIController:

    def __init__(self, canvas, username, status_callback=None):
        self.canvas = canvas
        self.status_callback = status_callback
        self.username = username

        # Data handlers
        self.calibration_handler = CalibrationDataHandler(username)
        self.eeg_handler = None
        
        # EEG device
        self.eeg_device = None

        self.width = WINDOW_WIDTH
        self.height = WINDOW_HEIGHT
        self.center_x = self.width // 2
        self.center_y = self.height // 2

        self.center_radius = self._calculate_center_radius()

        # UI Components
        self.center_circle = CenterCircle(canvas, self.center_x, self.center_y, self.center_radius)
        self.stimulus_circles = []
        self._create_stimulus_circles()
        self.timer = Timer(canvas)
        self.timer.reposition(self.height)
        self.rest_screen = RestScreen(canvas)
        self.rest_screen.reposition(self.width, self.height)

        # Input devices
        self.tobii = TobiiHandler()
        self.input_mode = INPUT_MODE_MOUSE
        self.mouse_x = self.center_x
        self.mouse_y = self.center_y
        self.gaze_x = self.center_x
        self.gaze_y = self.center_y

        # Phase and timing
        self.current_phase = PHASE_TESTING
        self.focus_time = DEFAULT_FOCUS_TIME
        self.gap_time = DEFAULT_GAP_TIME
        self.calibration_rounds = DEFAULT_CALIBRATION_ROUNDS

        # Calibration state
        self.calibration_active = False
        self.calibration_sequence = []
        self.current_calibration_index = 0
        self.calibration_start_time = None
        self.calibration_session_start = None
        self.calibration_completed_rounds = 0
        
        # Phase tracking
        self.is_in_starting_rest = False
        self.is_in_focus_phase = False
        self.is_in_ending_rest = False
        
        self.total_calibrations_done = 0
        self.circles_completed_in_round = 0

        # Tobii focus tracking
        self.tobii_focus_start_time = None
        self.tobii_currently_focused_circle = None

        self.last_time = time.time()
        self.running = False

    def _calculate_center_radius(self):
        return int(min(self.width, self.height - CONTROL_PANEL_HEIGHT) * CENTER_CIRCLE_RADIUS_RATIO)

    def _create_stimulus_circles(self):
        min_dimension = min(self.width, self.height - CONTROL_PANEL_HEIGHT)
        distance = int(min_dimension * STIMULUS_DISTANCE_RATIO)

        for angle_deg in STIMULUS_ANGLES:
            angle_rad = math.radians(angle_deg)
            x = self.center_x + distance * math.cos(angle_rad)
            y = self.center_y + distance * math.sin(angle_rad)
            self.stimulus_circles.append(
                StimulusCircle(self.canvas, len(self.stimulus_circles)+1, x, y, STIMULUS_CIRCLE_RADIUS)
            )

    # ============================================================
    # Input Mode Management
    # ============================================================
    def set_input_mode(self, mode):
        """Switch between Mouse, Tobii, and EEG input modes."""
        # Stop any active calibration when switching modes
        if self.calibration_active:
            self.stop_calibration()
        
        # Stop previous mode
        if self.input_mode == INPUT_MODE_TOBII:
            try:
                self.tobii.stop_tracking()
            except:
                pass
        elif self.input_mode == INPUT_MODE_EEG:
            try:
                if self.eeg_device:
                    self.eeg_device.stop_stream()
                    self.eeg_device.disconnect()
                    self.eeg_device = None
            except:
                pass
        
        self.input_mode = mode
        
        if mode == INPUT_MODE_TOBII:
            if self.tobii.is_available():
                self.tobii.start_tracking(self._on_gaze_update)
                self._update_status("Tobii Active", "success")
            else:
                self._update_status("Tobii Hardware Not Connected", "error")
                self.input_mode = INPUT_MODE_MOUSE
                
        elif mode == INPUT_MODE_EEG:
            # Initialize EEG - NO MOCK DEVICE
            try:
                # Only try real g.Nautilus device
                self.eeg_device = GNautilusDevice(channel_count=EEG_CHANNEL_COUNT)
                
                # Try to connect
                if self.eeg_device.connect():
                    if self.eeg_handler is None:
                        self.eeg_handler = EEGDataHandler(
                            self.username,
                            sampling_rate=self.eeg_device.get_sampling_rate(),
                            channel_count=self.eeg_device.get_channel_count()
                        )
                    
                    self._update_status(f"g.Nautilus Connected & Ready", "success")
                else:
                    self._update_status("EEG Hardware Not Connected", "error")
                    self.input_mode = INPUT_MODE_MOUSE
                    self.eeg_device = None
            except Exception as e:
                self._update_status("EEG Hardware Not Connected", "error")
                self.input_mode = INPUT_MODE_MOUSE
                self.eeg_device = None
        else:
            # Mouse mode
            self._update_status("Mouse Active", "info")

    def _on_gaze_update(self, norm_x, norm_y, gaze_data):
        """Callback from Tobii handler."""
        self.gaze_x = int(norm_x * self.width)
        self.gaze_y = int(norm_y * self.height)

        if (
            self.calibration_active
            and self.is_in_focus_phase
            and 0 <= self.current_calibration_index < len(self.calibration_sequence)
        ):
            glowing_circle_index = self.calibration_sequence[self.current_calibration_index]
            glowing_circle = glowing_circle_index + 1
            
            # Check if user is focusing on the glowing circle
            is_focusing_on_target = self._check_gaze_on_stimulus(glowing_circle_index, self.gaze_x, self.gaze_y)
            
            if is_focusing_on_target:
                if self.tobii_currently_focused_circle != glowing_circle:
                    # Started focusing on new circle
                    self.tobii_focus_start_time = time.time()
                    self.tobii_currently_focused_circle = glowing_circle
            else:
                # Not focusing on target
                self.tobii_focus_start_time = None
                self.tobii_currently_focused_circle = None
            
            # Log gaze data
            safe_data = {
                "timestamp": gaze_data.get("timestamp"),
                "avg_x": gaze_data.get("avg_x"),
                "avg_y": gaze_data.get("avg_y"),
                "left": gaze_data.get("left"),
                "right": gaze_data.get("right")
            }
            self.calibration_handler.log_gaze_data(safe_data, glowing_circle)

    def _check_gaze_on_stimulus(self, stimulus_index, gaze_x, gaze_y):
        """Check if gaze is on specific stimulus circle."""
        cx, cy = self.stimulus_circles[stimulus_index].get_position()
        dist = math.dist((gaze_x, gaze_y), (cx, cy))
        return dist <= TOBII_FOCUS_THRESHOLD

    def _on_eeg_sample(self, sample):
        """Callback from EEG device for each sample."""
        if self.eeg_handler and self.calibration_active:
            self.eeg_handler.add_sample(sample)

    def on_mouse_move(self, x, y):
        self.mouse_x = x
        self.mouse_y = y

    def get_current_position(self):
        if self.input_mode == INPUT_MODE_TOBII:
            return (self.gaze_x, self.gaze_y)
        else:
            return (self.mouse_x, self.mouse_y)

    # ============================================================
    # Phase and Settings
    # ============================================================
    def set_phase(self, phase):
        self.stop_calibration()
        self.current_phase = phase
        self._update_status(f"{phase} Active", "info")

    def set_focus_time(self, t):
        self.focus_time = t
        if self.eeg_handler:
            self.eeg_handler.set_timing_parameters(self.gap_time, self.focus_time)

    def set_gap_time(self, t):
        self.gap_time = t
        if self.eeg_handler:
            self.eeg_handler.set_timing_parameters(self.gap_time, self.focus_time)

    def set_calibration_rounds(self, r):
        self.calibration_rounds = r

    # ============================================================
    # Calibration Control
    # ============================================================
    def start_calibration(self):
        if self.current_phase != PHASE_CALIBRATION:
            self._update_status("Must switch to Calibration Phase", "error")
            return False

        # Initialize appropriate handler
        if self.input_mode == INPUT_MODE_EEG:
            if not self.eeg_device or not self.eeg_device.is_connected():
                self._update_status("EEG Hardware Not Connected", "error")
                return False
            
            if not self.eeg_handler:
                self._update_status("EEG Handler Not Initialized", "error")
                return False
            
            # Start EEG streaming
            try:
                if not self.eeg_device.start_stream(self._on_eeg_sample):
                    self._update_status("Failed to Start EEG Streaming", "error")
                    return False
            except Exception as e:
                self._update_status(f"EEG Start Error: {e}", "error")
                return False
            
            self.eeg_handler.set_timing_parameters(self.gap_time, self.focus_time)
            self.eeg_handler.start_calibration_index(1)
            
        elif self.input_mode == INPUT_MODE_TOBII:
            if not self.tobii.is_available():
                self._update_status("Tobii Hardware Not Connected", "error")
                return False
            
            if not self.calibration_handler.start_session():
                self._update_status("Cannot Start Session", "error")
                return False
        else:
            # Mouse mode
            if not self.calibration_handler.start_session():
                self._update_status("Cannot Start Session", "error")
                return False

        # Generate calibration sequence
        self.calibration_sequence = []
        for _ in range(self.calibration_rounds):
            seq = list(range(8))
            random.shuffle(seq)
            self.calibration_sequence.extend(seq)

        self.calibration_active = True
        self.current_calibration_index = 0
        self.circles_completed_in_round = 0
        self.calibration_completed_rounds = 1
        
        # Start with initial rest period
        self.is_in_starting_rest = True
        self.is_in_focus_phase = False
        self.is_in_ending_rest = False
        
        self.calibration_start_time = time.time()
        self.calibration_session_start = time.time()

        # Tobii focus tracking reset
        self.tobii_focus_start_time = None
        self.tobii_currently_focused_circle = None

        # Start collection for first circle
        first_circle = self.calibration_sequence[0] + 1
        if self.input_mode == INPUT_MODE_EEG:
            self.eeg_handler.start_circle_collection(first_circle)
            self.eeg_handler.set_phase("starting_rest")
        else:
            self.calibration_handler.start_circle_collection(first_circle, "starting_rest")

        # Show rest screen
        self.rest_screen.show()
        self._hide_main_ui()

        self.timer.show()
        self._update_status(f"Calibration Started: Round 1/{self.calibration_rounds}", "success")
        return True

    def stop_calibration(self):
        if not self.calibration_active:
            return

        self.calibration_active = False
        self._deactivate_all_stimuli()
        self.center_circle.return_dots_home()
        self.rest_screen.hide()
        self._show_main_ui()
        self.timer.hide()

        # Stop devices
        try:
            if self.input_mode == INPUT_MODE_EEG and self.eeg_device:
                self.eeg_device.stop_stream()
            else:
                self.calibration_handler.end_circle_focus()
                self.calibration_handler.end_session()
        except:
            pass

        self._update_status("Calibration Stopped", "warning")

    def _activate_stimulus(self, i):
        self._deactivate_all_stimuli()
        self.stimulus_circles[i].set_glow(True)

    def _deactivate_all_stimuli(self):
        for c in self.stimulus_circles:
            c.set_glow(False)

    def _hide_main_ui(self):
        """Hide circles during rest periods."""
        self.center_circle.hide()
        for circle in self.stimulus_circles:
            circle.hide()

    def _show_main_ui(self):
        """Show circles during focus periods."""
        self.center_circle.show()
        for circle in self.stimulus_circles:
            circle.show()

    # ============================================================
    # Helper: Check if hovering over any stimulus circle
    # ============================================================
    def _is_hovering_stimulus_circle(self, x, y):
        """Check if cursor/gaze is hovering over any stimulus circle."""
        for circle in self.stimulus_circles:
            cx, cy = circle.get_position()
            dist = math.dist((x, y), (cx, cy))
            if dist <= STIMULUS_HOVER_THRESHOLD:
                return True, circle
        return False, None

    # ============================================================
    # Animation and Calibration Updates
    # ============================================================
    def start_animation(self):
        self.running = True
        self.last_time = time.time()

    def stop_animation(self):
        self.running = False

    def update(self):
        if not self.running:
            return

        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        if self.calibration_active:
            self._update_calibration(now)
            elapsed = now - self.calibration_session_start
            self.timer.update(elapsed)

        elif self.current_phase == PHASE_TESTING:
            x, y = self.get_current_position()
            
            # Only move dots if hovering over a stimulus circle
            is_hovering, hovered_circle = self._is_hovering_stimulus_circle(x, y)
            
            if is_hovering and hovered_circle:
                target_x, target_y = hovered_circle.get_position()
                self.center_circle.move_dots_toward(target_x, target_y, 1.0)
            else:
                self.center_circle.return_dots_home()

        self.center_circle.update(dt)
        for c in self.stimulus_circles:
            c.update_animation(dt)

    def _update_calibration(self, now):
        """Handle calibration state machine with rest-focus-rest cycles."""
        elapsed = now - self.calibration_start_time
        
        # Phase 1: Starting Rest
        if self.is_in_starting_rest:
            remaining = self.gap_time - elapsed
            self.timer.update_countdown(remaining, "Rest")
            
            if elapsed >= self.gap_time:
                # Transition to focus phase
                self.is_in_starting_rest = False
                self.is_in_focus_phase = True
                self.calibration_start_time = now
                
                # Show main UI and activate circle
                self.rest_screen.hide()
                self._show_main_ui()
                
                idx = self.calibration_sequence[self.current_calibration_index]
                self._activate_stimulus(idx)
                
                if self.input_mode == INPUT_MODE_EEG:
                    self.eeg_handler.set_phase("focus")
                else:
                    circle_num = idx + 1
                    self.calibration_handler.start_circle_focus(circle_num, "focus")
        
        # Phase 2: Focus
        elif self.is_in_focus_phase:
            remaining = self.focus_time - elapsed
            self.timer.update_countdown(remaining, "Focus")
            
            # Dot animation
            if self.input_mode == INPUT_MODE_TOBII:
                # For Tobii: Only move dots if focused for TOBII_FOCUS_DURATION
                if (self.tobii_focus_start_time and 
                    (now - self.tobii_focus_start_time) >= TOBII_FOCUS_DURATION):
                    
                    index = self.calibration_sequence[self.current_calibration_index]
                    tx, ty = self.stimulus_circles[index].get_position()
                    focus_duration = now - self.tobii_focus_start_time
                    progress = min(1.0, focus_duration / (self.focus_time - TOBII_FOCUS_DURATION))
                    self.center_circle.move_dots_toward(tx, ty, progress)
                else:
                    # Not focused long enough - dots stay home
                    self.center_circle.return_dots_home()
            else:
                # For Mouse/EEG: Move dots after trigger time
                trigger = self.focus_time * DOT_MOVE_TRIGGER_RATIO
                if elapsed >= trigger:
                    index = self.calibration_sequence[self.current_calibration_index]
                    tx, ty = self.stimulus_circles[index].get_position()
                    remaining_time = max(0.001, self.focus_time - trigger)
                    progress = min(1.0, (elapsed - trigger) / remaining_time)
                    self.center_circle.move_dots_toward(tx, ty, progress)
            
            if elapsed >= self.focus_time:
                # Transition to ending rest
                self.is_in_focus_phase = False
                self.is_in_ending_rest = True
                self.calibration_start_time = now
                
                # Reset Tobii focus tracking
                self.tobii_focus_start_time = None
                self.tobii_currently_focused_circle = None
                
                # Hide main UI
                self._deactivate_all_stimuli()
                self.center_circle.return_dots_home()
                self._hide_main_ui()
                self.rest_screen.show()
                
                if self.input_mode == INPUT_MODE_EEG:
                    self.eeg_handler.set_phase("ending_rest")
                else:
                    try:
                        self.calibration_handler.end_circle_focus()
                        circle_num = self.calibration_sequence[self.current_calibration_index] + 1
                        self.calibration_handler.start_circle_collection(circle_num, "ending_rest")
                    except:
                        pass
        
        # Phase 3: Ending Rest
        elif self.is_in_ending_rest:
            remaining = self.gap_time - elapsed
            self.timer.update_countdown(remaining, "Rest")
            
            if elapsed >= self.gap_time:
                # Save data and move to next circle
                if self.input_mode == INPUT_MODE_EEG:
                    self.eeg_handler.save_circle_data()
                else:
                    self.calibration_handler.end_circle_focus()
                
                self.current_calibration_index += 1
                self.circles_completed_in_round += 1
                
                # Check if round complete
                if self.circles_completed_in_round >= 8:
                    self.circles_completed_in_round = 0
                    self.calibration_completed_rounds += 1
                    
                    if self.input_mode == INPUT_MODE_EEG:
                        self.eeg_handler.start_calibration_index(self.calibration_completed_rounds)
                    else:
                        self.calibration_handler.end_session()
                        self.calibration_handler.increment_session_number()
                        self.total_calibrations_done += 1
                        self.calibration_handler.generate_mapping_file(self.total_calibrations_done)
                
                # Check if all calibrations complete
                if self.current_calibration_index >= len(self.calibration_sequence):
                    self.calibration_active = False
                    self.rest_screen.hide()
                    self._show_main_ui()
                    self.timer.hide()
                    
                    if self.input_mode == INPUT_MODE_EEG:
                        self.eeg_device.stop_stream()
                    else:
                        self.calibration_handler.end_session()
                    
                    self._update_status("Calibration Complete", "success")
                    return
                
                # Start next circle
                idx = self.calibration_sequence[self.current_calibration_index]
                circle_num = idx + 1
                
                self.is_in_ending_rest = False
                self.is_in_starting_rest = True
                self.calibration_start_time = now
                
                if self.input_mode == INPUT_MODE_EEG:
                    self.eeg_handler.start_circle_collection(circle_num)
                    self.eeg_handler.set_phase("starting_rest")
                else:
                    self.calibration_handler.start_circle_collection(circle_num, "starting_rest")
                
                self._update_status(
                    f"Calibration: Round {self.calibration_completed_rounds}/{self.calibration_rounds}",
                    "info"
                )

    # ============================================================
    # Resize and Theme
    # ============================================================
    def resize(self, w, h):
        self.width = w
        self.height = h
        self.center_x = w // 2
        self.center_y = h // 2

        self.center_radius = self._calculate_center_radius()
        self.center_circle.resize(self.center_x, self.center_y, self.center_radius)

        min_dim = min(w, h - CONTROL_PANEL_HEIGHT)
        distance = int(min_dim * STIMULUS_DISTANCE_RATIO)

        for i, angle in enumerate(STIMULUS_ANGLES):
            rad = math.radians(angle)
            x = self.center_x + distance * math.cos(rad)
            y = self.center_y + distance * math.sin(rad)
            self.stimulus_circles[i].reposition(x, y)

        self.timer.reposition(h)
        self.rest_screen.reposition(w, h)

    def update_theme(self):
        try:
            self.canvas.config(bg=get_color('bg'))
        except:
            pass

        self.center_circle.update_theme()
        for c in self.stimulus_circles:
            c.update_theme()
        self.timer.update_theme()
        self.rest_screen.update_theme()

    # ============================================================
    # Status and Cleanup
    # ============================================================
    def _update_status(self, msg, level="info"):
        if self.status_callback:
            self.status_callback(msg, level)

    def cleanup(self):
        try:
            self.tobii.stop_tracking()
            if self.eeg_device:
                self.eeg_device.disconnect()
            if self.eeg_handler:
                self.eeg_handler.cleanup()
        except:
            pass
        print("Controller cleaned")