# -*- coding: utf-8 -*-
# ===============================================
# FILE: ui_components.py
# UI Components for BCI Interface
# Updated: Cross (+) for calibration, dots for testing
# ===============================================

import math
import random
from config import *


class Dot:
    """Represents a single dot in the center circle with spring physics."""
    
    def __init__(self, canvas, home_x, home_y, color):
        self.canvas = canvas
        self.home_x = home_x
        self.home_y = home_y
        
        self.x = home_x
        self.y = home_y
        self.vx = 0.0
        self.vy = 0.0
        
        self.target_x = home_x
        self.target_y = home_y
        
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
        self.home_x = x
        self.home_y = y
    
    def set_target(self, x, y):
        self.target_x = x
        self.target_y = y
    
    def update(self, dt):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)
        
        if dist > 0.5:
            ax = dx * DOT_SPRING_STRENGTH * dt
            ay = dy * DOT_SPRING_STRENGTH * dt
            
            self.vx += ax
            self.vy += ay
        else:
            self.vx *= 0.5
            self.vy *= 0.5
        
        self.vx *= DOT_DAMPING
        self.vy *= DOT_DAMPING
        
        speed = math.hypot(self.vx, self.vy)
        max_speed = DOT_MAX_SPEED * dt
        if speed > max_speed:
            scale = max_speed / speed
            self.vx *= scale
            self.vy *= scale
        
        self.x += self.vx
        self.y += self.vy
        
        self._update_visual()
    
    def _update_visual(self):
        # Keep dots within circle bounds
        dx = self.x - self.home_x
        dy = self.y - self.home_y
        
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
        self.canvas.itemconfig(self.dot, fill=color)
    
    def hide(self):
        self.canvas.itemconfig(self.dot, state="hidden")
        self.canvas.itemconfig(self.glow, state="hidden")
    
    def show(self):
        self.canvas.itemconfig(self.dot, state="normal")


class CenterCircle:
    """Central circle - dots for testing, cross for calibration."""
    
    def __init__(self, canvas, center_x, center_y, radius):
        self.canvas = canvas
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.dots = []
        self.mode = "testing"  # "testing" or "calibration"
        
        # Circle border
        self.circle = canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill=get_color('circle_center'),
            outline=get_color('circle_border'),
            width=2
        )
        
        # Create dots (for testing phase)
        self._create_dots()
        
        # Create cross (for calibration phase)
        cross_size = radius * 0.5
        self.cross_h = canvas.create_line(
            center_x - cross_size, center_y,
            center_x + cross_size, center_y,
            fill=get_color('text_primary'),
            width=3,
            state="hidden"
        )
        self.cross_v = canvas.create_line(
            center_x, center_y - cross_size,
            center_x, center_y + cross_size,
            fill=get_color('text_primary'),
            width=3,
            state="hidden"
        )
    
    def _create_dots(self):
        """Create dots that stay within circle bounds."""
        color = get_color('dot')
        positions = []
        rows = 6
        cols = 6
        
        spacing = self.radius * 1.2 / rows
        
        for row in range(rows):
            for col in range(cols):
                x_offset = (col - cols/2) * spacing
                y_offset = (row - rows/2) * spacing
                
                x_offset += random.uniform(-spacing*0.1, spacing*0.1)
                y_offset += random.uniform(-spacing*0.1, spacing*0.1)
                
                x = self.center_x + x_offset
                y = self.center_y + y_offset
                
                dx = x - self.center_x
                dy = y - self.center_y
                dist = math.hypot(dx, dy)
                
                # Keep dots well within circle
                if dist < self.radius * 0.65:
                    positions.append((x, y))
        
        random.shuffle(positions)
        positions = positions[:DOT_COUNT]
        
        for x, y in positions:
            dot = Dot(self.canvas, x, y, color)
            self.dots.append(dot)
    
    def set_mode(self, mode):
        """Switch between 'testing' (dots) and 'calibration' (cross)."""
        self.mode = mode
        
        if mode == "calibration":
            # Hide dots, show cross
            for dot in self.dots:
                dot.hide()
            self.canvas.itemconfig(self.cross_h, state="normal")
            self.canvas.itemconfig(self.cross_v, state="normal")
        else:
            # Show dots, hide cross
            for dot in self.dots:
                dot.show()
            self.canvas.itemconfig(self.cross_h, state="hidden")
            self.canvas.itemconfig(self.cross_v, state="hidden")
    
    def resize(self, center_x, center_y, radius):
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
        
        # Update cross
        cross_size = radius * 0.5
        self.canvas.coords(
            self.cross_h,
            center_x - cross_size, center_y,
            center_x + cross_size, center_y
        )
        self.canvas.coords(
            self.cross_v,
            center_x, center_y - cross_size,
            center_x, center_y + cross_size
        )
        
        # Update dots
        for dot in self.dots:
            offset_x = dot.home_x - (center_x - dx)
            offset_y = dot.home_y - (center_y - dy)
            
            new_home_x = center_x + offset_x * scale
            new_home_y = center_y + offset_y * scale
            
            # Ensure dot stays within bounds
            dx_center = new_home_x - center_x
            dy_center = new_home_y - center_y
            dist_from_center = math.hypot(dx_center, dy_center)
            
            if dist_from_center > radius * 0.65:
                scale_factor = (radius * 0.65) / dist_from_center
                new_home_x = center_x + dx_center * scale_factor
                new_home_y = center_y + dy_center * scale_factor
            
            dot.set_home(new_home_x, new_home_y)
            
            if abs(dot.target_x - dot.home_x) < 1:
                dot.x = new_home_x
                dot.y = new_home_y
                dot.target_x = new_home_x
                dot.target_y = new_home_y
    
    def move_dots_toward(self, target_x, target_y, progress_ratio):
        """Move dots toward target (testing phase only)."""
        if self.mode != "testing":
            return
        
        dx = target_x - self.center_x
        dy = target_y - self.center_y
        dist = math.hypot(dx, dy)
        
        if dist > 10:
            dx /= dist
            dy /= dist
            
            push_dist = self.radius * 0.40 * progress_ratio
            
            for dot in self.dots:
                target_x_pos = dot.home_x + dx * push_dist
                target_y_pos = dot.home_y + dy * push_dist
                
                # Ensure target stays within circle bounds
                dx_center = target_x_pos - self.center_x
                dy_center = target_y_pos - self.center_y
                dist_from_center = math.hypot(dx_center, dy_center)
                
                max_dist = self.radius * 0.75
                if dist_from_center > max_dist:
                    scale = max_dist / dist_from_center
                    target_x_pos = self.center_x + dx_center * scale
                    target_y_pos = self.center_y + dy_center * scale
                
                dot.set_target(target_x_pos, target_y_pos)
        else:
            self.return_dots_home()
    
    def return_dots_home(self):
        """Return dots to home position."""
        for dot in self.dots:
            dot.set_target(dot.home_x, dot.home_y)
    
    def update(self, dt):
        """Update dot physics."""
        if self.mode == "testing":
            for dot in self.dots:
                dot.update(dt)
    
    def update_theme(self):
        self.canvas.itemconfig(
            self.circle,
            fill=get_color('circle_center'),
            outline=get_color('circle_border')
        )
        
        self.canvas.itemconfig(self.cross_h, fill=get_color('text_primary'))
        self.canvas.itemconfig(self.cross_v, fill=get_color('text_primary'))
        
        color = get_color('dot')
        for dot in self.dots:
            dot.update_color(color)
    
    def hide(self):
        self.canvas.itemconfig(self.circle, state="hidden")
        for dot in self.dots:
            dot.hide()
        self.canvas.itemconfig(self.cross_h, state="hidden")
        self.canvas.itemconfig(self.cross_v, state="hidden")
    
    def show(self):
        self.canvas.itemconfig(self.circle, state="normal")
        if self.mode == "testing":
            for dot in self.dots:
                dot.show()
        else:
            self.canvas.itemconfig(self.cross_h, state="normal")
            self.canvas.itemconfig(self.cross_v, state="normal")


class StimulusCircle:
    """Outer stimulus circle with numbering."""
    
    def __init__(self, canvas, number, center_x, center_y, radius):
        self.canvas = canvas
        self.number = number
        self.center_x = center_x
        self.center_y = center_y
        self.base_radius = radius
        self.target_radius = radius
        self.current_radius = radius
        
        self.is_glowing = False
        self.is_hovered = False
        
        self.circle = canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill=get_color('stimulus_normal'),
            outline=get_color('stimulus_border'),
            width=STIMULUS_NORMAL_WIDTH
        )
        
        self.label = canvas.create_text(
            center_x, center_y,
            text=str(number),
            fill=get_color('text_primary'),
            font=("Segoe UI", 20, "bold")
        )
    
    def reposition(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self._update_visual()
    
    def check_hover(self, cursor_x, cursor_y):
        dx = cursor_x - self.center_x
        dy = cursor_y - self.center_y
        distance = math.hypot(dx, dy)
        
        was_hovered = self.is_hovered
        self.is_hovered = distance <= STIMULUS_HOVER_THRESHOLD
        
        if self.is_hovered:
            self.target_radius = STIMULUS_HOVER_RADIUS
        else:
            self.target_radius = self.base_radius
        
        return self.is_hovered
    
    def update_animation(self, dt):
        if abs(self.current_radius - self.target_radius) > 0.1:
            diff = self.target_radius - self.current_radius
            self.current_radius += diff * STIMULUS_SCALE_SPEED * dt
            self._update_visual()
    
    def _update_visual(self):
        r = self.current_radius
        self.canvas.coords(
            self.circle,
            self.center_x - r, self.center_y - r,
            self.center_x + r, self.center_y + r
        )
        self.canvas.coords(self.label, self.center_x, self.center_y)
    
    def set_glow(self, glow):
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
                fill=get_color('stimulus_normal'),
                outline=get_color('stimulus_border'),
                width=STIMULUS_NORMAL_WIDTH
            )
            self.canvas.itemconfig(self.label, fill=get_color('text_primary'))
    
    def get_position(self):
        return self.center_x, self.center_y
    
    def update_theme(self):
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
                outline=get_color('stimulus_border')
            )
            self.canvas.itemconfig(self.label, fill=get_color('text_primary'))
    
    def hide(self):
        self.canvas.itemconfig(self.circle, state="hidden")
        self.canvas.itemconfig(self.label, state="hidden")
    
    def show(self):
        self.canvas.itemconfig(self.circle, state="normal")
        self.canvas.itemconfig(self.label, state="normal")


class Timer:
    """Timer display (not shown during calibration per requirements)."""
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.x = TIMER_PADDING
        self.y = 0
        self.visible = False
        self.elapsed_time = 0.0
        
        self.bg = canvas.create_rectangle(
            0, 0, 0, 0,
            fill=get_color('timer_bg'),
            outline=get_color('timer_border'),
            width=2,
            state="hidden"
        )
        
        self.time_label = canvas.create_text(
            0, 0,
            text="00:00.0",
            fill=get_color('timer_text'),
            font=TIMER_FONT,
            anchor="w",
            state="hidden"
        )
        
        self.desc_label = canvas.create_text(
            0, 0,
            text="Elapsed",
            fill=get_color('text_secondary'),
            font=TIMER_LABEL_FONT,
            anchor="w",
            state="hidden"
        )
    
    def reposition(self, canvas_height):
        self.y = canvas_height - TIMER_HEIGHT - TIMER_PADDING
        if self.visible:
            self._update_position()
    
    def _update_position(self):
        self.canvas.coords(
            self.bg,
            self.x, self.y,
            self.x + TIMER_WIDTH, self.y + TIMER_HEIGHT
        )
        
        self.canvas.coords(
            self.time_label,
            self.x + 10, self.y + TIMER_HEIGHT // 2
        )
        
        self.canvas.coords(
            self.desc_label,
            self.x + 10, self.y + 10
        )
    
    def show(self):
        self.visible = True
        self.elapsed_time = 0.0
        self.canvas.itemconfig(self.bg, state="normal")
        self.canvas.itemconfig(self.time_label, state="normal")
        self.canvas.itemconfig(self.desc_label, state="normal")
        self._update_position()
        self.update(0.0)
    
    def hide(self):
        self.visible = False
        self.canvas.itemconfig(self.bg, state="hidden")
        self.canvas.itemconfig(self.time_label, state="hidden")
        self.canvas.itemconfig(self.desc_label, state="hidden")
    
    def update(self, elapsed_time):
        """Update with total elapsed time."""
        self.elapsed_time = elapsed_time
        
        if self.visible:
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            deciseconds = int((elapsed_time % 1) * 10)
            
            time_str = f"{minutes:02d}:{seconds:02d}.{deciseconds}"
            self.canvas.itemconfig(self.time_label, text=time_str)
    
    def update_countdown(self, remaining_time, phase_name):
        """Update with countdown and phase name."""
        if self.visible:
            seconds = max(0, int(remaining_time))
            deciseconds = max(0, int((remaining_time % 1) * 10))
            
            time_str = f"{seconds:02d}.{deciseconds}s"
            self.canvas.itemconfig(self.time_label, text=time_str)
            self.canvas.itemconfig(self.desc_label, text=phase_name)
    
    def update_theme(self):
        self.canvas.itemconfig(self.bg, fill=get_color('timer_bg'))
        self.canvas.itemconfig(self.bg, outline=get_color('timer_border'))
        self.canvas.itemconfig(self.time_label, fill=get_color('timer_text'))
        self.canvas.itemconfig(self.desc_label, fill=get_color('text_secondary'))


class RestScreen:
    """Full-screen REST/START/THANK YOU display."""
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.width = 0
        self.height = 0
        self.visible = False
        
        # Background
        self.bg = canvas.create_rectangle(
            0, 0, 0, 0,
            fill=get_color('rest_screen_bg'),
            outline="",
            state="hidden"
        )
        
        # Main text (REST/START/THANK YOU)
        self.text = canvas.create_text(
            0, 0,
            text=REST_SCREEN_TEXT,
            fill=get_color('rest_screen_text'),
            font=REST_SCREEN_FONT,
            state="hidden"
        )
        
        # Instruction text (for EEG mode)
        self.instruction = canvas.create_text(
            0, 0,
            text="",
            fill=get_color('rest_screen_text'),
            font=REST_SCREEN_INSTRUCTION_FONT,
            state="hidden"
        )
    
    def reposition(self, width, height):
        """Update position based on canvas dimensions."""
        self.width = width
        self.height = height
        
        if self.visible:
            self._update_position()
    
    def _update_position(self):
        """Update canvas element positions."""
        self.canvas.coords(
            self.bg,
            0, 0,
            self.width, self.height
        )
        
        self.canvas.coords(
            self.text,
            self.width // 2,
            self.height // 2 - 60
        )
        
        self.canvas.coords(
            self.instruction,
            self.width // 2,
            self.height // 2 + 60
        )
    
    def show(self, main_text="REST"):
        """Show rest screen with custom main text."""
        self.visible = True
        self.canvas.itemconfig(self.text, text=main_text, state="normal")
        self.canvas.itemconfig(self.bg, state="normal")
        self.canvas.itemconfig(self.instruction, state="hidden")
        
        self.canvas.tag_raise(self.bg)
        self.canvas.tag_raise(self.text)
        self.canvas.tag_raise(self.instruction)
        
        self._update_position()
    
    def show_with_instruction(self, main_text, instruction_text):
        """Show rest screen with instruction (for EEG mode)."""
        self.visible = True
        self.canvas.itemconfig(self.text, text=main_text, state="normal")
        self.canvas.itemconfig(self.instruction, text=instruction_text, state="normal")
        self.canvas.itemconfig(self.bg, state="normal")
        
        self.canvas.tag_raise(self.bg)
        self.canvas.tag_raise(self.text)
        self.canvas.tag_raise(self.instruction)
        
        self._update_position()
    
    def hide(self):
        """Hide rest screen."""
        self.visible = False
        self.canvas.itemconfig(self.bg, state="hidden")
        self.canvas.itemconfig(self.text, state="hidden")
        self.canvas.itemconfig(self.instruction, state="hidden")
    
    def update_theme(self):
        """Update colors for theme change."""
        self.canvas.itemconfig(self.bg, fill=get_color('rest_screen_bg'))
        self.canvas.itemconfig(self.text, fill=get_color('rest_screen_text'))
        self.canvas.itemconfig(self.instruction, fill=get_color('rest_screen_text'))