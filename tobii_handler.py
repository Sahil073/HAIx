# ===============================================
# FILE: tobii_handler.py
# Tobii Eye Tracker Integration
# ===============================================

import time


class TobiiHandler:
    """
    Handles Tobii eye tracker connection and gaze data.
    Provides fallback to mouse if Tobii is unavailable.
    """
    
    def __init__(self):
        self.tobii_available = False
        self.tobii_research = None
        self.eyetracker = None
        self.running = False
        
        # Current gaze position (normalized 0-1)
        self.gaze_x = 0.5
        self.gaze_y = 0.5
        
        # Callback for gaze updates
        self.gaze_callback = None
        
        # Try to load Tobii SDK
        self._load_tobii_sdk()
    
    def _load_tobii_sdk(self):
        """Attempt to load Tobii Research SDK."""
        try:
            import tobii_research as tr
            self.tobii_research = tr
            print("✓ Tobii Research SDK loaded successfully")
            self._connect_eyetracker()
        except ImportError:
            print("⚠ Tobii Research SDK not found")
            print("  Install with: pip install tobii-research")
            self.tobii_available = False
    
    def _connect_eyetracker(self):
        """Connect to first available Tobii eye tracker."""
        try:
            eyetrackers = self.tobii_research.find_all_eyetrackers()
            
            if not eyetrackers:
                print("⚠ No Tobii eye tracker devices found")
                self.tobii_available = False
                return False
            
            self.eyetracker = eyetrackers[0]
            print(f"✓ Connected to Tobii: {self.eyetracker.model}")
            print(f"  Serial: {self.eyetracker.serial_number}")
            
            self.tobii_available = True
            return True
            
        except Exception as e:
            print(f"✗ Error connecting to Tobii: {e}")
            self.tobii_available = False
            return False
    
    def is_available(self):
        """Check if Tobii is available."""
        return self.tobii_available
    
    def start_tracking(self, callback=None):
        """
        Start gaze tracking.
        callback: function(norm_x, norm_y, gaze_data) called on each gaze update.
        """
        if not self.tobii_available:
            print("✗ Cannot start tracking: Tobii unavailable")
            return False
        
        self.gaze_callback = callback
        
        try:
            self.eyetracker.subscribe_to(
                self.tobii_research.EYETRACKER_GAZE_DATA,
                self._on_gaze_data,
                as_dictionary=True
            )
            self.running = True
            print("✓ Gaze tracking started")
            return True
            
        except Exception as e:
            print(f"✗ Error starting gaze tracking: {e}")
            return False
    
    def stop_tracking(self):
        """Stop gaze tracking."""
        if self.eyetracker and self.running:
            try:
                self.eyetracker.unsubscribe_from(
                    self.tobii_research.EYETRACKER_GAZE_DATA
                )
                print("✓ Gaze tracking stopped")
            except Exception as e:
                print(f"⚠ Error stopping tracking: {e}")
        
        self.running = False
    
    def _on_gaze_data(self, gaze_data):
        """Internal callback for gaze data from Tobii SDK."""
        try:
            # Extract left and right gaze points
            left = gaze_data.get("left_gaze_point_on_display_area")
            right = gaze_data.get("right_gaze_point_on_display_area")
            
            # Prepare data for logging (including NaN values)
            log_data = {
                "timestamp": time.time(),
                "left": list(left) if left else [float('nan'), float('nan')],
                "right": list(right) if right else [float('nan'), float('nan')],
                "avg_x": None,
                "avg_y": None
            }
            
            # Only calculate average if both eyes have valid data
            if left and right:
                # Check if values are valid (not NaN)
                try:
                    if all(isinstance(v, (int, float)) and not (isinstance(v, float) and str(v) == 'nan') for v in left + right):
                        # Average both eyes
                        gaze_x = (left[0] + right[0]) / 2.0
                        gaze_y = (left[1] + right[1]) / 2.0
                        
                        # Update internal state
                        self.gaze_x = gaze_x
                        self.gaze_y = gaze_y
                        
                        log_data["avg_x"] = gaze_x
                        log_data["avg_y"] = gaze_y
                        
                        # Call user callback with valid data
                        if self.gaze_callback:
                            self.gaze_callback(gaze_x, gaze_y, log_data)
                    else:
                        # Invalid data, set to NaN
                        log_data["avg_x"] = float('nan')
                        log_data["avg_y"] = float('nan')
                        if self.gaze_callback:
                            self.gaze_callback(self.gaze_x, self.gaze_y, log_data)
                except:
                    log_data["avg_x"] = float('nan')
                    log_data["avg_y"] = float('nan')
                    if self.gaze_callback:
                        self.gaze_callback(self.gaze_x, self.gaze_y, log_data)
            else:
                # No valid data from eyes
                log_data["avg_x"] = float('nan')
                log_data["avg_y"] = float('nan')
                if self.gaze_callback:
                    self.gaze_callback(self.gaze_x, self.gaze_y, log_data)
                    
        except Exception as e:
            print(f"⚠ Error processing gaze data: {e}")
    
    def get_current_gaze(self):
        """Get latest gaze position (normalized 0-1)."""
        return self.gaze_x, self.gaze_y