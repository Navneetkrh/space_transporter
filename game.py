import imgui
import numpy as np
from utils.graphics import Object, Camera, Shader
import sys
from enum import Enum, auto
import random
from assets.objects.objects import Pirate, Transporter,Planet,SpaceStation

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
            
         
            self.gameState["transporter"] = Transporter()
            # Add its shader to the shaders list
            self.shaders.append(self.gameState["transporter"].shader)
            # Set initial position slightly away from origin to see it better
            # self.gameState["transporter"].set_position(np.array([20,0, -10], dtype=np.float32))
          
            
            # Initialize empty lists for other game objects
            self.gameState["planets"] = []
            self.gameState["spaceStations"] = []
            self.gameState["pirates"] = []
            self.gameState["lasers"] = []
            ############################################################################
            # Initialize Planets and space stations (Randomly place n planets and n spacestations within world bounds)
            self.n_planets = 30 # for example
            # Add to Game.InitScene method after initializing empty lists
            # Initialize Planets and space stations
            # Create random planets
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
                        
            ############################################################################
            # Initialize transporter (Randomly choose start and end planet, and initialize transporter at start planet)
            
            ############################################################################
            # Initialize Pirates (Spawn at random locations within world bounds)
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
            ############################################################################
            # Initialize minimap arrow (Need to write orthographic projection shader for it)
            
            ############################################################################

    def ProcessFrame(self, inputs, time):
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
            imgui.begin("YOU WON", False, imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_RESIZE)
            
            button_w, button_h = 150, 40
            imgui.set_cursor_pos_x((window_w - button_w) / 2)
            if imgui.button("New Game", button_w, button_h):
                self.screen = GameScreen.GAME
                self.InitScene()
                
            imgui.end()
            imgui.render()
            self.gui.render(imgui.get_draw_data())

        elif self.screen == GameScreen.GAME_OVER:
            window_w, window_h = 400, 200
            x_pos = (self.width - window_w) / 2
            y_pos = (self.height - window_h) / 2
            
            imgui.new_frame()
            imgui.set_next_window_position(x_pos, y_pos)
            imgui.set_next_window_size(window_w, window_h)
            imgui.begin("GAME OVER", False, imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_RESIZE)
            
            button_w, button_h = 150, 40
            imgui.set_cursor_pos_x((window_w - button_w) / 2)
            if imgui.button("New Game", button_w, button_h):
                self.screen = GameScreen.GAME
                self.InitScene()
                
            imgui.end()
            imgui.render()
            self.gui.render(imgui.get_draw_data())

    def UpdateScene(self, inputs, time):
        delta_time = time['deltaTime'];
        if self.screen == GameScreen.GAME:
            # Update camera to follow transporter's rotation as well
            transporter = self.gameState["transporter"]
            transporter_pos = transporter.position

            # Calculate camera offset based on transporter's orientation vectors
            behind_offset = -transporter.forward_direction * 50  # 50 units behind
            up_offset = transporter.up_direction * 20  # 20 units above
            
            # Set camera position using the transformed offset
            self.camera.position = transporter_pos + behind_offset + up_offset
            self.camera.up = transporter.up_direction
            
            # Make camera look at a point slightly ahead of the transporter
            look_ahead_point = transporter_pos + transporter.forward_direction * 10
            self.camera.lookAt = look_ahead_point - self.camera.position
            
            # Ensure lookAt vector is never zero
            if np.all(np.abs(self.camera.lookAt) < 1e-6):
                self.camera.lookAt = transporter.forward_direction
            
            # Update transporter
            self.gameState['transporter'].update(inputs, delta_time)

            # update pirates
            for pirate in self.gameState["pirates"]:
                pirate.update(delta_time, transporter_pos)
            

            
            ############################################################################
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

   

            # Update spacestations (Update velocity and position to revolve around respective planet)
            # Update space stations (orbit around planets)
            for station in self.gameState["spaceStations"]:
                station.update(delta_time)

            ############################################################################
            # Check for collision between lasers and other objects (pirates, planets, etc.)

            for laser in self.gameState["lasers"]:
                # Check for collision with pirates
                for pirate in self.gameState["pirates"]:
                    # check distance between laser and pirate
                    distance = np.linalg.norm(laser.position - pirate.position)
                    if distance < 20.0:  # Collision radius
                        # Destroy pirate
                        self.gameState["pirates"].remove(pirate)
                        # Remove laser
                        self.gameState["lasers"].remove(laser)
                        break
                
                # Check for collision with planets
                for planet in self.gameState["planets"]:
                    distance = np.linalg.norm(laser.position - planet.position)
                    if distance < 10.0:
                        # Remove laser
                        self.gameState["lasers"].remove(laser)
                        break

            
            # This would be implemented here
            ############################################################################

            if "transporter" in self.gameState and "destination_station" in self.gameState:
                transporter_pos = self.gameState["transporter"].position
                dest_station_pos = self.gameState["destination_station"].position
                
                # Simple distance-based collision detection
                distance = np.linalg.norm(transporter_pos - dest_station_pos)
                if distance < 15.0:  # Collision radius
                    # Player won!
                    self.screen = GameScreen.WIN
    
    def DrawScene(self):
        if self.screen == GameScreen.GAME: 
            # Example draw statements
            for i, shader in enumerate(self.shaders):
               self.camera.Update(shader)
    
            self.gameState["transporter"].Draw()
            # self.gameState["stars"].Draw()
            # self.gameState["arrow"].Draw()
    
            # if self.gameState["transporter"].properties["view"] == 2: # Conditionally draw crosshair
            #     self.gameState["crosshair"].Draw()

            # print("lasers", self.gameState["lasers"])
            for laser in self.gameState["lasers"]:
                laser.Draw()
            for planet in self.gameState["planets"]:
                planet.Draw()
            for spaceStation in self.gameState["spaceStations"]:
                spaceStation.Draw()
            for pirate in self.gameState["pirates"]:
                pirate.Draw()
            ######################################################
            pass

