# ===============================================
# FILE: calibration_data_handler.py
# Handles storing, grouping, and mapping gaze data
# ===============================================

import os
import json
import time


class CalibrationDataHandler:

    def __init__(self, username):
        self.username = username

        self.base_dir = os.path.join("calibration_logs", username)
        os.makedirs(self.base_dir, exist_ok=True)

        self.current_session_number = 1
        self.current_session_data = []
        self.active_circle = None

    # ---------------------------------------------------------
    # SESSION MANAGEMENT
    # ---------------------------------------------------------
    def start_session(self):
        self.current_session_data = []
        return True

    def end_session(self):
        """Save grouped gaze data into JSON."""
        grouped = {}

        for entry in self.current_session_data:
            cid = entry["circle"]
            grouped.setdefault(cid, []).append(entry)

        filename = f"session_{self.current_session_number}.json"
        path = os.path.join(self.base_dir, filename)

        with open(path, "w") as f:
            json.dump(grouped, f, indent=4)

        print(f"✓ Saved: {path}")

    def increment_session_number(self):
        self.current_session_number += 1

    # ---------------------------------------------------------
    # CIRCLE FOCUS CONTROL
    # ---------------------------------------------------------
    def start_circle_focus(self, circle_id):
        self.active_circle = circle_id

    def end_circle_focus(self):
        self.active_circle = None

    # ---------------------------------------------------------
    # MAIN GAZE LOGGING FUNCTION
    # ---------------------------------------------------------
    def log_gaze_data(self, gaze_data, circle_id):
        """
        gaze_data format from tobii_handler:
        {
            "timestamp": float,
            "left": [xL, yL],
            "right": [xR, yR],
            "avg_x": float or nan,
            "avg_y": float or nan
        }
        """

        entry = {
            "circle": circle_id,
            "timestamp": gaze_data.get("timestamp", time.time()),
            "x": gaze_data.get("avg_x"),
            "y": gaze_data.get("avg_y")
        }

        self.current_session_data.append(entry)

    # ---------------------------------------------------------
    # MAPPING FILE GENERATION
    # ---------------------------------------------------------
    def generate_mapping_file(self, calibration_number):
        grouped = {}
        for e in self.current_session_data:
            grouped.setdefault(e["circle"], []).append(e)

        mapping = {}

        for cid, samples in grouped.items():
            xs = [s["x"] for s in samples if s["x"] is not None]
            ys = [s["y"] for s in samples if s["y"] is not None]

            if xs and ys:
                mapping[cid] = {
                    "avg_x": sum(xs) / len(xs),
                    "avg_y": sum(ys) / len(ys),
                    "samples": len(xs)
                }

        out = os.path.join(self.base_dir, f"mapping_{calibration_number}.json")

        with open(out, "w") as f:
            json.dump(mapping, f, indent=4)

        print(f"✓ Mapping Saved: {out}")
