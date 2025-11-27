import time
import math
import random
from config import *
from ui_components import CenterCircle, StimulusCircle, Timer
from calibration_data_handler import CalibrationDataHandler

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

        self.calibration_handler = CalibrationDataHandler(username)

        self.width = WINDOW_WIDTH
        self.height = WINDOW_HEIGHT
        self.center_x = self.width // 2
        self.center_y = self.height // 2

        self.center_radius = self._calculate_center_radius()

        self.center_circle = CenterCircle(canvas, self.center_x, self.center_y, self.center_radius)
        self.stimulus_circles = []
        self._create_stimulus_circles()

        self.timer = Timer(canvas)
        self.timer.reposition(self.height)

        self.tobii = TobiiHandler()
        self.input_mode = INPUT_MODE_MOUSE
        self.mouse_x = self.center_x
        self.mouse_y = self.center_y
        self.gaze_x = self.center_x
        self.gaze_y = self.center_y

        self.current_phase = PHASE_TESTING
        self.focus_time = DEFAULT_FOCUS_TIME
        self.gap_time = DEFAULT_GAP_TIME
        self.calibration_rounds = DEFAULT_CALIBRATION_ROUNDS

        self.calibration_active = False
        self.calibration_sequence = []
        self.current_calibration_index = 0
        self.calibration_start_time = None
        self.calibration_session_start = None
        self.calibration_completed_rounds = 0
        self.is_in_glow_phase = False
        self.is_in_gap_phase = False

        self.total_calibrations_done = 0

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

    # -------------------------------------------------------------
    # Tracking
    # -------------------------------------------------------------
    def set_input_mode(self, mode):
        self.input_mode = mode
        if mode == INPUT_MODE_TOBII:
            if self.tobii.is_available():
                self.tobii.start_tracking(self._on_gaze_update)
                self._update_status("Tobii Active", "success")
            else:
                self._update_status("Tobii Not Available", "error")
                self.input_mode = INPUT_MODE_MOUSE
        else:
            try:
                self.tobii.stop_tracking()
            except:
                pass
            self._update_status("Mouse Active", "info")

    def _on_gaze_update(self, norm_x, norm_y, gaze_data):
        """Callback from Tobii handler with normalized gaze data."""

        # Convert norm coords → screen coords
        self.gaze_x = int(norm_x * self.width)
        self.gaze_y = int(norm_y * self.height)

        # ------------------------------------------------------------------
        # LOG ONLY WHEN:
        # - calibration is active
        # - we are in glow phase
        # - we know which circle is glowing
        # ------------------------------------------------------------------
        if (
            self.calibration_active
            and self.is_in_glow_phase
            and 0 <= self.current_calibration_index < len(self.calibration_sequence)
        ):
            glowing_circle = self.calibration_sequence[self.current_calibration_index] + 1

            # Extract Tobii data correctly
            safe_data = {
                "timestamp": gaze_data.get("timestamp"),
                "avg_x": gaze_data.get("avg_x"),
                "avg_y": gaze_data.get("avg_y"),
                "left": gaze_data.get("left"),
                "right": gaze_data.get("right")
            }

            self.calibration_handler.log_gaze_data(safe_data, glowing_circle)

    def on_mouse_move(self, x, y):
        self.mouse_x = x
        self.mouse_y = y

    def get_current_position(self):
        return (self.gaze_x, self.gaze_y) if self.input_mode == INPUT_MODE_TOBII else (self.mouse_x, self.mouse_y)

    # -------------------------------------------------------------
    # Phase
    # -------------------------------------------------------------
    def set_phase(self, phase):
        self.stop_calibration()
        self.current_phase = phase
        self._update_status(f"{phase} Active", "info")

    def set_focus_time(self, t): self.focus_time = t
    def set_gap_time(self, t): self.gap_time = t
    def set_calibration_rounds(self, r): self.calibration_rounds = r

    # -------------------------------------------------------------
    # Calibration
    # -------------------------------------------------------------
    def start_calibration(self):
        if self.current_phase != PHASE_CALIBRATION:
            self._update_status("Must switch to Calibration Phase", "error")
            return False

        if not self.calibration_handler.start_session():
            self._update_status("Cannot Start Session", "error")
            return False

        self.calibration_sequence = []
        for _ in range(self.calibration_rounds):
            seq = list(range(8))
            random.shuffle(seq)
            self.calibration_sequence.extend(seq)

        self.calibration_active = True
        self.current_calibration_index = 0
        self.is_in_glow_phase = True
        self.is_in_gap_phase = False
        self.calibration_start_time = time.time()
        self.calibration_session_start = time.time()

        first = self.calibration_sequence[0]
        self._activate_stimulus(first)
        self.calibration_handler.start_circle_focus(first + 1)

        self.timer.show()
        self._update_status("Calibration Started", "success")
        return True

    def stop_calibration(self):
        if not self.calibration_active:
            return

        self.calibration_active = False
        self._deactivate_all_stimuli()
        self.center_circle.return_dots_home()
        self.timer.hide()

        try:
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

    # -------------------------------------------------------------
    # Animation + Calibration Update
    # -------------------------------------------------------------
    def start_animation(self):
        self.running = True
        self.last_time = time.time()

    def stop_animation(self):
        self.running = False

    def update(self):
        if not self.running: return

        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        # Calibration active
        if self.calibration_active:
            self._update_calibration(now)
            elapsed = now - self.calibration_session_start
            self.timer.update(elapsed)

        elif self.current_phase == PHASE_TESTING:
            x, y = self.get_current_position()
            if math.dist((x, y), (self.center_x, self.center_y)) > self.center_radius:
                self.center_circle.move_dots_toward(x, y, 1.0)
            else:
                self.center_circle.return_dots_home()

        self.center_circle.update(dt)

        for c in self.stimulus_circles:
            c.update_animation(dt)

    def _update_calibration(self, now):
        elapsed = now - self.calibration_start_time

        if self.is_in_glow_phase:
            trigger = self.focus_time * DOT_MOVE_TRIGGER_RATIO
            if elapsed >= trigger:
                index = self.calibration_sequence[self.current_calibration_index]
                tx, ty = self.stimulus_circles[index].get_position()
                remaining = max(0.001, self.focus_time - trigger)
                progress = min(1.0, (elapsed - trigger) / remaining)
                self.center_circle.move_dots_toward(tx, ty, progress)

            if elapsed >= self.focus_time:
                self.is_in_glow_phase = False
                self.is_in_gap_phase = True
                self.calibration_start_time = now
                self._deactivate_all_stimuli()
                self.center_circle.return_dots_home()

                try: self.calibration_handler.end_circle_focus()
                except: pass

        elif self.is_in_gap_phase:
            if elapsed >= self.gap_time:
                self.current_calibration_index += 1

                if self.current_calibration_index >= len(self.calibration_sequence):
                    self.calibration_active = False
                    self._deactivate_all_stimuli()
                    self.timer.hide()

                    self.calibration_handler.end_session()
                    self.calibration_handler.increment_session_number()
                    self.total_calibrations_done += 1
                    self.calibration_handler.generate_mapping_file(self.total_calibrations_done)

                    self._update_status("Calibration Complete", "success")
                    return

                idx = self.calibration_sequence[self.current_calibration_index]
                self.is_in_glow_phase = True
                self.is_in_gap_phase = False
                self.calibration_start_time = now
                self._activate_stimulus(idx)
                self.calibration_handler.start_circle_focus(idx + 1)

    # -------------------------------------------------------------
    # Resize + Theme
    # -------------------------------------------------------------
    def resize(self, w, h):
        self.width = w
        self.height = h
        self.center_x = w // 2
        self.center_y = h // 2

        self.center_radius = self._calculate_center_radius()
        self.center_circle.resize(self.center_x, self.center_y, self.center_radius)

        min_dim = min(w, h - CONTROL_PANEL_HEIGHT)
        distance = int(min_dim * STIMULUS_DISTANCE_RATIO)

        # *** YOUR ORIGINAL UI CODE RESTORED (correct sin/cos) ***
        for i, angle in enumerate(STIMULUS_ANGLES):
            rad = math.radians(angle)
            x = self.center_x + distance * math.cos(rad)
            y = self.center_y + distance * math.sin(rad)
            self.stimulus_circles[i].reposition(x, y)

        self.timer.reposition(h)

    def update_theme(self):
        try:
            self.canvas.config(bg=get_color('bg'))
        except:
            pass

        self.center_circle.update_theme()
        for c in self.stimulus_circles:
            c.update_theme()
        self.timer.update_theme()

    # -------------------------------------------------------------
    # Status + Cleanup
    # -------------------------------------------------------------
    def _update_status(self, msg, level="info"):
        if self.status_callback:
            self.status_callback(msg, level)

    def cleanup(self):
        try:
            self.tobii.stop_tracking()
        except:
            pass
        print("Controller cleaned")
