# ===============================================
# FILE: eeg_device.py
# EEG Device Interface with g.Nautilus Support
# ===============================================

import time
import threading
import random
import logging
import sys
from typing import Callable, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EEGDevice:
    """
    Abstract interface for EEG device integration.
    Provides standardized methods for streaming 32-channel EEG data.
    """
    
    def connect(self) -> bool:
        """Establish connection to EEG device."""
        raise NotImplementedError
    
    def disconnect(self) -> None:
        """Disconnect from EEG device."""
        raise NotImplementedError
    
    def start_stream(self, callback: Callable) -> bool:
        """
        Start streaming EEG data.
        
        Args:
            callback: Function to call with each sample.
                      Signature: callback(sample_dict)
                      where sample_dict = {"t": timestamp, "channels": [c1..c32]}
        
        Returns:
            True if streaming started successfully, False otherwise.
        """
        raise NotImplementedError
    
    def stop_stream(self) -> None:
        """Stop streaming EEG data."""
        raise NotImplementedError
    
    def is_connected(self) -> bool:
        """Check if device is connected and ready."""
        raise NotImplementedError
    
    def get_sampling_rate(self) -> int:
        """Get the sampling rate in Hz."""
        raise NotImplementedError
    
    def get_channel_count(self) -> int:
        """Get the number of channels."""
        raise NotImplementedError


class GNautilusDevice(EEGDevice):
    """
    g.Nautilus 32-channel EEG device implementation.
    Uses g.tec's Python API for data acquisition.
    """
    
    def __init__(self, channel_count: int = 32, api_path: Optional[str] = None):
        """
        Initialize g.Nautilus device.
        
        Args:
            channel_count: Number of EEG channels (default: 32)
            api_path: Optional path to g.tec API (if not in system path)
        """
        self.channel_count = channel_count
        self._connected = False
        self.is_streaming = False
        self.device = None
        self.stream_thread: Optional[threading.Thread] = None
        self.callback: Optional[Callable] = None
        self._stop_event = threading.Event()
        self.sampling_rate = 250  # Will be updated from device
        
        # Add g.tec API path if provided
        if api_path:
            sys.path.insert(0, api_path)
        else:
            # Default g.tec installation path
            default_path = r"C:\Program Files\gtec\g.NEEDaccess\python"
            if default_path not in sys.path:
                sys.path.insert(0, default_path)
        
        # Try to import g.Nautilus API
        try:
            import gnautilus as gn
            self.gn = gn
            logger.info("✓ g.Nautilus API imported successfully")
        except ImportError as e:
            logger.error(f"✗ Failed to import g.Nautilus API: {e}")
            logger.error("Please install g.NEEDaccess software from g.tec")
            raise
        
        logger.info(f"g.Nautilus device initialized ({channel_count} channels)")
    
    def connect(self) -> bool:
        """Establish connection to g.Nautilus device."""
        try:
            logger.info("Searching for g.Nautilus devices...")
            
            # Get available devices
            devices = self.gn.GetAvailableDevices()
            
            if not devices:
                logger.error("✗ No g.Nautilus devices found")
                logger.error("Please check:")
                logger.error("  1. Device is powered on")
                logger.error("  2. Bluetooth is connected")
                logger.error("  3. g.NEEDaccess shows device as connected")
                return False
            
            # Use first available device
            self.device = devices[0]
            
            # Get device information
            device_name = self.device.Name
            serial = self.device.SerialNumber
            channels = self.device.NumberOfChannels
            
            logger.info(f"✓ Found device: {device_name}")
            logger.info(f"  Serial Number: {serial}")
            logger.info(f"  Channels: {channels}")
            
            # Verify channel count
            if channels != self.channel_count:
                logger.warning(
                    f"Channel count mismatch: expected {self.channel_count}, "
                    f"device has {channels}"
                )
                self.channel_count = channels
            
            # Get sampling rate
            self.sampling_rate = int(self.device.SamplingRate)
            logger.info(f"  Sampling Rate: {self.sampling_rate} Hz")
            
            # Configure device
            self._configure_device()
            
            self._connected = True
            logger.info("✓ g.Nautilus connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to connect to g.Nautilus: {e}")
            return False
    
    def _configure_device(self):
        """Configure device settings."""
        try:
            # Set device configuration
            # Example configurations (adjust as needed):
            
            # Enable all channels
            channel_config = [True] * self.channel_count
            self.device.SetConfiguration(channel_config)
            
            # Set notch filter (50 Hz or 60 Hz depending on your location)
            # self.device.SetNotchFilter(50)  # Europe
            # self.device.SetNotchFilter(60)  # USA
            
            logger.info("✓ Device configured")
            
        except Exception as e:
            logger.warning(f"Configuration warning: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from g.Nautilus device."""
        if self.is_streaming:
            self.stop_stream()
        
        try:
            if self.device:
                # Clean up device resources
                self.device = None
            
            self._connected = False
            logger.info("✓ g.Nautilus disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
    
    def is_connected(self) -> bool:
        """Check if device is connected."""
        return self._connected
    
    def get_sampling_rate(self) -> int:
        """Get sampling rate."""
        return self.sampling_rate
    
    def get_channel_count(self) -> int:
        """Get channel count."""
        return self.channel_count
    
    def start_stream(self, callback: Callable) -> bool:
        """Start streaming EEG data from g.Nautilus."""
        if not self._connected or not self.device:
            logger.error("✗ Cannot start stream: Device not connected")
            return False
        
        if self.is_streaming:
            logger.warning("Stream already running")
            return False
        
        try:
            self.callback = callback
            self.is_streaming = True
            self._stop_event.clear()
            
            # Start acquisition on device
            self.device.StartAcquisition()
            logger.info("✓ Started data acquisition on device")
            
            # Start streaming thread
            self.stream_thread = threading.Thread(
                target=self._stream_worker,
                daemon=True,
                name="g.Nautilus-Stream-Thread"
            )
            self.stream_thread.start()
            
            logger.info("✓ g.Nautilus streaming started")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to start streaming: {e}")
            self.is_streaming = False
            return False
    
    def stop_stream(self) -> None:
        """Stop streaming EEG data."""
        if not self.is_streaming:
            return
        
        self.is_streaming = False
        self._stop_event.set()
        
        # Wait for thread to finish
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2.0)
        
        # Stop acquisition on device
        try:
            if self.device:
                self.device.StopAcquisition()
                logger.info("✓ Stopped data acquisition on device")
        except Exception as e:
            logger.warning(f"Error stopping acquisition: {e}")
        
        logger.info("✓ g.Nautilus streaming stopped")
    
    def _stream_worker(self) -> None:
        """
        Background thread that reads data from g.Nautilus.
        Continuously polls device for new samples.
        """
        sample_count = 0
        error_count = 0
        max_errors = 10
        
        logger.info("Stream worker started")
        
        while self.is_streaming and not self._stop_event.is_set():
            try:
                # Get data from device (this blocks until data is available)
                data = self.device.GetData()
                
                if not data:
                    # No data available, short sleep
                    time.sleep(0.001)
                    continue
                
                # Process each sample in the data packet
                for scan in data:
                    if not self.is_streaming:
                        break
                    
                    # Extract channel data
                    # g.Nautilus returns data in Scans format
                    channels = list(scan.Channels[:self.channel_count])
                    
                    # Create sample dictionary
                    sample = {
                        "t": time.time(),  # Use current timestamp
                        "channels": channels
                    }
                    
                    # Send to callback
                    if self.callback:
                        try:
                            self.callback(sample)
                            sample_count += 1
                        except Exception as e:
                            logger.error(f"Error in callback: {e}")
                            error_count += 1
                            if error_count >= max_errors:
                                logger.error("Too many callback errors, stopping stream")
                                self.is_streaming = False
                                break
                
                # Reset error count on successful batch
                error_count = 0
                
            except Exception as e:
                logger.error(f"Error reading data: {e}")
                error_count += 1
                if error_count >= max_errors:
                    logger.error("Too many read errors, stopping stream")
                    self.is_streaming = False
                    break
                time.sleep(0.01)
        
        logger.info(f"Stream worker stopped after {sample_count} samples")


class MockEEGDevice(EEGDevice):
    """
    Mock EEG device for development and testing.
    Generates synthetic 32-channel EEG data.
    """
    
    def __init__(self, sampling_rate: int = 256, channel_count: int = 32):
        """Initialize mock EEG device."""
        self.sampling_rate = sampling_rate
        self.channel_count = channel_count
        self.is_streaming = False
        self.stream_thread: Optional[threading.Thread] = None
        self.callback: Optional[Callable] = None
        self._stop_event = threading.Event()
        self._connected = False
        
        logger.info(f"Mock EEG Device initialized ({channel_count} ch @ {sampling_rate} Hz)")
    
    def connect(self) -> bool:
        """Simulate connection."""
        logger.info("Connecting to Mock EEG device...")
        time.sleep(0.5)
        self._connected = True
        logger.info("✓ Mock EEG device connected")
        return True
    
    def disconnect(self) -> None:
        """Disconnect mock device."""
        if self.is_streaming:
            self.stop_stream()
        self._connected = False
        logger.info("✓ Mock EEG device disconnected")
    
    def is_connected(self) -> bool:
        """Check connection."""
        return self._connected
    
    def get_sampling_rate(self) -> int:
        """Get sampling rate."""
        return self.sampling_rate
    
    def get_channel_count(self) -> int:
        """Get channel count."""
        return self.channel_count
    
    def start_stream(self, callback: Callable) -> bool:
        """Start mock streaming."""
        if not self._connected:
            logger.error("✗ Device not connected")
            return False
        
        if self.is_streaming:
            return False
        
        self.callback = callback
        self.is_streaming = True
        self._stop_event.clear()
        
        self.stream_thread = threading.Thread(
            target=self._stream_worker,
            daemon=True,
            name="Mock-EEG-Stream"
        )
        self.stream_thread.start()
        
        logger.info("✓ Mock streaming started")
        return True
    
    def stop_stream(self) -> None:
        """Stop mock streaming."""
        if not self.is_streaming:
            return
        
        self.is_streaming = False
        self._stop_event.set()
        
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2.0)
        
        logger.info("✓ Mock streaming stopped")
    
    def _stream_worker(self) -> None:
        """Generate mock EEG data."""
        import math
        
        sample_interval = 1.0 / self.sampling_rate
        baseline_amps = [random.uniform(10, 50) for _ in range(self.channel_count)]
        frequencies = [random.uniform(8, 12) for _ in range(self.channel_count)]
        
        sample_count = 0
        
        while self.is_streaming and not self._stop_event.is_set():
            start_time = time.time()
            
            # Generate realistic EEG signals
            channels = []
            current_time = time.time()
            
            for i in range(self.channel_count):
                # Alpha wave + noise
                alpha = baseline_amps[i] * random.uniform(0.8, 1.2) * \
                       (0.5 + 0.5 * math.sin(2 * math.pi * frequencies[i] * current_time))
                noise = random.gauss(0, 5)
                signal = alpha + noise
                channels.append(round(signal, 2))
            
            sample = {
                "t": current_time,
                "channels": channels
            }
            
            if self.callback:
                try:
                    self.callback(sample)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
            
            sample_count += 1
            
            # Maintain timing
            elapsed = time.time() - start_time
            sleep_time = max(0, sample_interval - elapsed)
            if sleep_time > 0:
                self._stop_event.wait(sleep_time)
        
        logger.info(f"Mock worker stopped after {sample_count} samples")