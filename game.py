import imgui
import numpy as np
from utils.graphics import Object, Camera, Shader
import sys
import time
from enum import Enum, auto
import random
from assets.objects.objects import Pirate, Transporter, Planet, SpaceStation
from assets.shaders.shaders import standard_shader, laser_shader, minimap_shader, crosshair_shader, destination_shader

class GameScreen(Enum):
    MAIN_MENU = auto()
    GAME = auto()
    WIN = auto()
    GAME_OVER = auto()

class Game:
    def __init__(self, height, width, gui):
        self.gui = gui
        self.height = height
        self.width = width
        self.screen = GameScreen.MAIN_MENU
        self.speed_lines = []  # For speed line effect
        self.acceleration_effect_intensity = 0.0
        self.acceleration_color_tint = np.array([0.0, 0.0, 0.2, 0.0], dtype=np.float32)

    def InitScene(self):
        if self.screen == GameScreen.GAME:
            self.camera = Camera(self.height, self.width)
            self.shaders = []
            self.gameState = {}
            
            self.worldMin = np.array([-5000, -5000, -5000], dtype=np.float32)
            self.worldMax = np.array([5000, 5000, 5000], dtype=np.float32)
            
            self.gameState["transporter"] = Transporter()
            self.shaders.append(self.gameState["transporter"].shader)
            
            self.gameState["planets"] = []
            self.gameState["spaceStations"] = []
            self.gameState["pirates"] = []
            self.gameState["lasers"] = []
            
            # Create random planets
            self.n_planets = 30
            for i in range(self.n_planets):
                planet = Planet()
                random_pos = np.array([
                    random.uniform(self.worldMin[0], self.worldMax[0]),
                    random.uniform(self.worldMin[1], self.worldMax[1]),
                    random.uniform(self.worldMin[2], self.worldMax[2])
                ], dtype=np.float32)
                planet.set_position(random_pos)
                
                random_color = np.array([
                    random.uniform(0.3, 1.0),
                    random.uniform(0.3, 1.0),
                    random.uniform(0.3, 1.0),
                    1.0
                ], dtype=np.float32)
                planet.set_color(random_color)
                self.gameState["planets"].append(planet)
                self.shaders.append(planet.shader)
                
                # Create a space station for each planet
                station = SpaceStation()
                orbit_radius = 150.0
                orbit_angle = random.uniform(0, 2 * np.pi)
                station_pos = random_pos + np.array([
                    orbit_radius * np.cos(orbit_angle),
                    0,  # Keep on same y-level as planet
                    orbit_radius * np.sin(orbit_angle)
                ], dtype=np.float32)
                station.set_position(station_pos)
                station.parent_planet = planet
                station.orbit_angle = orbit_angle
                station.orbit_radius = orbit_radius
                station.orbit_speed = random.uniform(0.2, 0.5)
                self.gameState["spaceStations"].append(station)
                self.shaders.append(station.shader)

            # Randomly choose start and destination
            if len(self.gameState["spaceStations"]) >= 2:
                start_idx = random.randrange(0, len(self.gameState["spaceStations"]))
                dest_idx = start_idx
                while dest_idx == start_idx:
                    dest_idx = random.randrange(0, len(self.gameState["spaceStations"]))
                
                self.gameState["start_station"] = self.gameState["spaceStations"][start_idx]
                self.gameState["destination_station"] = self.gameState["spaceStations"][dest_idx]
                
                # Set transporter at start station
                start_pos = self.gameState["start_station"].position.copy()
                start_pos += np.array([0, 20, 0], dtype=np.float32)
                self.gameState["transporter"].set_position(start_pos)
                self.gameState["transporter"].start_planet = self.gameState["start_station"].parent_planet
                self.gameState["transporter"].target_planet = self.gameState["destination_station"].parent_planet
                
                # Make the destination planet distinct
                dest_planet = self.gameState["destination_station"].parent_planet
                dest_planet.graphics_obj.properties['scale'] *= 1.2
                dest_planet.shader = Shader(destination_shader["vertex_shader"], 
                                         destination_shader["fragment_shader"])
                dest_planet.graphics_obj.shader = dest_planet.shader
                self.shaders.append(dest_planet.shader)
                dest_planet.set_color(np.array([1.0, 0.9, 0.3, 1.0]))
                
            # Initialize Pirates
            self.n_pirates = 10
            for i in range(self.n_pirates):
                pirate = Pirate()
                
                # Generate random position away from player start
                while True:
                    random_pos = np.array([
                        random.uniform(self.worldMin[0], self.worldMax[0]),
                        random.uniform(self.worldMin[1], self.worldMax[1]),
                        random.uniform(self.worldMin[2], self.worldMax[2])
                    ], dtype=np.float32)
                    
                    if "start_station" in self.gameState:
                        distance = np.linalg.norm(random_pos - self.gameState["start_station"].position)
                        if distance > 500.0:  # Safe distance from player start
                            break
                    else:
                        break
                
                pirate.set_position(random_pos)
                self.gameState["pirates"].append(pirate)
                self.shaders.append(pirate.shader)

    def ProcessFrame(self, inputs, time):
        # Handle view toggle with '1' key
        if inputs["1"] and not hasattr(self, "key_cooldown"):
            if self.screen == GameScreen.GAME and "transporter" in self.gameState:
                self.gameState["transporter"].toggle_view()
                self.key_cooldown = 0.2  # Cooldown to prevent multiple toggles
    
        if hasattr(self, "key_cooldown"):
            self.key_cooldown -= time["deltaTime"]
            if self.key_cooldown <= 0:
                delattr(self, "key_cooldown")
                
        self.UpdateScene(inputs, time)
        self.DrawScene()
        self.DrawText()

    def DrawText(self):
        if self.screen == GameScreen.MAIN_MENU:
            window_w, window_h = 400, 200
            x_pos = (self.width - window_w) / 2
            y_pos = (self.height - window_h) / 2

            imgui.new_frame()
            imgui.set_next_window_position(x_pos, y_pos)
            imgui.set_next_window_size(window_w, window_h)
            imgui.begin("Main Menu", False, imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_RESIZE)

            button_w, button_h = 150, 40
            imgui.set_cursor_pos_x((window_w - button_w) / 2)
            if imgui.button("New Game", button_w, button_h):
                self.screen = GameScreen.GAME
                self.InitScene()

            imgui.spacing()
            imgui.set_cursor_pos_x((window_w - button_w) / 2)
            if imgui.button("Exit", button_w, button_h):
                sys.exit()

            imgui.end()
            imgui.render()
            self.gui.render(imgui.get_draw_data())

        elif self.screen == GameScreen.WIN:
            window_w, window_h = 400, 200
            x_pos = (self.width - window_w) / 2
            y_pos = (self.height - window_h) / 2
            
            imgui.new_frame()
            imgui.set_next_window_position(x_pos, y_pos)
            imgui.set_next_window_size(window_w, window_h)
            imgui.begin("MISSION COMPLETE", False, imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_RESIZE)
            
            imgui.text("You successfully reached the destination!")
            imgui.text("Cargo delivered. Well done, captain!")
            imgui.spacing()
            
            button_w, button_h = 150, 40
            imgui.set_cursor_pos_x((window_w - button_w) / 2)
            if imgui.button("New Mission", button_w, button_h):
                self.screen = GameScreen.GAME
                self.InitScene()
                
            imgui.spacing()
            imgui.set_cursor_pos_x((window_w - button_w) / 2)
            if imgui.button("Main Menu", button_w, button_h):
                self.screen = GameScreen.MAIN_MENU
                
            imgui.end()
            imgui.render()
            self.gui.render(imgui.get_draw_data())

        elif self.screen == GameScreen.GAME_OVER:
            window_w, window_h = 400, 250
            x_pos = (self.width - window_w) / 2
            y_pos = (self.height - window_h) / 2
            
            imgui.new_frame()
            imgui.set_next_window_position(x_pos, y_pos)
            imgui.set_next_window_size(window_w, window_h)
            imgui.begin("GAME OVER", False, imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_RESIZE)
            
            imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.3, 0.3, 1.0)
            imgui.text("Your ship was destroyed by a pirate vessel!")
            imgui.pop_style_color()
            
            imgui.spacing()
            imgui.text("The cargo was lost in the deep space.")
            imgui.text("Better luck on your next mission, captain.")
            imgui.spacing()
            imgui.separator()
            imgui.spacing()
            
            button_w, button_h = 150, 40
            imgui.set_cursor_pos_x((window_w - button_w) / 2)
            if imgui.button("Try Again", button_w, button_h):
                self.screen = GameScreen.GAME
                self.InitScene()
                
            imgui.spacing()
            imgui.set_cursor_pos_x((window_w - button_w) / 2)
            if imgui.button("Main Menu", button_w, button_h):
                self.screen = GameScreen.MAIN_MENU
            
            imgui.end()
            imgui.render()
            self.gui.render(imgui.get_draw_data())

    def UpdateScene(self, inputs, time):
        delta_time = time['deltaTime']
        if self.screen == GameScreen.GAME:
            # Update transporter first
            transporter = self.gameState["transporter"]
            transporter.update(inputs, delta_time)
            transporter_pos = transporter.position
            
            # Update camera based on view mode
            if transporter.view == 1:  # Third-person view
                behind_offset = -transporter.forward_direction * 50
                up_offset = transporter.up_direction * 20
                
                self.camera.position = transporter_pos + behind_offset + up_offset
                self.camera.up = transporter.up_direction
                
                look_ahead_point = transporter_pos + transporter.forward_direction * 10
                self.camera.lookAt = look_ahead_point - self.camera.position
            else:  # First-person view
                self.camera.position = transporter_pos + transporter.up_direction * 5
                self.camera.up = transporter.up_direction
                self.camera.lookAt = transporter.forward_direction * 10
            
            # Ensure lookAt vector is never zero
            if np.all(np.abs(self.camera.lookAt) < 1e-6):
                self.camera.lookAt = transporter.forward_direction
            
            # Update pirates
            player_forward = transporter.forward_direction
            for pirate in self.gameState["pirates"]:
                pirate.update(delta_time, transporter_pos, player_forward)
                
                # Check for collision with player
                distance = np.linalg.norm(pirate.position - transporter_pos)
                if distance < pirate.collision_radius:
                    self.screen = GameScreen.GAME_OVER
                    return
            
            # Handle laser firing
            current_time = time['currentTime']
            if inputs["F"] and self.gameState['transporter'].can_shoot(current_time):
                new_laser = self.gameState['transporter'].shoot(current_time)
                if new_laser:
                    self.gameState['lasers'].append(new_laser)
                    if new_laser.shader not in self.shaders:
                        self.shaders.append(new_laser.shader)
            
            # Update lasers and remove expired ones
            i = 0
            while i < len(self.gameState['lasers']):
                if self.gameState['lasers'][i].update(delta_time):
                    self.gameState['lasers'].pop(i)
                else:
                    i += 1

            # Update space stations orbits
            for station in self.gameState["spaceStations"]:
                station.update(delta_time)

            # Check for laser collisions
            for i in range(len(self.gameState["lasers"]) - 1, -1, -1):
                laser = self.gameState["lasers"][i]
                laser_removed = False
                
                # Check collisions with pirates
                for j in range(len(self.gameState["pirates"]) - 1, -1, -1):
                    if laser_removed:
                        break
                        
                    pirate = self.gameState["pirates"][j]
                    distance = np.linalg.norm(laser.position - pirate.position)
                    if distance < pirate.collision_radius:
                        self.gameState["pirates"].pop(j)
                        self.gameState["lasers"].pop(i)
                        laser_removed = True
                
                if laser_removed:
                    continue
                    
                # Check collisions with planets
                for planet in self.gameState["planets"]:
                    if laser_removed:
                        break
                        
                    distance = np.linalg.norm(laser.position - planet.position)
                    if distance < 100.0:  # Planet collision radius
                        self.gameState["lasers"].pop(i)
                        laser_removed = True

            # Check for win condition
            if "transporter" in self.gameState and "destination_station" in self.gameState:
                transporter_pos = self.gameState["transporter"].position
                dest_station_pos = self.gameState["destination_station"].position
                distance = np.linalg.norm(transporter_pos - dest_station_pos)
                
                # Show proximity message when getting close
                if distance < 100.0 and not hasattr(self, "proximity_alert"):
                    print("Approaching destination! Slow down for docking.")
                    self.proximity_alert = True
                
                # Docking range
                if distance < 50.0:
                    self.screen = GameScreen.WIN
            
    def DrawScene(self):
        if self.screen == GameScreen.GAME: 
            # Update all shaders
            for shader in self.shaders:
               self.camera.Update(shader)
    
            # Only draw the transporter in third-person view
            if self.gameState["transporter"].view == 1:
                self.gameState["transporter"].Draw()
    
            # Draw all game objects
            for laser in self.gameState["lasers"]:
                laser.Draw()
                
            for planet in self.gameState["planets"]:
                planet.Draw()
                
            for spaceStation in self.gameState["spaceStations"]:
                spaceStation.Draw()
                
            for pirate in self.gameState["pirates"]:
                pirate.Draw()
            
            # Draw crosshair in first-person view
            if self.gameState["transporter"].view == 2:
                self.DrawCrosshair()
                
            self.DrawMinimapArrow()
            self.DrawSpeedDisplay()

    def DrawSpeedDisplay(self):
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
        panel_width = gauge_radius * 2 + 60
        panel_height = gauge_radius * 2 + 60
        panel_x = 20
        panel_y = self.height - panel_height - 20-60
        
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
        labels = ["THR", "HI", "MAX", "SYS1", "SYS2"]
        label_color = imgui.get_color_u32_rgba(0.7, 0.7, 0.8, 0.8)
        
        for i, label in enumerate(labels):
            label_x = bulb_start_x + i * (bulb_spacing+5) - 20
            label_y = bulb_y + bulb_radius + 5
            draw_list.add_text(label_x, label_y, label_color, label)
        
        # Draw movement effects
        speed_ratio = current_speed / max_speed
        if speed_ratio > 0.01 or self.acceleration_effect_intensity > 0.01:
            self.DrawMovementEffect(draw_list, speed_ratio)
        
        imgui.render()
        self.gui.render(imgui.get_draw_data())

    def DrawMovementEffect(self, draw_list, speed_ratio):
        """Draw visual effects for movement and acceleration"""
        width, height = self.width, self.height
        
        # Draw acceleration effect overlay
        if self.acceleration_effect_intensity > 0.1:
            alpha = self.acceleration_effect_intensity * 0.4
            
            # Draw a gradient from edges to center
            center_x = width / 2
            center_y = height / 2
            outer_radius = max(width, height) * 0.7
            inner_radius = outer_radius * (1.0 - self.acceleration_effect_intensity * 0.5)
            
            num_segments = 60
            for i in range(num_segments):
                angle1 = 2 * np.pi * i / num_segments
                angle2 = 2 * np.pi * (i + 1) / num_segments
                
                x1_outer = center_x + np.cos(angle1) * outer_radius
                y1_outer = center_y + np.sin(angle1) * outer_radius
                x2_outer = center_x + np.cos(angle2) * outer_radius
                y2_outer = center_y + np.sin(angle2) * outer_radius
                
                x1_inner = center_x + np.cos(angle1) * inner_radius
                y1_inner = center_y + np.sin(angle1) * inner_radius
                x2_inner = center_x + np.cos(angle2) * inner_radius
                y2_inner = center_y + np.sin(angle2) * inner_radius
                
                draw_list.add_quad_filled(
                    x1_outer, y1_outer,
                    x2_outer, y2_outer,
                    x2_inner, y2_inner,
                    x1_inner, y1_inner,
                    imgui.get_color_u32_rgba(0.0, 0.0, 0.5, alpha * (1.0 - i/num_segments))
                )
        
        movement_intensity = max(speed_ratio * 0.6, self.acceleration_effect_intensity)
        
        base_num_lines = int(max(8, 25 * movement_intensity))
        num_lines = base_num_lines
        
        if num_lines > 0:
            if len(self.speed_lines) < num_lines:
                for _ in range(num_lines - len(self.speed_lines)):
                    x = random.randint(0, width)
                    y = random.randint(0, height)
                    length = random.randint(20, 100) * movement_intensity
                    angle = random.uniform(-0.3, 0.3)
                    self.speed_lines.append({
                        'x': x,
                        'y': y,
                        'length': length,
                        'angle': angle,
                        'alpha': random.uniform(0.3, 0.9)
                    })
            
            for i, line in enumerate(self.speed_lines):
                if i >= num_lines:
                    break
                
                dx = line['length'] * np.cos(line['angle'])
                dy = line['length'] * np.sin(line['angle'])
                
                if self.acceleration_effect_intensity > 0.1:
                    line_color = imgui.get_color_u32_rgba(
                        0.9, 0.9, 1.0, 
                        line['alpha'] * movement_intensity
                    )
                else:
                    line_color = imgui.get_color_u32_rgba(
                        0.7, 0.8, 1.0, 
                        line['alpha'] * movement_intensity * 0.8
                    )
                
                draw_list.add_line(
                    line['x'], line['y'],
                    line['x'] + dx, line['y'] + dy,
                    line_color, 1.5
                )
                
                move_speed = 0.05
                if self.acceleration_effect_intensity > 0.1:
                    move_speed = 0.08
                
                line['x'] -= dx * move_speed
                line['y'] -= dy * move_speed
                
                if line['x'] < 0 or line['x'] > width or line['y'] < 0 or line['y'] > height:
                    line['x'] = random.randint(0, width)
                    line['y'] = random.randint(0, height)
                    line['length'] = random.randint(20, 100) * movement_intensity
                    line['alpha'] = random.uniform(0.3, 0.9)
            
            while len(self.speed_lines) > num_lines:
                self.speed_lines.pop()

    def DrawCrosshair(self):
        """Draw a simple + crosshair in the center of the screen."""
        imgui.new_frame()
        
        center_x = self.width / 2
        center_y = self.height / 2
        
        size = 10.0
        thickness = 2.0
        color = (1.0, 0.2, 0.2, 1.0)
        
        draw_list = imgui.get_background_draw_list()
        
        draw_list.add_line(
            center_x - size, center_y,
            center_x + size, center_y,
            imgui.get_color_u32_rgba(*color), thickness
        )
        
        draw_list.add_line(
            center_x, center_y - size,
            center_x, center_y + size,
            imgui.get_color_u32_rgba(*color), thickness
        )
        
        imgui.render()
        self.gui.render(imgui.get_draw_data())                

    def DrawMinimapArrow(self):
        """Draw a 2D arrow pointing to the destination relative to player orientation."""
        if "destination_station" not in self.gameState or "transporter" not in self.gameState:
            return
        
        imgui.new_frame()
        
        transporter = self.gameState["transporter"]
        player_pos = transporter.position
        destination_pos = self.gameState["destination_station"].position
        
        forward_dir = transporter.forward_direction
        right_dir = transporter.right_direction
        up_dir = transporter.up_direction
        
        world_direction = destination_pos - player_pos
        distance = np.linalg.norm(world_direction)
        
        if distance < 10:
            imgui.render()
            self.gui.render(imgui.get_draw_data())
            return
        
        if distance > 0:
            world_direction = world_direction / distance
        
        local_forward = np.dot(world_direction, forward_dir)
        local_right = np.dot(world_direction, right_dir)
        local_up = np.dot(world_direction, up_dir)
        
        angle = np.arctan2(-local_right, local_forward)
        
        pos_x = self.width - 80
        pos_y = 80
        
        draw_list = imgui.get_background_draw_list()
        
        circle_radius = 50
        bg_color = imgui.get_color_u32_rgba(0.0, 0.0, 0.0, 0.5)
        draw_list.add_circle_filled(pos_x, pos_y, circle_radius, bg_color)
        border_color = imgui.get_color_u32_rgba(1.0, 1.0, 1.0, 0.7)
        draw_list.add_circle(pos_x, pos_y, circle_radius, border_color, 16, 1.5)
        
        forward_length = 15.0
        forward_color = imgui.get_color_u32_rgba(0.7, 0.7, 0.7, 0.6)
        draw_list.add_line(
            pos_x, pos_y,
            pos_x, pos_y - forward_length,
            forward_color, 1.0
        )
        draw_list.add_text(
            pos_x - 5, pos_y - forward_length - 12,
            forward_color, "F"
        )
        
        arrow_length = 35.0
        head_length = 15.0
        arrow_width = 8.0
        head_width = 18.0
        
        sin_angle = np.sin(angle)
        cos_angle = np.cos(angle)
        
        tip_x = pos_x + arrow_length * sin_angle
        tip_y = pos_y - arrow_length * cos_angle
        
        head_base_x = pos_x + (arrow_length - head_length) * sin_angle
        head_base_y = pos_y - (arrow_length - head_length) * cos_angle
        
        tail_x = pos_x + arrow_length/3 * sin_angle * -0.5
        tail_y = pos_y - arrow_length/3 * cos_angle * -0.5
        
        perp_x = cos_angle
        perp_y = sin_angle
        
        left_corner_x = head_base_x + head_width/2 * perp_x
        left_corner_y = head_base_y + head_width/2 * perp_y
        
        right_corner_x = head_base_x - head_width/2 * perp_x
        right_corner_y = head_base_y - head_width/2 * perp_y
        
        shaft_left_top_x = head_base_x + arrow_width/2 * perp_x
        shaft_left_top_y = head_base_y + arrow_width/2 * perp_y
        
        shaft_right_top_x = head_base_x - arrow_width/2 * perp_x
        shaft_right_top_y = head_base_y - arrow_width/2 * perp_y
        
        shaft_left_bottom_x = tail_x + arrow_width/2 * perp_x
        shaft_left_bottom_y = tail_y + arrow_width/2 * perp_y
        
        shaft_right_bottom_x = tail_x - arrow_width/2 * perp_x
        shaft_right_bottom_y = tail_y - arrow_width/2 * perp_y
        
        if local_forward > 0:
            g = min(1.0, 0.8 + 0.2 * local_forward)
            r = min(1.0, (1.0 - local_forward) + distance / 10000.0)
            b = 0.2
        else:
            b = min(1.0, 0.8 - 0.2 * local_forward)
            r = min(1.0, abs(local_forward) + distance / 10000.0)
            g = 0.2
        
        arrow_color = imgui.get_color_u32_rgba(r, g, b, 1.0)
        
        draw_list.add_triangle_filled(
            tip_x, tip_y,
            left_corner_x, left_corner_y,
            right_corner_x, right_corner_y,
            arrow_color
        )
        
        draw_list.add_quad_filled(
            shaft_left_top_x, shaft_left_top_y,
            shaft_right_top_x, shaft_right_top_y,
            shaft_right_bottom_x, shaft_right_bottom_y,
            shaft_left_bottom_x, shaft_left_bottom_y,
            arrow_color
        )
        
        outline_color = imgui.get_color_u32_rgba(1.0, 1.0, 1.0, 0.7)
        
        draw_list.add_triangle(
            tip_x, tip_y,
            left_corner_x, left_corner_y,
            right_corner_x, right_corner_y,
            outline_color, 1.0
        )
        
        draw_list.add_quad(
            shaft_left_top_x, shaft_left_top_y,
            shaft_right_top_x, shaft_right_top_y,
            shaft_right_bottom_x, shaft_right_bottom_y,
            shaft_left_bottom_x, shaft_left_bottom_y,
            outline_color, 1.0
        )
        
        direction_text = ""
        if abs(local_forward) > abs(local_right):
            if local_forward > 0:
                direction_text = "Forward"
            else:
                direction_text = "Behind"
        else:
            if local_right > 0:
                direction_text = "Left"
            else:
                direction_text = "Right"
        
        elevation_text = ""
        if abs(local_up) > 0.3:
            if local_up > 0:
                elevation_text = "Above"
            else:
                elevation_text = "Below"
        
        info_text = f"{int(distance)}u {direction_text}"
        if elevation_text:
            info_text += f" {elevation_text}"
        
        text_color = imgui.get_color_u32_rgba(1.0, 1.0, 1.0, 1.0)
        text_width = len(info_text) * 7
        draw_list.add_text(pos_x - text_width/2, pos_y + circle_radius + 5, text_color, info_text)
        
        imgui.render()
        self.gui.render(imgui.get_draw_data())


