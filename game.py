import imgui
import numpy as np
from utils.graphics import Object, Camera, Shader
import sys
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
                
                
                station = SpaceStation()
                
                orbit_radius = 150.0  
                orbit_angle = random.uniform(0, 2 * np.pi)  
                station_pos = random_pos + np.array([
                    orbit_radius * np.cos(orbit_angle),
                    0,  
                    orbit_radius * np.sin(orbit_angle)
                ], dtype=np.float32)
                station.set_position(station_pos)
                
                station.parent_planet = planet
                station.orbit_angle = orbit_angle
                station.orbit_radius = orbit_radius
                station.orbit_speed = random.uniform(0.2, 0.5)  
                self.gameState["spaceStations"].append(station)
                self.shaders.append(station.shader)

            
            if len(self.gameState["spaceStations"]) >= 2:
                
                start_idx = random.randrange(0, len(self.gameState["spaceStations"]))
                dest_idx = start_idx
                while dest_idx == start_idx:
                    dest_idx = random.randrange(0, len(self.gameState["spaceStations"]))
                
                
                self.gameState["start_station"] = self.gameState["spaceStations"][start_idx]
                self.gameState["destination_station"] = self.gameState["spaceStations"][dest_idx]
                
                
                start_pos = self.gameState["start_station"].position.copy()
                
                start_pos += np.array([0, 20, 0], dtype=np.float32)
                self.gameState["transporter"].set_position(start_pos)
                self.gameState["transporter"].start_planet = self.gameState["start_station"].parent_planet
                self.gameState["transporter"].target_planet = self.gameState["destination_station"].parent_planet
                
                
                dest_planet = self.gameState["destination_station"].parent_planet
                
                
                dest_planet.graphics_obj.properties['scale'] *= 1.2  
                
                
                dest_planet.shader = Shader(destination_shader["vertex_shader"], 
                                         destination_shader["fragment_shader"])
                dest_planet.graphics_obj.shader = dest_planet.shader
                
                
                self.shaders.append(dest_planet.shader)
                
                
                dest_planet.set_color(np.array([1.0, 0.9, 0.3, 1.0]))  
                
            
            self.n_pirates = 10  
            for i in range(self.n_pirates):
                pirate = Pirate()
                
                
                while True:
                    random_pos = np.array([
                        random.uniform(self.worldMin[0], self.worldMax[0]),
                        random.uniform(self.worldMin[1], self.worldMax[1]),
                        random.uniform(self.worldMin[2], self.worldMax[2])
                    ], dtype=np.float32)
                    
                    
                    if "start_station" in self.gameState:
                        distance = np.linalg.norm(random_pos - self.gameState["start_station"].position)
                        if distance > 500.0:  
                            break
                    else:
                        break
                
                pirate.set_position(random_pos)
                self.gameState["pirates"].append(pirate)
                self.shaders.append(pirate.shader)

    def ProcessFrame(self, inputs, time):
        
        if (inputs["R_CLICK"] or inputs["1"]) and not hasattr(self, "view_cooldown"):
            if self.screen == GameScreen.GAME and "transporter" in self.gameState:
                self.gameState["transporter"].toggle_view()
                self.view_cooldown = 0.2  
    
        if hasattr(self, "view_cooldown"):
            self.view_cooldown -= time["deltaTime"]
            if self.view_cooldown <= 0:
                delattr(self, "view_cooldown")
                
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
            
            transporter = self.gameState["transporter"]
            transporter.update(inputs, delta_time)
            transporter_pos = transporter.position
            
            
            if transporter.view == 1:  
                
                behind_offset = -transporter.forward_direction * 50  
                up_offset = transporter.up_direction * 20  
                
                
                self.camera.position = transporter_pos + behind_offset + up_offset
                self.camera.up = transporter.up_direction
                
                
                look_ahead_point = transporter_pos + transporter.forward_direction * 10
                self.camera.lookAt = look_ahead_point - self.camera.position
            else:  
                
                self.camera.position = transporter_pos + transporter.up_direction * 5  
                self.camera.up = transporter.up_direction
                
                
                self.camera.lookAt = transporter.forward_direction * 10
            
            
            if np.all(np.abs(self.camera.lookAt) < 1e-6):
                self.camera.lookAt = transporter.forward_direction
            
            
            player_forward = transporter.forward_direction

            
            for pirate in self.gameState["pirates"]:
                pirate.update(delta_time, transporter_pos, player_forward)
                
                
                distance = np.linalg.norm(pirate.position - transporter_pos)
                if distance < pirate.collision_radius:  
                    
                    print("Pirate collision detected!")
                    self.screen = GameScreen.GAME_OVER
                    return
            
            
            current_time = time['currentTime']
            if (inputs["L_CLICK"] or inputs["F"]) and self.gameState['transporter'].can_shoot(current_time):
                
                new_laser = self.gameState['transporter'].shoot(current_time)
                if new_laser:
                    self.gameState['lasers'].append(new_laser)
                    
                    if new_laser.shader not in self.shaders:
                        self.shaders.append(new_laser.shader)
            
            
            i = 0
            while i < len(self.gameState['lasers']):
                
                if self.gameState['lasers'][i].update(delta_time):
                    
                    self.gameState['lasers'].pop(i)
                else:
                    i += 1

            
            for station in self.gameState["spaceStations"]:
                station.update(delta_time)

            
            for i in range(len(self.gameState["lasers"]) - 1, -1, -1):
                laser = self.gameState["lasers"][i]
                laser_removed = False
                
                
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
                    
                
                for planet in self.gameState["planets"]:
                    if laser_removed:
                        break
                        
                    distance = np.linalg.norm(laser.position - planet.position)
                    if distance < 100.0:  
                        
                        self.gameState["lasers"].pop(i)
                        laser_removed = True

            
            if "transporter" in self.gameState and "destination_station" in self.gameState:
                transporter_pos = self.gameState["transporter"].position
                dest_station_pos = self.gameState["destination_station"].position
                
                
                distance = np.linalg.norm(transporter_pos - dest_station_pos)
                
                
                if distance < 100.0 and not hasattr(self, "proximity_alert"):
                    print("Approaching destination! Slow down for docking.")
                    self.proximity_alert = True
                
                
                if distance < 50.0:  
                    
                    self.screen = GameScreen.WIN
            
    def DrawScene(self):
        if self.screen == GameScreen.GAME: 
            
            for shader in self.shaders:
               self.camera.Update(shader)
    
            
            if self.gameState["transporter"].view == 1:  
                self.gameState["transporter"].Draw()
    
            
            for laser in self.gameState["lasers"]:
                laser.Draw()
                
            for planet in self.gameState["planets"]:
                planet.Draw()
                
            for spaceStation in self.gameState["spaceStations"]:
                spaceStation.Draw()
                
            for pirate in self.gameState["pirates"]:
                pirate.Draw()
            
            
            if self.gameState["transporter"].view == 2:  
                self.DrawCrosshair()
                
            
            self.DrawMinimapArrow()

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



