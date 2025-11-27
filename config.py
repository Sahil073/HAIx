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

# Light Mode (Default)
LIGHT_THEME = {
    'bg': '#E8EAF0',
    'circle_center': '#B8C5A0',
    'circle_border': '#7A8F6E',
    'dot': '#E07A7A',
    'dot_glow': '#FFFFFF',
    'stimulus_normal': '#2D3142',
    'stimulus_glow': "#EC0A0A",
    'control_bg': '#F5F7FA',
    'text_primary': '#2D3142',
    'text_secondary': '#6B7280',
    'dropdown_bg': '#FFFFFF',
    'dropdown_hover': '#F0F4F8',
    'timer_bg': '#FFFFFF',
    'timer_text': '#2D3142'
}

# Dark Mode
DARK_THEME = {
    'bg': '#1A1A2E',
    'circle_center': '#2D3142',
    'circle_border': '#4F5B66',
    'dot': '#FF6B6B',
    'dot_glow': '#FFFFFF',
    'stimulus_normal': '#3E4554',
    'stimulus_glow': '#FFA500',
    'control_bg': '#0F1419',
    'text_primary': '#E2E8F0',
    'text_secondary': '#A0AEC0',
    'dropdown_bg': '#2D3748',
    'dropdown_hover': '#4A5568',
    'timer_bg': '#2D3142',
    'timer_text': '#E2E8F0'
}

# Colorblind Mode (Deuteranopia-friendly)
COLORBLIND_THEME = {
    'bg': '#F0F0F0',
    'circle_center': '#A0B0C0',
    'circle_border': '#607080',
    'dot': '#0066CC',  # Blue instead of red
    'dot_glow': '#FFFFFF',
    'stimulus_normal': '#2D3142',
    'stimulus_glow': '#FF8800',  # Orange instead of yellow
    'control_bg': '#E8E8E8',
    'text_primary': '#1A1A1A',
    'text_secondary': '#4A4A4A',
    'dropdown_bg': '#FFFFFF',
    'dropdown_hover': '#E0E0E0',
    'timer_bg': '#FFFFFF',
    'timer_text': '#1A1A1A'
}

# Current theme (will be set by application)
CURRENT_THEME = LIGHT_THEME

# Theme names
THEME_LIGHT = "Light Mode"
THEME_DARK = "Dark Mode"
THEME_COLORBLIND = "Colorblind Mode"

# ==================== UI Colors (Dynamic) ====================
def get_color(key):
    """Get color from current theme."""
    return CURRENT_THEME.get(key, '#FFFFFF')

# ==================== Center Circle Configuration ====================
CENTER_CIRCLE_RADIUS_RATIO = 0.15  # REDUCED from 0.25 to 0.15 (smaller circle)
DOT_COUNT = 50  # Number of dots in center circle
DOT_RADIUS = 3
DOT_GLOW_RADIUS = 5

# ==================== Stimulus Circle Configuration ====================
STIMULUS_CIRCLE_COUNT = 8
STIMULUS_CIRCLE_RADIUS = 30  # Radius of each stimulus circle
STIMULUS_GLOW_WIDTH = 4  # Border width when glowing
STIMULUS_NORMAL_WIDTH = 2  # Normal border width
STIMULUS_DISTANCE_RATIO = 0.45  # Distance from center as ratio

# --- Hover / animation defaults used by ui_components.py ---
STIMULUS_HOVER_THRESHOLD = 40     # px - when cursor is considered "hovering" (safe default)
STIMULUS_HOVER_RADIUS = 40        # px - radius to expand to when hovered
STIMULUS_SCALE_SPEED = 8.0        # interpolation speed for smooth scaling

# ==================== Animation Configuration ====================
FPS = 60
FRAME_TIME = int(1000 / FPS)  # milliseconds

# Dot physics parameters (from original working code)
DOT_SPRING_STRENGTH = 8.0  # Spring force toward target
DOT_DAMPING = 0.85  # Velocity damping
DOT_MAX_SPEED = 300.0  # Maximum speed in pixels/second
DOT_MOVE_DURATION = 0.3  # seconds - time for dots to reach target
DOT_RETURN_DURATION = 0.5  # seconds - time for dots to return

# ==================== Phase Configuration ====================
PHASE_TESTING = "Testing Phase"
PHASE_CALIBRATION = "Calibration Phase"
PHASE_START = "Start Phase"
PHASES = [PHASE_TESTING, PHASE_CALIBRATION, PHASE_START]

# ==================== Input Modes ====================
INPUT_MODE_MOUSE = "Mouse Cursor"
INPUT_MODE_TOBII = "Tobii Eye Tracker"
INPUT_MODES = [INPUT_MODE_MOUSE, INPUT_MODE_TOBII]

# ==================== Time Configuration ====================
FOCUS_TIME_OPTIONS = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]  # seconds
DEFAULT_FOCUS_TIME = 3.0
GAP_TIME_OPTIONS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]  # seconds
DEFAULT_GAP_TIME = 2.0

# ==================== Calibration Configuration ====================
CALIBRATION_ROUNDS_OPTIONS = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
DEFAULT_CALIBRATION_ROUNDS = 5
DOT_MOVE_TRIGGER_RATIO = 0.83  # Dots start moving at 83% of focus time

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

# ==================== Stimulus Circle Positions ====================
STIMULUS_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]  # 8 positions (degrees)
