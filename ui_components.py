# -*- coding: utf-8 -*-
# ===============================================
# FILE: ui_components.py
# UI Components for BCI Interface
# Updated: Stimulus circles with black fill and white borders
# Added instruction display for EEG mode
# Fixed: Dots always remain inside circle
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
    """Central circle containing animated dots."""
    
    def __init__(self, canvas, center_x, center_y, radius):
        self.canvas = canvas
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.dots = []
        
        self.circle = canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill=get_color('circle_center'),
            outline=get_color('circle_border'),
            width=2
        )
        
        self._create_dots()
    
    def _create_dots(self):
        """Create dots that always stay within circle bounds."""
        color = get_color('dot')
        positions = []
        rows = 7
        cols = 7
        
        # Reduced spacing to keep dots more centered
        spacing = self.radius * 1.4 / rows
        
        for row in range(rows):
            for col in range(cols):
                x_offset = (col - cols/2) * spacing
                y_offset = (row - rows/2) * spacing
                
                # Reduced randomness
                x_offset += random.uniform(-spacing*0.15, spacing*0.15)
                y_offset += random.uniform(-spacing*0.15, spacing*0.15)
                
                x = self.center_x + x_offset
                y = self.center_y + y_offset
                
                dx = x - self.center_x
                dy = y - self.center_y
                dist = math.hypot(dx, dy)
                
                # Tighter bounds - keep dots well within circle
                if dist < self.radius * 0.75:
                    positions.append((x, y))
        
        random.shuffle(positions)
        positions = positions[:DOT_COUNT]
        
        for x, y in positions:
            dot = Dot(self.canvas, x, y, color)
            self.dots.append(dot)
    
    def resize(self, center_x, center_y, radius):
        scale = radius / self.radius if self.radius > 0 else 1
        dx = center_x - self.center_x
        dy = center_y - self.center_y
        
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        
        self.canvas.coords(
            self.circle,
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius
        )
        
        for dot in self.dots:
            offset_x = dot.home_x - (center_x - dx)
            offset_y = dot.home_y - (center_y - dy)
            
            new_home_x = center_x + offset_x * scale
            new_home_y = center_y + offset_y * scale
            
            # Ensure dot stays within bounds after resize
            dx_center = new_home_x - center_x
            dy_center = new_home_y - center_y
            dist_from_center = math.hypot(dx_center, dy_center)
            
            if dist_from_center > radius * 0.75:
                scale_factor = (radius * 0.75) / dist_from_center
                new_home_x = center_x + dx_center * scale_factor
                new_home_y = center_y + dy_center * scale_factor
            
            dot.set_home(new_home_x, new_home_y)
            
            if abs(dot.target_x - dot.home_x) < 1:
                dot.x = new_home_x
                dot.y = new_home_y
                dot.target_x = new_home_x
                dot.target_y = new_home_y
    
    def move_dots_toward(self, target_x, target_y, progress_ratio):
        dx = target_x - self.center_x
        dy = target_y - self.center_y
        dist = math.hypot(dx, dy)
        
        if dist > 10:
            dx /= dist
            dy /= dist
            
            push_dist = self.radius * 0.5 * progress_ratio
            
            for dot in self.dots:
                target_x_pos = dot.home_x + dx * push_dist
                target_y_pos = dot.home_y + dy * push_dist
                
                # Ensure target stays within circle
                dx_center = target_x_pos - self.center_x
                dy_center = target_y_pos - self.center_y
                dist_from_center = math.hypot(dx_center, dy_center)
                
                if dist_from_center > self.radius * 0.90:
                    scale = (self.radius * 0.90) / dist_from_center
                    target_x_pos = self.center_x + dx_center * scale
                    target_y_pos = self.center_y + dy_center * scale
                
                dot.set_target(target_x_pos, target_y_pos)
        else:
            self.return_dots_home()
    
    def return_dots_home(self):
        for dot in self.dots:
            dot.set_target(dot.home_x, dot.home_y)
    
    def update(self, dt):
        for dot in self.dots:
            dot.update(dt)
    
    def update_theme(self):
        self.canvas.itemconfig(
            self.circle,
            fill=get_color('circle_center'),
            outline=get_color('circle_border')
        )
        
        color = get_color('dot')
        for dot in self.dots:
            dot.update_color(color)
    
    def hide(self):
        self.canvas.itemconfig(self.circle, state="hidden")
        for dot in self.dots:
            dot.hide()
    
    def show(self):
        self.canvas.itemconfig(self.circle, state="normal")
        for dot in self.dots:
            dot.show()


class StimulusCircle:
    """Outer stimulus circle with black fill, white border, and white numbers."""
    
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
        
        # Black fill with white border
        self.circle = canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill=get_color('stimulus_normal'),
            outline=get_color('stimulus_border'),
            width=STIMULUS_NORMAL_WIDTH
        )
        
        # White number inside
        self.label = canvas.create_text(
            center_x, center_y,
            text=str(number),
            fill=get_color('text_primary'),
            font=("Segoe UI", 14, "bold")
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
    """Timer display with countdown functionality."""
    
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
    """Full-screen REST display during gap periods with optional instruction text."""
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.width = 0
        self.height = 0
        self.visible = False
        
        # Background rectangle
        self.bg = canvas.create_rectangle(
            0, 0, 0, 0,
            fill=get_color('rest_screen_bg'),
            outline="",
            state="hidden"
        )
        
        # REST text
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
        """Update position and size based on canvas dimensions."""
        self.width = width
        self.height = height
        
        if self.visible:
            self._update_position()
    
    def _update_position(self):
        """Update canvas element positions."""
        # Full screen background
        self.canvas.coords(
            self.bg,
            0, 0,
            self.width, self.height
        )
        
        # Centered REST text
        self.canvas.coords(
            self.text,
            self.width // 2,
            self.height // 2 - 50
        )
        
        # Instruction text below REST
        self.canvas.coords(
            self.instruction,
            self.width // 2,
            self.height // 2 + 50
        )
    
    def show(self):
        """Show rest screen without instruction."""
        self.visible = True
        self.canvas.itemconfig(self.bg, state="normal")
        self.canvas.itemconfig(self.text, state="normal")
        self.canvas.itemconfig(self.instruction, state="hidden")
        
        # Bring to front
        self.canvas.tag_raise(self.bg)
        self.canvas.tag_raise(self.text)
        self.canvas.tag_raise(self.instruction)
        
        self._update_position()
    
    def show_with_instruction(self, instruction_text):
        """Show rest screen with instruction text (for EEG mode)."""
        self.visible = True
        self.canvas.itemconfig(self.bg, state="normal")
        self.canvas.itemconfig(self.text, state="normal")
        self.canvas.itemconfig(self.instruction, text=instruction_text, state="normal")
        
        # Bring to front
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