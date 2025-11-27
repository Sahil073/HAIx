# ===============================================
# FILE: ui_components.py
# UI Components for BCI Interface
# ===============================================

import math
import random
from config import *


class Dot:
    """
    Represents a single dot in the center circle.
    Uses smooth spring physics for natural movement.
    """
    
    def __init__(self, canvas, home_x, home_y, color):
        self.canvas = canvas
        self.home_x = home_x
        self.home_y = home_y
        
        # Current position and velocity
        self.x = home_x
        self.y = home_y
        self.vx = 0.0
        self.vy = 0.0
        
        # Target position
        self.target_x = home_x
        self.target_y = home_y
        
        # Create visual elements
        self.glow = canvas.create_oval(
            self.x - DOT_GLOW_RADIUS, self.y - DOT_GLOW_RADIUS,
            self.x + DOT_GLOW_RADIUS, self.y + DOT_GLOW_RADIUS,
            fill="", outline=get_color('dot_glow'), width=1, state="hidden"
        )
        
        self.dot = canvas.create_oval(
            self.x - DOT_RADIUS, self.y - DOT_RADIUS,
            self.x + DOT_RADIUS, self.y + DOT_RADIUS,
            fill=color, outline=""
        )
    
    def set_home(self, x, y):
        """Update home position (for window resize)."""
        self.home_x = x
        self.home_y = y
    
    def set_target(self, x, y):
        """Set target position for movement."""
        self.target_x = x
        self.target_y = y
    
    def update(self, dt):
        """
        Update position using spring physics.
        Uses SLOWER movement parameters from config.
        """
        # Spring force toward target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)
        
        if dist > 0.5:
            # Apply spring acceleration (SLOWER with reduced spring strength)
            ax = dx * DOT_SPRING_STRENGTH * dt
            ay = dy * DOT_SPRING_STRENGTH * dt
            
            self.vx += ax
            self.vy += ay
        else:
            # Very close to target, reduce velocity
            self.vx *= 0.5
            self.vy *= 0.5
        
        # Apply damping (INCREASED for smoother movement)
        self.vx *= DOT_DAMPING
        self.vy *= DOT_DAMPING
        
        # Limit maximum speed (REDUCED for slower movement)
        speed = math.hypot(self.vx, self.vy)
        max_speed = DOT_MAX_SPEED * dt
        if speed > max_speed:
            scale = max_speed / speed
            self.vx *= scale
            self.vy *= scale
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Update visual
        self._update_visual()
    
    def _update_visual(self):
        """Update canvas position."""
        self.canvas.coords(
            self.dot,
            self.x - DOT_RADIUS, self.y - DOT_RADIUS,
            self.x + DOT_RADIUS, self.y + DOT_RADIUS
        )
        self.canvas.coords(
            self.glow,
            self.x - DOT_GLOW_RADIUS, self.y - DOT_GLOW_RADIUS,
            self.x + DOT_GLOW_RADIUS, self.y + DOT_GLOW_RADIUS
        )
    
    def update_color(self, color):
        """Update dot color (for theme changes)."""
        self.canvas.itemconfig(self.dot, fill=color)


class CenterCircle:
    """
    Central circle containing animated dots.
    Dots move toward stimulus circles during calibration.
    NOW SMALLER than before.
    """
    
    def __init__(self, canvas, center_x, center_y, radius):
        self.canvas = canvas
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.dots = []
        
        # Create circle background
        self.circle = canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill=get_color('circle_center'),
            outline=get_color('circle_border'),
            width=2
        )
        
        # Create dots
        self._create_dots()
    
    def _create_dots(self):
        """Create dots in fixed grid pattern that appears random."""
        color = get_color('dot')
        
        # Create fixed pattern positions (appears random but reproducible)
        positions = []
        rows = 7
        cols = 7
        spacing = self.radius * 1.6 / rows
        
        for row in range(rows):
            for col in range(cols):
                # Grid position
                x_offset = (col - cols/2) * spacing
                y_offset = (row - rows/2) * spacing
                
                # Add slight random offset for natural look
                x_offset += random.uniform(-spacing*0.2, spacing*0.2)
                y_offset += random.uniform(-spacing*0.2, spacing*0.2)
                
                x = self.center_x + x_offset
                y = self.center_y + y_offset
                
                # Only keep dots within circle boundary
                dx = x - self.center_x
                dy = y - self.center_y
                dist = math.hypot(dx, dy)
                
                if dist < self.radius * 0.85:
                    positions.append((x, y))
        
        # Take exactly DOT_COUNT positions
        random.shuffle(positions)
        positions = positions[:DOT_COUNT]
        
        # Create dots at these fixed positions
        for x, y in positions:
            dot = Dot(self.canvas, x, y, color)
            self.dots.append(dot)
    
    def resize(self, center_x, center_y, radius):
        """Handle window resize - maintain relative positions."""
        # Calculate scale factors
        scale = radius / self.radius if self.radius > 0 else 1
        dx = center_x - self.center_x
        dy = center_y - self.center_y
        
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        
        # Update circle
        self.canvas.coords(
            self.circle,
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius
        )
        
        # Update dot home positions maintaining relative positions
        for dot in self.dots:
            # Calculate offset from old center
            offset_x = dot.home_x - (center_x - dx)
            offset_y = dot.home_y - (center_y - dy)
            
            # Apply scale and new center
            new_home_x = center_x + offset_x * scale
            new_home_y = center_y + offset_y * scale
            
            dot.set_home(new_home_x, new_home_y)
            
            # If dot is at home, update current position too
            if abs(dot.target_x - dot.home_x) < 1:
                dot.x = new_home_x
                dot.y = new_home_y
                dot.target_x = new_home_x
                dot.target_y = new_home_y
    
    def move_dots_toward(self, target_x, target_y, progress_ratio):
        """
        Move dots toward target position based on progress.
        Uses unified movement with SLOWER physics.
        """
        # Calculate direction from center to target
        dx = target_x - self.center_x
        dy = target_y - self.center_y
        dist = math.hypot(dx, dy)
        
        if dist > 10:
            # Normalize direction
            dx /= dist
            dy /= dist
            
            # Push distance based on progress (adjusted for smaller circle)
            push_dist = self.radius * 0.6 * progress_ratio
            
            # All dots move in same direction from their home positions
            for dot in self.dots:
                target_x_pos = dot.home_x + dx * push_dist
                target_y_pos = dot.home_y + dy * push_dist
                
                # Keep within circle boundary
                dx_center = target_x_pos - self.center_x
                dy_center = target_y_pos - self.center_y
                dist_from_center = math.hypot(dx_center, dy_center)
                
                if dist_from_center > self.radius * 0.95:
                    scale = (self.radius * 0.95) / dist_from_center
                    target_x_pos = self.center_x + dx_center * scale
                    target_y_pos = self.center_y + dy_center * scale
                
                dot.set_target(target_x_pos, target_y_pos)
        else:
            # Too close to center, return home
            self.return_dots_home()
    
    def return_dots_home(self):
        """Return all dots to their home positions."""
        for dot in self.dots:
            dot.set_target(dot.home_x, dot.home_y)
    
    def update(self, dt):
        """Update all dots."""
        for dot in self.dots:
            dot.update(dt)
    
    def update_theme(self):
        """Update colors for theme change."""
        self.canvas.itemconfig(
            self.circle,
            fill=get_color('circle_center'),
            outline=get_color('circle_border')
        )
        
        color = get_color('dot')
        for dot in self.dots:
            dot.update_color(color)


class StimulusCircle:
    """
    Outer stimulus circle that glows during calibration.
    NOW BIGGER and with SMOOTH SCALING animation on hover.
    Numbered 1-8 clockwise from right (0 degrees).
    """
    
    def __init__(self, canvas, number, center_x, center_y, radius):
        self.canvas = canvas
        self.number = number
        self.center_x = center_x
        self.center_y = center_y
        self.base_radius = radius  # Base radius (normal size)
        self.target_radius = radius  # Target radius (for animation)
        self.current_radius = radius  # Current animated radius
        
        self.is_glowing = False
        self.is_hovered = False
        
        # Create circle
        self.circle = canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill=get_color('stimulus_normal'),
            outline=get_color('stimulus_normal'),
            width=STIMULUS_NORMAL_WIDTH
        )
        
        # Create number label
        self.label = canvas.create_text(
            center_x, center_y,
            text=str(number),
            fill=get_color('text_secondary'),
            font=("Segoe UI", 14, "bold")  # Slightly larger font for bigger circles
        )
    
    def reposition(self, center_x, center_y):
        """Update position (for window resize)."""
        self.center_x = center_x
        self.center_y = center_y
        
        self._update_visual()
    
    def check_hover(self, cursor_x, cursor_y):
        """
        Check if cursor/gaze is hovering over this circle.
        
        Args:
            cursor_x: X coordinate of cursor/gaze
            cursor_y: Y coordinate of cursor/gaze
            
        Returns:
            True if hovering, False otherwise
        """
        dx = cursor_x - self.center_x
        dy = cursor_y - self.center_y
        distance = math.hypot(dx, dy)
        
        # Use hover threshold from config
        was_hovered = self.is_hovered
        self.is_hovered = distance <= STIMULUS_HOVER_THRESHOLD
        
        # Update target radius based on hover state
        if self.is_hovered:
            self.target_radius = STIMULUS_HOVER_RADIUS
        else:
            self.target_radius = self.base_radius
        
        return self.is_hovered
    
    def update_animation(self, dt):
        """
        Update smooth scaling animation.
        
        Args:
            dt: Delta time in seconds
        """
        # Smoothly interpolate current radius toward target radius
        if abs(self.current_radius - self.target_radius) > 0.1:
            diff = self.target_radius - self.current_radius
            self.current_radius += diff * STIMULUS_SCALE_SPEED * dt
            
            # Update visual
            self._update_visual()
    
    def _update_visual(self):
        """Update circle visual representation on canvas."""
        r = self.current_radius
        self.canvas.coords(
            self.circle,
            self.center_x - r, self.center_y - r,
            self.center_x + r, self.center_y + r
        )
        self.canvas.coords(self.label, self.center_x, self.center_y)
    
    def set_glow(self, glow):
        """Set glow state."""
        self.is_glowing = glow
        
        if glow:
            self.canvas.itemconfig(
                self.circle,
                outline=get_color('stimulus_glow'),
                width=STIMULUS_GLOW_WIDTH
            )
            self.canvas.itemconfig(self.label, fill=get_color('stimulus_glow'))
        else:
            self.canvas.itemconfig(
                self.circle,
                outline=get_color('stimulus_normal'),
                width=STIMULUS_NORMAL_WIDTH
            )
            self.canvas.itemconfig(self.label, fill=get_color('text_secondary'))
    
    def get_position(self):
        """Return center position."""
        return self.center_x, self.center_y
    
    def update_theme(self):
        """Update colors for theme change."""
        if self.is_glowing:
            self.canvas.itemconfig(
                self.circle,
                outline=get_color('stimulus_glow')
            )
            self.canvas.itemconfig(self.label, fill=get_color('stimulus_glow'))
        else:
            self.canvas.itemconfig(
                self.circle,
                fill=get_color('stimulus_normal'),
                outline=get_color('stimulus_normal')
            )
            self.canvas.itemconfig(self.label, fill=get_color('text_secondary'))


class Timer:
    """
    Small non-intrusive timer display in bottom-left corner.
    Shows elapsed time during calibration.
    """
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.x = TIMER_PADDING
        self.y = 0  # Will be set based on canvas height
        self.visible = False
        self.elapsed_time = 0.0
        
        # Create timer background
        self.bg = canvas.create_rectangle(
            0, 0, 0, 0,
            fill=get_color('timer_bg'),
            outline=get_color('text_secondary'),
            width=1,
            state="hidden"
        )
        
        # Create time label
        self.time_label = canvas.create_text(
            0, 0,
            text="00:00.0",
            fill=get_color('timer_text'),
            font=TIMER_FONT,
            anchor="w",
            state="hidden"
        )
        
        # Create description label
        self.desc_label = canvas.create_text(
            0, 0,
            text="Elapsed",
            fill=get_color('text_secondary'),
            font=TIMER_LABEL_FONT,
            anchor="w",
            state="hidden"
        )
    
    def reposition(self, canvas_height):
        """Update position based on canvas height."""
        self.y = canvas_height - TIMER_HEIGHT - TIMER_PADDING
        
        if self.visible:
            self._update_position()
    
    def _update_position(self):
        """Update all element positions."""
        # Background
        self.canvas.coords(
            self.bg,
            self.x, self.y,
            self.x + TIMER_WIDTH, self.y + TIMER_HEIGHT
        )
        
        # Time text
        self.canvas.coords(
            self.time_label,
            self.x + 10, self.y + TIMER_HEIGHT // 2
        )
        
        # Description
        self.canvas.coords(
            self.desc_label,
            self.x + 10, self.y + 10
        )
    
    def show(self):
        """Show timer."""
        self.visible = True
        self.elapsed_time = 0.0
        self.canvas.itemconfig(self.bg, state="normal")
        self.canvas.itemconfig(self.time_label, state="normal")
        self.canvas.itemconfig(self.desc_label, state="normal")
        self._update_position()
        self.update(0.0)
    
    def hide(self):
        """Hide timer."""
        self.visible = False
        self.canvas.itemconfig(self.bg, state="hidden")
        self.canvas.itemconfig(self.time_label, state="hidden")
        self.canvas.itemconfig(self.desc_label, state="hidden")
    
    def update(self, elapsed_time):
        """Update timer display."""
        self.elapsed_time = elapsed_time
        
        if self.visible:
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            deciseconds = int((elapsed_time % 1) * 10)
            
            time_str = f"{minutes:02d}:{seconds:02d}.{deciseconds}"
            self.canvas.itemconfig(self.time_label, text=time_str)
    
    def update_theme(self):
        """Update colors for theme change."""
        self.canvas.itemconfig(self.bg, fill=get_color('timer_bg'))
        self.canvas.itemconfig(self.bg, outline=get_color('text_secondary'))
        self.canvas.itemconfig(self.time_label, fill=get_color('timer_text'))
        self.canvas.itemconfig(self.desc_label, fill=get_color('text_secondary'))