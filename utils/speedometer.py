import numpy as np
import time
import imgui
from imgui.integrations.glfw import GlfwRenderer
def DrawSpeedDisplay():
        """Draw a cockpit-styled speed indicator with gauge and status lights"""
        if "transporter" not in self.gameState:
            return
            
        transporter = self.gameState["transporter"]
        current_speed = np.linalg.norm(transporter.velocity)
        max_speed = transporter.max_speed
        
        # Calculate acceleration effect intensity
        if hasattr(self, 'last_speed'):
            speed_delta = current_speed - self.last_speed
            if speed_delta > 0.5:  # Threshold for noticeable acceleration
                self.acceleration_effect_intensity = min(1.0, self.acceleration_effect_intensity + speed_delta * 0.01)
            else:
                self.acceleration_effect_intensity = max(0.0, self.acceleration_effect_intensity - 0.02)
        else:
            self.acceleration_effect_intensity = 0.0
        
        self.last_speed = current_speed
        
        imgui.new_frame()
        draw_list = imgui.get_background_draw_list()
        speed_percent = current_speed / max_speed
        
        # ----- COCKPIT-STYLE SPEED DISPLAY -----
        
        # 1. Create panel background
        gauge_radius = 60
        panel_width = gauge_radius * 2 + 40
        panel_height = gauge_radius * 2 + 60
        panel_x = 20
        panel_y = self.height - panel_height - 20
        
        center_x = panel_x + panel_width / 2
        center_y = panel_y + gauge_radius + 30
        
        panel_color = imgui.get_color_u32_rgba(0.15, 0.15, 0.18, 0.9)
        border_color = imgui.get_color_u32_rgba(0.6, 0.6, 0.7, 1.0)
        
        # Draw main panel with rounded corners
        draw_list.add_rect_filled(
            panel_x, panel_y, 
            panel_x + panel_width, panel_y + panel_height,
            panel_color, 10.0
        )
        
        # Add highlight at top for 3D effect
        highlight_color = imgui.get_color_u32_rgba(0.3, 0.3, 0.35, 0.8)
        draw_list.add_rect_filled(
            panel_x, panel_y, 
            panel_x + panel_width, panel_y + 8,
            highlight_color, 10.0, imgui.DRAW_ROUND_CORNERS_TOP
        )
        
        # Panel border
        draw_list.add_rect(
            panel_x, panel_y, 
            panel_x + panel_width, panel_y + panel_height,
            border_color, 10.0, 0, 2.0
        )
        
        # 2. Add title
        title_text = "VELOCITY"
        title_color = imgui.get_color_u32_rgba(0.8, 0.8, 1.0, 0.9)
        text_width = len(title_text) * 7
        draw_list.add_text(
            center_x - text_width / 2, panel_y + 10,
            title_color, title_text
        )
        
        # 3. Draw circular gauge background
        gauge_bg_color = imgui.get_color_u32_rgba(0.1, 0.1, 0.12, 0.8)
        draw_list.add_circle_filled(
            center_x, center_y, gauge_radius,
            gauge_bg_color
        )
        
        gauge_border_color = imgui.get_color_u32_rgba(0.5, 0.5, 0.6, 1.0)
        draw_list.add_circle(
            center_x, center_y, gauge_radius,
            gauge_border_color, 36, 2.0
        )
        
        # 4. Draw tick marks and speed numbers
        num_ticks = 10
        main_ticks = [0, 2, 5, 7]
        
        for i in range(num_ticks + 1):
            angle = np.radians(-90 + (270 * i / num_ticks))
            cos_a = np.cos(angle)
            sin_a = np.sin(angle)
            
            inner_factor = 0.85 if i in main_ticks else 0.9
            inner_x = center_x + gauge_radius * inner_factor * cos_a
            inner_y = center_y + gauge_radius * inner_factor * sin_a
            outer_x = center_x + gauge_radius * 0.95 * cos_a
            outer_y = center_y + gauge_radius * 0.95 * sin_a
            
            tick_color = imgui.get_color_u32_rgba(0.7, 0.7, 0.8, 0.9)
            tick_thickness = 2.0 if i in main_ticks else 1.0
            draw_list.add_line(inner_x, inner_y, outer_x, outer_y, tick_color, tick_thickness)
            
            if i in main_ticks:
                tick_speed = int((i / num_ticks) * max_speed)
                speed_text = f"{tick_speed}"
                
                text_factor = 0.75
                text_x = center_x + gauge_radius * text_factor * cos_a - 8
                text_y = center_y + gauge_radius * text_factor * sin_a - 8
                
                draw_list.add_text(text_x, text_y, tick_color, speed_text)
        
        # 5. Draw center cap
        cap_color = imgui.get_color_u32_rgba(0.3, 0.3, 0.35, 1.0)
        draw_list.add_circle_filled(center_x, center_y, 8, cap_color)
        cap_border_color = imgui.get_color_u32_rgba(0.6, 0.6, 0.7, 1.0)
        draw_list.add_circle(center_x, center_y, 8, cap_border_color, 0, 1.5)
        
        # 6. Draw speed indicator needle
        needle_angle = np.radians(-90 + (270 * speed_percent))
        needle_length = gauge_radius * 0.8
        needle_x = center_x + needle_length * np.cos(needle_angle)
        needle_y = center_y + needle_length * np.sin(needle_angle)
        
        # Choose needle color based on speed
        if speed_percent < 0.5:
            r = speed_percent * 2
            g = 1.0
            b = 0.0
        else:
            r = 1.0
            g = 2.0 * (1.0 - speed_percent)
            b = 0.0
        
        needle_color = imgui.get_color_u32_rgba(r, g, b, 0.9)
        needle_glow_color = imgui.get_color_u32_rgba(r, g, b, 0.4)
        
        # Draw glow if accelerating
        if self.acceleration_effect_intensity > 0.1:
            draw_list.add_line(
                center_x, center_y, needle_x, needle_y,
                needle_glow_color, 5.0 + self.acceleration_effect_intensity * 3
            )
        
        # Draw actual needle
        draw_list.add_line(center_x, center_y, needle_x, needle_y, needle_color, 2.0)
        
        # 7. Draw digital speed value
        digital_text = f"{int(current_speed)}"
        text_width = len(digital_text) * 7
        digital_color = imgui.get_color_u32_rgba(r, g, b, 1.0)
        draw_list.add_text(
            center_x - text_width/2, center_y + gauge_radius/2,
            digital_color, digital_text
        )
        
        # 8. Add indicator bulbs
        bulb_radius = 7
        bulb_spacing = 26
        num_bulbs = 5
        bulb_y = panel_y + panel_height - 25
        bulb_start_x = center_x - ((num_bulbs - 1) * bulb_spacing) / 2
        
        for i in range(num_bulbs):
            bulb_x = bulb_start_x + i * bulb_spacing
            
            # Different bulb statuses
            if i == 0:  # Thrust indicator
                if transporter.is_accelerating:
                    bulb_color = imgui.get_color_u32_rgba(0.4, 0.7, 1.0, 0.9)
                    glow_color = imgui.get_color_u32_rgba(0.4, 0.7, 1.0, 0.4)
                    draw_list.add_circle_filled(bulb_x, bulb_y, bulb_radius * 1.8, glow_color)
                else:
                    bulb_color = imgui.get_color_u32_rgba(0.2, 0.3, 0.5, 0.7)
            elif i == 1:  # High speed indicator
                if speed_percent > 0.75:
                    bulb_color = imgui.get_color_u32_rgba(1.0, 0.9, 0.2, 0.9)
                    glow_color = imgui.get_color_u32_rgba(1.0, 0.9, 0.2, 0.4)
                    draw_list.add_circle_filled(bulb_x, bulb_y, bulb_radius * 1.5, glow_color)
                else:
                    bulb_color = imgui.get_color_u32_rgba(0.5, 0.5, 0.2, 0.7)
            elif i == 2:  # Max speed warning
                if speed_percent > 0.95:
                    bulb_color = imgui.get_color_u32_rgba(1.0, 0.3, 0.2, 0.9)
                    glow_color = imgui.get_color_u32_rgba(1.0, 0.3, 0.2, 0.4)
                    draw_list.add_circle_filled(bulb_x, bulb_y, bulb_radius * 1.5, glow_color)
                else:
                    bulb_color = imgui.get_color_u32_rgba(0.5, 0.2, 0.2, 0.7)
            elif i == 3:  # Random blink - system status
                if (int(time.time() * 2) % (6 + i)) < 1:
                    bulb_color = imgui.get_color_u32_rgba(0.3, 0.8, 0.4, 0.9)
                else:
                    bulb_color = imgui.get_color_u32_rgba(0.2, 0.4, 0.2, 0.7)
            else:  # Another random blink - system status
                if (int(time.time() * 3) % (8 + i)) < 2:
                    bulb_color = imgui.get_color_u32_rgba(0.4, 0.6, 1.0, 0.9)
                else:
                    bulb_color = imgui.get_color_u32_rgba(0.2, 0.3, 0.5, 0.7)
            
            # Draw bulb with border
            draw_list.add_circle_filled(bulb_x, bulb_y, bulb_radius, bulb_color)
            border_color = imgui.get_color_u32_rgba(0.6, 0.6, 0.7, 0.8)
            draw_list.add_circle(bulb_x, bulb_y, bulb_radius, border_color, 0, 1.5)
        
        # 9. Add labels under bulbs
        labels = ["THRUST", "HIGH", "MAX", "SYS1", "SYS2"]
        label_color = imgui.get_color_u32_rgba(0.7, 0.7, 0.8, 0.8)
        
        for i, label in enumerate(labels):
            label_x = bulb_start_x + i * bulb_spacing - 10
            label_y = bulb_y + bulb_radius + 5
            draw_list.add_text(label_x, label_y, label_color, label)
        
        # Draw movement effects
        speed_ratio = current_speed / max_speed
        if speed_ratio > 0.01 or self.acceleration_effect_intensity > 0.01:
            self.DrawMovementEffect(draw_list, speed_ratio)
        
        imgui.render()
        self.gui.render(imgui.get_draw_data())