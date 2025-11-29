# ===============================================
# FILE: eeg_data_handler.py
# Handles EEG data collection and JSONL storage (32 channels)
# ===============================================

import os
import json
import time
import logging
import uuid
from typing import List, Dict, Optional
from collections import deque
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EEGDataHandler:
    """
    Manages EEG data collection and storage in JSONL format.
    Thread-safe implementation for concurrent data acquisition.
    Supports configurable channel count (default: 32 channels).
    """
    
    def __init__(self, username: str, sampling_rate: int = 256, channel_count: int = 32):
        """
        Initialize EEG data handler.
        
        Args:
            username: User identifier for folder creation
            sampling_rate: EEG sampling rate in Hz
            channel_count: Number of EEG channels
        """
        self.username = username
        self.sampling_rate = sampling_rate
        self.channel_count = channel_count
        self.session_id = str(uuid.uuid4())[:8]
        
        # Create base directory structure
        self.base_dir = os.path.join("eeg_calibration", username)
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Current collection state
        self.current_calibration_index = 1
        self.current_circle = None
        self.current_phase = None  # "starting_rest", "focus", "ending_rest"
        
        # Data buffers (thread-safe)
        self._lock = threading.Lock()
        self.starting_rest_data: List[Dict] = []
        self.focus_data: List[Dict] = []
        self.ending_rest_data: List[Dict] = []
        
        # Metadata
        self.gap_time = 2.0  # Will be set from UI
        self.focus_time = 4.0  # Will be set from UI
        
        logger.info(f"✓ EEG Data Handler initialized for user: {username}")
        logger.info(f"  Session ID: {self.session_id}")
        logger.info(f"  Channels: {channel_count}")
        logger.info(f"  Sampling Rate: {sampling_rate} Hz")
        logger.info(f"  Storage path: {self.base_dir}")
    
    def set_timing_parameters(self, gap_time: float, focus_time: float) -> None:
        """
        Update timing parameters from UI.
        
        Args:
            gap_time: Rest period duration in seconds
            focus_time: Focus period duration in seconds
        """
        self.gap_time = gap_time
        self.focus_time = focus_time
        logger.info(f"Timing updated: gap={gap_time}s, focus={focus_time}s")
    
    def start_calibration_index(self, calibration_index: int) -> None:
        """
        Start a new calibration iteration.
        
        Args:
            calibration_index: Calibration number (1, 2, 3, ...)
        """
        self.current_calibration_index = calibration_index
        logger.info(f"Started calibration index: {calibration_index}")
    
    def start_circle_collection(self, circle_number: int) -> None:
        """
        Start collecting data for a specific circle activation.
        
        Args:
            circle_number: Circle ID (1-8)
        """
        with self._lock:
            self.current_circle = circle_number
            self.starting_rest_data = []
            self.focus_data = []
            self.ending_rest_data = []
            self.current_phase = None
        
        logger.debug(f"Started collection for circle {circle_number}")
    
    def set_phase(self, phase: str) -> None:
        """
        Set current collection phase.
        
        Args:
            phase: One of "starting_rest", "focus", "ending_rest"
        """
        with self._lock:
            self.current_phase = phase
        
        logger.debug(f"Phase changed to: {phase}")
    
    def add_sample(self, sample: Dict) -> None:
        """
        Add EEG sample to current phase buffer.
        Thread-safe method called from EEG streaming thread.
        
        Args:
            sample: EEG sample dict {"t": timestamp, "channels": [c1..cN]}
        """
        with self._lock:
            if self.current_phase is None or self.current_circle is None:
                return  # Not collecting
            
            # Validate channel count
            if len(sample.get("channels", [])) != self.channel_count:
                logger.warning(
                    f"Channel count mismatch: expected {self.channel_count}, "
                    f"got {len(sample.get('channels', []))}"
                )
                return
            
            # Format sample for storage
            formatted_sample = {
                "t": sample["t"],
                "ch": sample["channels"]  # All channels preserved
            }
            
            # Add to appropriate buffer
            if self.current_phase == "starting_rest":
                self.starting_rest_data.append(formatted_sample)
            elif self.current_phase == "focus":
                self.focus_data.append(formatted_sample)
            elif self.current_phase == "ending_rest":
                self.ending_rest_data.append(formatted_sample)
    
    def save_circle_data(self) -> bool:
        """
        Save collected data for current circle to JSONL file.
        Creates one JSON line per circle activation.
        
        Returns:
            True if saved successfully, False otherwise
        """
        with self._lock:
            if self.current_circle is None:
                logger.warning("No circle data to save")
                return False
            
            # Prepare data entry
            entry = {
                "username": self.username,
                "session_id": self.session_id,
                "calibration_index": self.current_calibration_index,
                "circle": self.current_circle,
                "channel_count": self.channel_count,
                "sampling_rate": self.sampling_rate,
                "starting_rest": self.starting_rest_data.copy(),
                "focus": self.focus_data.copy(),
                "ending_rest": self.ending_rest_data.copy(),
                "meta": {
                    "gap_time": self.gap_time,
                    "focus_time": self.focus_time,
                    "timestamp": time.time()
                }
            }
            
            # Determine filename
            filename = f"{self.current_calibration_index}.jsonl"
            filepath = os.path.join(self.base_dir, filename)
            
            # Clear buffers
            circle_saved = self.current_circle
            samples_rest_start = len(self.starting_rest_data)
            samples_focus = len(self.focus_data)
            samples_rest_end = len(self.ending_rest_data)
            
            self.starting_rest_data = []
            self.focus_data = []
            self.ending_rest_data = []
            self.current_circle = None
            self.current_phase = None
        
        # Write to file (outside lock to avoid blocking data collection)
        try:
            # Append mode - each circle adds one line
            with open(filepath, 'a', encoding='utf-8') as f:
                json.dump(entry, f, ensure_ascii=False)
                f.write('\n')
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk
            
            logger.info(f"✓ Saved circle {circle_saved} data to {filename}")
            logger.debug(f"  Starting rest samples: {samples_rest_start}")
            logger.debug(f"  Focus samples: {samples_focus}")
            logger.debug(f"  Ending rest samples: {samples_rest_end}")
            logger.debug(f"  Channels per sample: {self.channel_count}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to save circle data: {e}")
            return False
    
    def get_data_summary(self) -> Dict:
        """
        Get summary of collected data for current circle.
        
        Returns:
            Dictionary with sample counts per phase
        """
        with self._lock:
            return {
                "circle": self.current_circle,
                "phase": self.current_phase,
                "channel_count": self.channel_count,
                "starting_rest_samples": len(self.starting_rest_data),
                "focus_samples": len(self.focus_data),
                "ending_rest_samples": len(self.ending_rest_data)
            }
    
    def cleanup(self) -> None:
        """Cleanup handler resources."""
        with self._lock:
            self.current_circle = None
            self.current_phase = None
            self.starting_rest_data = []
            self.focus_data = []
            self.ending_rest_data = []
        
        logger.info("EEG Data Handler cleaned up")


def load_jsonl_file(filepath: str) -> List[Dict]:
    """
    Utility function to load JSONL file.
    
    Args:
        filepath: Path to JSONL file
        
    Returns:
        List of JSON objects (one per line)
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


def validate_jsonl_file(filepath: str) -> bool:
    """
    Validate JSONL file format and content.
    
    Args:
        filepath: Path to JSONL file
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "username", "session_id", "calibration_index", "circle",
        "channel_count", "sampling_rate", "starting_rest", "focus", 
        "ending_rest", "meta"
    ]
    
    try:
        data = load_jsonl_file(filepath)
        
        if not data:
            logger.warning(f"File {filepath} is empty")
            return False
        
        for idx, entry in enumerate(data):
            # Check required fields
            for field in required_fields:
                if field not in entry:
                    logger.error(f"Entry {idx}: missing field '{field}'")
                    return False
            
            # Validate data structure
            if not isinstance(entry["starting_rest"], list):
                logger.error(f"Entry {idx}: 'starting_rest' must be a list")
                return False
            
            if not isinstance(entry["focus"], list):
                logger.error(f"Entry {idx}: 'focus' must be a list")
                return False
            
            if not isinstance(entry["ending_rest"], list):
                logger.error(f"Entry {idx}: 'ending_rest' must be a list")
                return False
            
            # Validate channel count consistency
            channel_count = entry.get("channel_count", 0)
            for phase in ["starting_rest", "focus", "ending_rest"]:
                for sample in entry[phase]:
                    if len(sample.get("ch", [])) != channel_count:
                        logger.error(
                            f"Entry {idx}, {phase}: channel count mismatch "
                            f"(expected {channel_count}, got {len(sample.get('ch', []))})"
                        )
                        return False
        
        logger.info(f"✓ File {filepath} is valid ({len(data)} entries)")
        return True
        
    except Exception as e:
        logger.error(f"Validation error for {filepath}: {e}")
        return False


def print_file_statistics(filepath: str) -> None:
    """
    Print statistics about a JSONL calibration file.
    
    Args:
        filepath: Path to JSONL file
    """
    try:
        data = load_jsonl_file(filepath)
        
        if not data:
            print(f"File {filepath} is empty or invalid")
            return
        
        print(f"\n{'='*60}")
        print(f"Statistics for: {filepath}")
        print(f"{'='*60}")
        
        total_samples = 0
        channel_count = data[0].get("channel_count", "unknown")
        sampling_rate = data[0].get("sampling_rate", "unknown")
        
        print(f"Channel Count: {channel_count}")
        print(f"Sampling Rate: {sampling_rate} Hz")
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
        
        if isinstance(sampling_rate, (int, float)) and sampling_rate > 0:
            duration = total_samples / sampling_rate
            print(f"Total Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        
        print(f"{'='*60}\n")
        
    except Exception as e:
        logger.error(f"Error printing statistics: {e}")