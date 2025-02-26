import imgui
import numpy as np
from utils.graphics import Object, Camera, Shader
import sys

class Game:
    def __init__(self, height, width, gui):
        self.gui = gui
        self.height = height
        self.width = width
        self.screen = 0

    def InitScene(self):
        if self.screen == 1:
            ############################################################################
            # Define world state
            self.camera = Camera(self.height, self.width)
            self.shaders = []
            self.gameState = {} # Can define keys as 'transporter', 'pirates', etc. Their values being Object() or list of Object()
            ############################################################################
            # Define world boundaries
            self.worldMin = np.array([-5000, -5000, -5000], dtype=np.float32)
            self.worldMax = np.array([5000, 5000, 5000], dtype=np.float32)
            ############################################################################
            # Initialize Planets and space stations (Randomly place n planets and n spacestations within world bounds)
            self.n_planets = 30 # for example
            
            ############################################################################
            # Initialize transporter (Randomly choose start and end planet, and initialize transporter at start planet)


            ############################################################################
            # Initialize Pirates (Spawn at random locations within world bounds)
            self.n_pirates = 20 # for example
    

            ############################################################################
            # Initialize minimap arrow (Need to write orthographic projection shader for it)


            ############################################################################

    def ProcessFrame(self, inputs, time):
        self.UpdateScene(inputs, time)
        self.DrawScene()
        self.DrawText()

    def DrawText(self):
        if self.screen == 0:  # Example start screen
            window_w, window_h = 400, 200  # Set the window size
            x_pos = (self.width - window_w) / 2
            y_pos = (self.height - window_h) / 2

            imgui.new_frame()
            # Centered window
            imgui.set_next_window_position(x_pos, y_pos)
            imgui.set_next_window_size(window_w, window_h)
            imgui.begin("Main Menu", False, imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_RESIZE)

            # Calculate button dimensions
            button_w, button_h = 150, 40  # Button width and height
            # Center the button horizontally
            imgui.set_cursor_pos_x((window_w - button_w) / 2)
            if imgui.button("New g Game", button_w, button_h):
                # Code to start a new game goes here
                print("New Game button pressed")

            # Add some vertical spacing between buttons (if needed)
            imgui.spacing()

            # Center the exit button similarly
            imgui.set_cursor_pos_x((window_w - button_w) / 2)
            if imgui.button("Exit", button_w, button_h):
                # Code to exit the game goes here
                print("Exit button pressed")

            imgui.end()

            imgui.render()
            self.gui.render(imgui.get_draw_data())


        if self.screen == 2:
            # YOU WON Screen
            window_w, window_h = 400, 200  # Set the window size
            x_pos = (self.width - window_w) / 2
            y_pos = (self.height - window_h) / 2
            imgui.new_frame()
            # Centered window
            imgui.set_next_window_position(x_pos, y_pos)
            imgui.set_next_window_size(window_w, window_h)
            imgui.begin("YOU WON", False, imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_RESIZE)
            # Center text horizontally
            imgui.set_cursor_pos_x((window_w - imgui.calc_text_size("Press 1: New Game")[0]) / 2)
            imgui.text("Press 1: New Game")
            imgui.end()
            imgui.render()
            self.gui.render(imgui.get_draw_data())

        if self.screen == 3:
            # GAME OVER Screen
            window_w, window_h = 400, 200  # Set the window size
            x_pos = (self.width - window_w) / 2
            y_pos = (self.height - window_h) / 2
            imgui.new_frame()
            # Centered window
            imgui.set_next_window_position(x_pos, y_pos)
            imgui.set_next_window_size(window_w, window_h)
            imgui.begin("GAME OVER", False, imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_RESIZE)
            # Center text horizontally
            imgui.set_cursor_pos_x((window_w - imgui.calc_text_size("Press 1: New Game")[0]) / 2)
            imgui.text("Press 1: New Game")
            imgui.end()
            imgui.render()
            self.gui.render(imgui.get_draw_data())

        
    def UpdateScene(self, inputs, time):
        if self.screen == 0: # Example start screen
            if inputs["1"]:
                self.screen = 1
                self.InitScene()
            elif inputs["2"]:
                # exit
                sys.exit()
        if self.screen == 2: # YOU WON
            pass
        if self.screen == 3: # GAME OVER
            pass
        
        if self.screen == 1: # Game screen
            ############################################################################
            # Manage inputs 
           

            ############################################################################
            # Update transporter (Update velocity, position, and check for collisions)
           

            ############################################################################
            # Update spacestations (Update velocity and position to revolve around respective planet)
            

            ############################################################################
            # Update Minimap Arrow: (Set direction based on transporter velocity direction and target direction)
            

            ############################################################################
            # Update Lasers (Update position of any currently shot lasers, make sure to despawn them if they go too far to save computation)
           
            
            ############################################################################
            # Update Pirates (Write logic to update their velocity based on transporter position, and check for collision with laser or transporter)
            

            ############################################################################
            # Update Camera (Check for view (3rd person or 1st person) and set position and LookAt accordingly)
            

            ############################################################################
            pass
    
    def DrawScene(self):
        if self.screen == 1: 
            ######################################################
            # Example draw statements
            
            for i, shader in enumerate(self.shaders):
               self.camera.Update(shader)

            self.gameState["transporter"].Draw()
            self.gameState["stars"].Draw()
            self.gameState["arrow"].Draw()

            if self.gameState["transporter"].properties["view"] == 2: # Conditionally draw crosshair
                self.gameState["crosshair"].Draw()

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

