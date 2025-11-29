# ===============================================
# FILE: calibration_data_handler.py
# Handles storing, grouping, and mapping gaze data (Tobii/Mouse)
# Now stores data similar to EEG format with phase tracking
# ===============================================

import os
import json
import time
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CalibrationDataHandler:
    """
    Handles Tobii and Mouse calibration data collection.
    Stores data in JSONL format with phase tracking (starting_rest, focus, ending_rest).
    """

    def __init__(self, username):
        self.username = username
        self.session_id = str(uuid.uuid4())[:8]

        # Create separate folders for eye tracking data
        self.base_dir = os.path.join("eye_calibration", username)
        os.makedirs(self.base_dir, exist_ok=True)

        self.current_calibration_index = 1
        self.current_circle = None
        self.current_phase = None  # "starting_rest", "focus", "ending_rest"
        
        # Data buffers per phase
        self.starting_rest_data = []
        self.focus_data = []
        self.ending_rest_data = []

        logger.info(f"✓ Eye Tracking Data Handler initialized for user: {username}")
        logger.info(f"  Session ID: {self.session_id}")
        logger.info(f"  Storage path: {self.base_dir}")

    # ---------------------------------------------------------
    # SESSION MANAGEMENT
    # ---------------------------------------------------------
    def start_session(self):
        """Start a new calibration session."""
        logger.info(f"Started session {self.current_calibration_index}")
        return True

    def end_session(self):
        """End current session."""
        logger.info(f"Ended session {self.current_calibration_index}")

    def increment_session_number(self):
        """Move to next calibration index."""
        self.current_calibration_index += 1
        logger.info(f"Incremented to calibration index {self.current_calibration_index}")

    # ---------------------------------------------------------
    # CIRCLE AND PHASE MANAGEMENT
    # ---------------------------------------------------------
    def start_circle_collection(self, circle_id, phase):
        """
        Start collecting data for a specific circle and phase.
        
        Args:
            circle_id: Circle number (1-8)
            phase: "starting_rest", "focus", or "ending_rest"
        """
        self.current_circle = circle_id
        self.current_phase = phase
        
        # Clear buffers if starting a new circle
        if phase == "starting_rest":
            self.starting_rest_data = []
            self.focus_data = []
            self.ending_rest_data = []
        
        logger.debug(f"Started collection: circle {circle_id}, phase {phase}")

    def start_circle_focus(self, circle_id, phase):
        """Alias for start_circle_collection."""
        self.start_circle_collection(circle_id, phase)

    def end_circle_focus(self):
        """End focus on current circle and save data."""
        if self.current_circle is not None:
            self.save_circle_data()
        
        self.current_circle = None
        self.current_phase = None

    # ---------------------------------------------------------
    # MAIN GAZE LOGGING FUNCTION
    # ---------------------------------------------------------
    def log_gaze_data(self, gaze_data, circle_id):
        """
        Log gaze data to appropriate phase buffer.
        
        Args:
            gaze_data: dict with keys:
                - timestamp: float
                - avg_x: float or None/nan
                - avg_y: float or None/nan
                - left: [xL, yL] or None
                - right: [xR, yR] or None
            circle_id: int (1-8)
        """
        if self.current_phase is None or self.current_circle != circle_id:
            return

        # Format sample for storage
        formatted_sample = {
            "t": gaze_data.get("timestamp", time.time()),
            "x": gaze_data.get("avg_x"),
            "y": gaze_data.get("avg_y"),
            "left": gaze_data.get("left"),
            "right": gaze_data.get("right")
        }

        # Add to appropriate buffer
        if self.current_phase == "starting_rest":
            self.starting_rest_data.append(formatted_sample)
        elif self.current_phase == "focus":
            self.focus_data.append(formatted_sample)
        elif self.current_phase == "ending_rest":
            self.ending_rest_data.append(formatted_sample)

    # ---------------------------------------------------------
    # SAVE DATA TO JSONL
    # ---------------------------------------------------------
    def save_circle_data(self):
        """
        Save collected data for current circle to JSONL file.
        One JSON line per circle activation.
        
        Returns:
            True if saved successfully, False otherwise
        """
        if self.current_circle is None:
            logger.warning("No circle data to save")
            return False

        # Prepare data entry
        entry = {
            "username": self.username,
            "session_id": self.session_id,
            "calibration_index": self.current_calibration_index,
            "circle": self.current_circle,
            "starting_rest": self.starting_rest_data.copy(),
            "focus": self.focus_data.copy(),
            "ending_rest": self.ending_rest_data.copy(),
            "meta": {
                "timestamp": time.time(),
                "data_type": "eye_tracking"
            }
        }

        # Determine filename
        filename = f"{self.current_calibration_index}.jsonl"
        filepath = os.path.join(self.base_dir, filename)

        # Store counts for logging
        circle_saved = self.current_circle
        samples_rest_start = len(self.starting_rest_data)
        samples_focus = len(self.focus_data)
        samples_rest_end = len(self.ending_rest_data)

        # Clear buffers
        self.starting_rest_data = []
        self.focus_data = []
        self.ending_rest_data = []

        # Write to file
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                json.dump(entry, f, ensure_ascii=False)
                f.write('\n')
                f.flush()
                os.fsync(f.fileno())

            logger.info(f"✓ Saved circle {circle_saved} data to {filename}")
            logger.debug(f"  Starting rest samples: {samples_rest_start}")
            logger.debug(f"  Focus samples: {samples_focus}")
            logger.debug(f"  Ending rest samples: {samples_rest_end}")

            return True

        except Exception as e:
            logger.error(f"✗ Failed to save circle data: {e}")
            return False

    # ---------------------------------------------------------
    # MAPPING FILE GENERATION (Legacy - for backward compatibility)
    # ---------------------------------------------------------
    def generate_mapping_file(self, calibration_number):
        """
        Generate averaged mapping file from focus phase data.
        This is a legacy function for backward compatibility.
        
        Args:
            calibration_number: int - calibration index
        """
        # Load all data from JSONL file
        filename = f"{calibration_number}.jsonl"
        filepath = os.path.join(self.base_dir, filename)

        if not os.path.exists(filepath):
            logger.warning(f"Cannot generate mapping: {filename} not found")
            return

        try:
            mapping = {}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = json.loads(line.strip())
                    circle = entry.get("circle")
                    focus_data = entry.get("focus", [])
                    
                    # Extract valid x, y coordinates from focus phase
                    xs = [s["x"] for s in focus_data if s.get("x") is not None]
                    ys = [s["y"] for s in focus_data if s.get("y") is not None]
                    
                    if xs and ys:
                        mapping[circle] = {
                            "avg_x": sum(xs) / len(xs),
                            "avg_y": sum(ys) / len(ys),
                            "samples": len(xs)
                        }

            # Save mapping file
            out = os.path.join(self.base_dir, f"mapping_{calibration_number}.json")
            with open(out, 'w') as f:
                json.dump(mapping, f, indent=4)

            logger.info(f"✓ Mapping Saved: {out}")

        except Exception as e:
            logger.error(f"✗ Failed to generate mapping: {e}")


def load_jsonl_file(filepath):
    """
    Load eye tracking JSONL file.
    
    Args:
        filepath: Path to JSONL file
        
    Returns:
        List of JSON objects (one per circle)
    """
    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing line {line_num}: {e}")
    except Exception as e:
        logger.error(f"Error loading file {filepath}: {e}")
    
    return data


def print_file_statistics(filepath):
    """
    Print statistics about eye tracking calibration file.
    
    Args:
        filepath: Path to JSONL file
    """
    try:
        data = load_jsonl_file(filepath)
        
        if not data:
            print(f"File {filepath} is empty or invalid")
            return
        
        print(f"\n{'='*60}")
        print(f"Eye Tracking Statistics: {filepath}")
        print(f"{'='*60}")
        
        total_samples = 0
        
        print(f"Total Circles: {len(data)}")
        print(f"\nPer-circle breakdown:")
        print(f"{'Circle':<8} {'Rest1':<10} {'Focus':<10} {'Rest2':<10} {'Total':<10}")
        print(f"{'-'*60}")
        
        for entry in data:
            circle = entry.get("circle", "?")
            rest1 = len(entry.get("starting_rest", []))
            focus = len(entry.get("focus", []))
            rest2 = len(entry.get("ending_rest", []))
            total = rest1 + focus + rest2
            
            print(f"{circle:<8} {rest1:<10} {focus:<10} {rest2:<10} {total:<10}")
            total_samples += total
        
        print(f"{'-'*60}")
        print(f"Total Samples: {total_samples}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        logger.error(f"Error printing statistics: {e}")