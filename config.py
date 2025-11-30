# -*- coding: utf-8 -*-
# ===============================================
# FILE: config.py
# Configuration file for BCI Interface
# ===============================================

# Window Configuration
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
MIN_WIDTH = 900
MIN_HEIGHT = 700

# ==================== Theme System ====================

# Black & White Theme
BLACK_WHITE_THEME = {
    'bg': "#000000",
    'circle_center': "#000000",
    'circle_border': "#FFFFFF",
    'dot': "#FFFFFF",
    'dot_glow': '#FFFFFF',
    'stimulus_normal': '#000000',  # Black fill
    'stimulus_border': '#FFFFFF',  # White border
    'stimulus_glow': "#FF0000",
    'control_bg': '#000000',
    'text_primary': '#FFFFFF',
    'text_secondary': '#CCCCCC',
    'dropdown_bg': '#000000',
    'dropdown_hover': '#1A1A1A',
    'timer_bg': '#000000',
    'timer_border': '#FFFFFF',
    'timer_text': '#FFFFFF',
    'rest_screen_bg': '#000000',
    'rest_screen_text': '#FFFFFF',
    'button_bg': '#FFFFFF',
    'button_fg': '#000000',
    'button_hover': '#CCCCCC'
}

# Current theme (will be set by application)
CURRENT_THEME = BLACK_WHITE_THEME

# Theme names
THEME_BLACK_WHITE = "Black & White"

# ==================== UI Colors (Dynamic) ====================
def get_color(key):
    """Get color from current theme."""
    return CURRENT_THEME.get(key, '#FFFFFF')

# ==================== Center Circle Configuration ====================
CENTER_CIRCLE_RADIUS_RATIO = 0.10
DOT_COUNT = 50
DOT_RADIUS = 3
DOT_GLOW_RADIUS = 5

# ==================== Stimulus Circle Configuration ====================
STIMULUS_CIRCLE_COUNT = 8
STIMULUS_CIRCLE_RADIUS = 60
STIMULUS_GLOW_WIDTH = 4
STIMULUS_NORMAL_WIDTH = 2
STIMULUS_DISTANCE_RATIO = 0.45

STIMULUS_HOVER_THRESHOLD = 40
STIMULUS_HOVER_RADIUS = 40
STIMULUS_SCALE_SPEED = 8.0

# ==================== Tobii Configuration ====================
TOBII_FOCUS_THRESHOLD = 80  # Pixels - radius to consider "focused on circle"
TOBII_FOCUS_DURATION = 1.5  # Seconds - how long user must focus before dots move

# ==================== Animation Configuration ====================
FPS = 60
FRAME_TIME = int(1000 / FPS)

# Dot physics parameters
DOT_SPRING_STRENGTH = 8.0
DOT_DAMPING = 0.85
DOT_MAX_SPEED = 300.0
DOT_MOVE_DURATION = 0.3
DOT_RETURN_DURATION = 0.5

# ==================== Phase Configuration ====================
PHASE_TESTING = "Testing Phase"
PHASE_CALIBRATION = "Calibration Phase"
PHASE_START = "Start Phase"
PHASES = [PHASE_TESTING, PHASE_CALIBRATION, PHASE_START]

# ==================== Input Modes ====================
INPUT_MODE_MOUSE = "Mouse Cursor"
INPUT_MODE_TOBII = "Tobii Eye Tracker"
INPUT_MODE_EEG = "EEG Headset"
INPUT_MODES = [INPUT_MODE_MOUSE, INPUT_MODE_TOBII, INPUT_MODE_EEG]

# ==================== Time Configuration ====================
# Mouse/Tobii Configuration
FOCUS_TIME_OPTIONS = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
DEFAULT_FOCUS_TIME = 3.0
GAP_TIME_OPTIONS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
DEFAULT_GAP_TIME = 2.0

# EEG Configuration
EEG_FOCUS_TIME_OPTIONS = [4.0, 8.0, 12.0, 16.0]  # Multiples of 4
EEG_DEFAULT_FOCUS_TIME = 4.0
EEG_GAP_TIME_OPTIONS = [2.0, 4.0, 6.0]  # Multiples of 2
EEG_DEFAULT_GAP_TIME = 2.0

# ==================== Calibration Configuration ====================
CALIBRATION_ROUNDS_OPTIONS = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
DEFAULT_CALIBRATION_ROUNDS = 5
DOT_MOVE_TRIGGER_RATIO = 0.83

# ==================== EEG Configuration ====================
EEG_SAMPLING_RATE = 256  # Hz
EEG_CHANNEL_COUNT = 32  # 32-channel EEG system

# ==================== EEG Action Instructions ====================
# Map each circle number (1-8) to a 3-word action instruction
EEG_ACTION_INSTRUCTIONS = {
    1: "THINK MOVE FORWARD",
    2: "THINK MOVE BACKWARD",
    3: "THINK TURN LEFT",
    4: "THINK TURN RIGHT",
    5: "THINK MOVE UP",
    6: "THINK MOVE DOWN",
    7: "THINK ACTION STOP",
    8: "THINK ACTION START"
}

# ==================== Control Panel Configuration ====================
CONTROL_PANEL_HEIGHT = 60
CONTROL_PADDING = 15
DROPDOWN_WIDTH = 150
DROPDOWN_HEIGHT = 30
LABEL_FONT = ("Segoe UI", 9)
DROPDOWN_FONT = ("Segoe UI", 9)
STATUS_FONT = ("Segoe UI", 10, "bold")
BUTTON_FONT = ("Segoe UI", 9, "bold")

# ==================== Timer Configuration ====================
TIMER_WIDTH = 120
TIMER_HEIGHT = 50
TIMER_PADDING = 15
TIMER_FONT = ("Consolas", 16, "bold")
TIMER_LABEL_FONT = ("Segoe UI", 8)

# ==================== Rest Screen Configuration ====================
REST_SCREEN_FONT = ("Segoe UI", 48, "bold")
REST_SCREEN_TEXT = "REST"
REST_SCREEN_INSTRUCTION_FONT = ("Segoe UI", 24, "bold")

# ==================== Stimulus Circle Positions ====================
STIMULUS_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]  # 8 positions (degrees)