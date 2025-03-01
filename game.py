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
            # Define world state
            self.camera = Camera(self.height, self.width)
            self.shaders = []
            self.gameState = {}
            
            # Define world boundaries
            self.worldMin = np.array([-5000, -5000, -5000], dtype=np.float32)
            self.worldMax = np.array([5000, 5000, 5000], dtype=np.float32)
            
            # Initialize transporter
            self.gameState["transporter"] = Transporter()
            self.shaders.append(self.gameState["transporter"].shader)
            
            # Initialize empty lists for other game objects
            self.gameState["planets"] = []
            self.gameState["spaceStations"] = []
            self.gameState["pirates"] = []
            self.gameState["lasers"] = []
            
            # Create random planets
            self.n_planets = 30
            for i in range(self.n_planets):
                planet = Planet()
                # Set random position within world bounds
                random_pos = np.array([
                    random.uniform(self.worldMin[0], self.worldMax[0]),
                    random.uniform(self.worldMin[1], self.worldMax[1]),
                    random.uniform(self.worldMin[2], self.worldMax[2])
                ], dtype=np.float32)
                planet.set_position(random_pos)
                
                # Random color for each planet
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
                # Calculate initial orbit position (offset from planet)
                orbit_radius = 150.0  # Distance from planet center
                orbit_angle = random.uniform(0, 2 * np.pi)  # Random initial angle
                station_pos = random_pos + np.array([
                    orbit_radius * np.cos(orbit_angle),
                    0,  # Keep on same y-level as planet
                    orbit_radius * np.sin(orbit_angle)
                ], dtype=np.float32)
                station.set_position(station_pos)
                # Store reference to parent planet for orbit calculations
                station.parent_planet = planet
                station.orbit_angle = orbit_angle
                station.orbit_radius = orbit_radius
                station.orbit_speed = random.uniform(0.2, 0.5)  # Radians per second
                self.gameState["spaceStations"].append(station)
                self.shaders.append(station.shader)

            # Randomly choose start and destination planets/stations
            if len(self.gameState["spaceStations"]) >= 2:
                # Select two different stations
                start_idx = random.randrange(0, len(self.gameState["spaceStations"]))
                dest_idx = start_idx
                while dest_idx == start_idx:
                    dest_idx = random.randrange(0, len(self.gameState["spaceStations"]))
                
                # Set start and destination
                self.gameState["start_station"] = self.gameState["spaceStations"][start_idx]
                self.gameState["destination_station"] = self.gameState["spaceStations"][dest_idx]
                
                # Set transporter at start station
                start_pos = self.gameState["start_station"].position.copy()
                # Offset slightly to avoid collision
                start_pos += np.array([0, 20, 0], dtype=np.float32)
                self.gameState["transporter"].set_position(start_pos)
                self.gameState["transporter"].start_planet = self.gameState["start_station"].parent_planet
                self.gameState["transporter"].target_planet = self.gameState["destination_station"].parent_planet
                
                # Make the destination planet glow and more distinct
                dest_planet = self.gameState["destination_station"].parent_planet
                
                # Make destination planet larger
                dest_planet.graphics_obj.properties['scale'] *= 1.2  # 20% larger
                
                # Create new shader instance for the destination planet
                dest_planet.shader = Shader(destination_shader["vertex_shader"], 
                                         destination_shader["fragment_shader"])
                dest_planet.graphics_obj.shader = dest_planet.shader
                
                # Update shader list
                self.shaders.append(dest_planet.shader)
                
                # Set a more vibrant gold color for the destination planet
                dest_planet.set_color(np.array([1.0, 0.9, 0.3, 1.0]))  # Brighter golden color
                
            # Initialize Pirates
            self.n_pirates = 10  # Number of pirates
            for i in range(self.n_pirates):
                pirate = Pirate()
                
                # Generate random position (ensure it's not too close to the player start)
                while True:
                    random_pos = np.array([
                        random.uniform(self.worldMin[0], self.worldMax[0]),
                        random.uniform(self.worldMin[1], self.worldMax[1]),
                        random.uniform(self.worldMin[2], self.worldMax[2])
                    ], dtype=np.float32)
                    
                    # Check distance from start station
                    if "start_station" in self.gameState:
                        distance = np.linalg.norm(random_pos - self.gameState["start_station"].position)
                        if distance > 500.0:  # Ensure pirates start at a safe distance
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
                self.key_cooldown = 0.2  # Set cooldown to prevent multiple toggles
    
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
            
            # Add congratulatory message
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
            
            # Fix parameter order for text_colored (text first, then colors)
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
            
            # Update camera based on view mode (first vs third person)
            if transporter.view == 1:  # Third-person view
                # Calculate camera offset based on transporter's orientation vectors
                behind_offset = -transporter.forward_direction * 50  # 50 units behind
                up_offset = transporter.up_direction * 20  # 20 units above
                
                # Set camera position using the transformed offset
                self.camera.position = transporter_pos + behind_offset + up_offset
                self.camera.up = transporter.up_direction
                
                # Make camera look at a point slightly ahead of the transporter
                look_ahead_point = transporter_pos + transporter.forward_direction * 10
                self.camera.lookAt = look_ahead_point - self.camera.position
            else:  # First-person view
                # Set camera position at the transporter's position
                self.camera.position = transporter_pos + transporter.up_direction * 5  # Slightly above for better view
                self.camera.up = transporter.up_direction
                
                # Set lookAt to point in the forward direction
                self.camera.lookAt = transporter.forward_direction * 10
            
            # Ensure lookAt vector is never zero
            if np.all(np.abs(self.camera.lookAt) < 1e-6):
                self.camera.lookAt = transporter.forward_direction
            
            # Get transporter position and forward vector for pirates
            player_forward = transporter.forward_direction

            # Update pirates with player's forward vector
            for pirate in self.gameState["pirates"]:
                pirate.update(delta_time, transporter_pos, player_forward)
                
                # Check for collision with player
                distance = np.linalg.norm(pirate.position - transporter_pos)
                if distance < pirate.collision_radius:  # Use pirate's collision radius
                    # Game over if pirate hits player
                    print("Pirate collision detected!")
                    self.screen = GameScreen.GAME_OVER
                    return
            
            # Handle laser firing
            current_time = time['currentTime']
            if inputs["F"] and self.gameState['transporter'].can_shoot(current_time):
                # Create a new laser
                new_laser = self.gameState['transporter'].shoot(current_time)
                if new_laser:
                    self.gameState['lasers'].append(new_laser)
                    # Add the laser's shader to our shader list if it's not already there
                    if new_laser.shader not in self.shaders:
                        self.shaders.append(new_laser.shader)
            
            # Update all lasers and remove expired ones
            i = 0
            while i < len(self.gameState['lasers']):
                # Update returns True if the laser should be removed
                if self.gameState['lasers'][i].update(delta_time):
                    # Remove expired laser
                    self.gameState['lasers'].pop(i)
                else:
                    i += 1

            # Update space stations (orbit around planets)
            for station in self.gameState["spaceStations"]:
                station.update(delta_time)

            # Check for collision between lasers and other objects
            for i in range(len(self.gameState["lasers"]) - 1, -1, -1):
                laser = self.gameState["lasers"][i]
                laser_removed = False
                
                # Check for collision with pirates
                for j in range(len(self.gameState["pirates"]) - 1, -1, -1):
                    if laser_removed:
                        break
                        
                    pirate = self.gameState["pirates"][j]
                    # Check distance between laser and pirate using pirate's collision radius
                    distance = np.linalg.norm(laser.position - pirate.position)
                    if distance < pirate.collision_radius:  # Use the pirate's collision radius
                        # Destroy pirate
                        self.gameState["pirates"].pop(j)
                        # Remove laser
                        self.gameState["lasers"].pop(i)
                        laser_removed = True
                
                if laser_removed:
                    continue
                    
                # Check for collision with planets
                for planet in self.gameState["planets"]:
                    if laser_removed:
                        break
                        
                    distance = np.linalg.norm(laser.position - planet.position)
                    if distance < 100.0:  # Planet collision radius
                        # Remove laser
                        self.gameState["lasers"].pop(i)
                        laser_removed = True

            # Check for win condition - arrival at destination
            if "transporter" in self.gameState and "destination_station" in self.gameState:
                transporter_pos = self.gameState["transporter"].position
                dest_station_pos = self.gameState["destination_station"].position
                
                # Calculate distance to destination
                distance = np.linalg.norm(transporter_pos - dest_station_pos)
                
                # Show proximity message when getting close
                if distance < 100.0 and not hasattr(self, "proximity_alert"):
                    print("Approaching destination! Slow down for docking.")
                    self.proximity_alert = True
                
                # Larger collision radius for easier docking
                if distance < 50.0:  # Increased from 15.0 to make it easier
                    # Player won! Show victory screen
                    self.screen = GameScreen.WIN
            
    def DrawScene(self):
        if self.screen == GameScreen.GAME: 
            # Update all shaders
            for shader in self.shaders:
               self.camera.Update(shader)
    
            # Only draw the transporter in third-person view
            if self.gameState["transporter"].view == 1:  # Third-person view
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
            
            # Draw a simple crosshair in first-person view
            if self.gameState["transporter"].view == 2:  # First-person view
                self.DrawCrosshair()
                
            # Draw 2D minimap arrow
            self.DrawMinimapArrow()

    def DrawCrosshair(self):
        """Draw a simple + crosshair in the center of the screen."""
        imgui.new_frame()
        
        # Calculate center position
        center_x = self.width / 2
        center_y = self.height / 2
        
        # Set crosshair size and color
        size = 10.0
        thickness = 2.0
        color = (1.0, 0.2, 0.2, 1.0)  # Red crosshair
        
        # Create a crosshair using ImGui drawing commands
        draw_list = imgui.get_background_draw_list()
        
        # Draw horizontal line
        draw_list.add_line(
            center_x - size, center_y,
            center_x + size, center_y,
            imgui.get_color_u32_rgba(*color), thickness
        )
        
        # Draw vertical line
        draw_list.add_line(
            center_x, center_y - size,
            center_x, center_y + size,
            imgui.get_color_u32_rgba(*color), thickness
        )
        
        # Render ImGui (crosshair only)
        imgui.render()
        self.gui.render(imgui.get_draw_data())

    def DrawMinimapArrow(self):
        """Draw a 2D arrow pointing to the destination."""
        if "destination_station" not in self.gameState or "transporter" not in self.gameState:
            return
            
        imgui.new_frame()
        
        # Get positions
        player_pos = self.gameState["transporter"].position
        destination_pos = self.gameState["destination_station"].position
        
        # Calculate direction to destination
        direction = destination_pos - player_pos
        distance = np.linalg.norm(direction)
        
        # Skip if we're very close
        if distance < 10:
            imgui.render()
            self.gui.render(imgui.get_draw_data())
            return
        
        # Normalize direction
        if distance > 0:
            direction = direction / distance
        
        # Calculate angle to destination (in screen space)
        # Convert from world to screen direction
        angle = np.arctan2(direction[0], direction[2])  # Using X,Z plane for top-down view
        
        # Create arrow parameters
        arrow_size = 100.0  # Base size
        # Scale based on distance (closer = smaller)
        size_factor = min(100, 50.0 / distance) if distance > 0 else 1.0
        arrow_size *= size_factor
        
        # Position on screen (fixed position in top-right corner)
        pos_x = self.width - 70
        pos_y = 70
        
        # Draw the background circle
        draw_list = imgui.get_background_draw_list()
        
        # Draw background circle
        circle_radius = 40
        bg_color = imgui.get_color_u32_rgba(1, 1, 1, 0.6)  # Semi-transparent black
        draw_list.add_circle(pos_x, pos_y, circle_radius, bg_color, 16, 2.0)
        
        # Calculate arrow points
        # Convert polar to cartesian coordinates
        tip_length = 25.0 * size_factor
        half_width = 10.0 * size_factor
        shaft_width = 5.0 * size_factor
        
        # Arrow tip position
        tip_x = pos_x + np.sin(angle) * tip_length
        tip_y = pos_y + np.cos(angle) * tip_length
        
        # Arrow base positions (perpendicular to direction)
        perp_angle = angle + np.pi/2
        perp_x = np.sin(perp_angle)
        perp_y = np.cos(perp_angle)
        
        # Arrow head vertices
        left_x = tip_x - half_width * perp_x
        left_y = tip_y - half_width * perp_y
        
        right_x = tip_x + half_width * perp_x
        right_y = tip_y + half_width * perp_y
        
        # Arrow base (top of shaft)
        base_distance = 15.0 * size_factor
        base_x = pos_x + np.sin(angle) * base_distance
        base_y = pos_y + np.cos(angle) * base_distance
        
        # Shaft points
        shaft_left_x = base_x - shaft_width * perp_x
        shaft_left_y = base_y - shaft_width * perp_y
        
        shaft_right_x = base_x + shaft_width * perp_x
        shaft_right_y = base_y + shaft_width * perp_y
        
        # Calculate the tail position (opposite of direction)
        tail_x = pos_x - np.sin(angle) * shaft_width
        tail_y = pos_y - np.cos(angle) * shaft_width
        
        # Arrow color based on distance
        # Red when far, green when close
        r = min(1.0, distance / 5000.0)  # Red component decreases with proximity
        g = 1.0 - (r * 0.7)  # Green component increases with proximity
        arrow_color = imgui.get_color_u32_rgba(r, g, 0.2, 1.0)
        
        # Draw the arrow head (triangle)
        draw_list.add_triangle(tip_x, tip_y, left_x, left_y, right_x, right_y, arrow_color, 2.0)
        
        # Draw the arrow shaft (rectangle)
        draw_list.add_quad(
            shaft_left_x, shaft_left_y,
            shaft_right_x, shaft_right_y,
            tail_x + shaft_width * perp_x, tail_y + shaft_width * perp_y,
            tail_x - shaft_width * perp_x, tail_y - shaft_width * perp_y,
            arrow_color, 2.0
        )
        
        # Optional: Add distance indicator text
        distance_text = f"{int(distance)}u"
        text_color = imgui.get_color_u32_rgba(1, 1, 1, 1)
        draw_list.add_text(pos_x - 15, pos_y + circle_radius + 5, text_color, distance_text)
        
        # Render ImGui
        imgui.render()
        self.gui.render(imgui.get_draw_data())



