import glfw
from OpenGL.GL import *
import imgui
from imgui.integrations.glfw import GlfwRenderer

class Window:
    def __init__(self):

        # Initialize glfw
        glfw.init()
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
        
        # Get the primary monitor for fullscreen
        monitor = glfw.get_primary_monitor()

        # Get the monitor's video mode (resolution, refresh rate)
        mode = glfw.get_video_mode(monitor)

        # Create a window using glfw
        self.windowHeight = mode.size.height
        self.windowWidth = mode.size.width

        self.window = glfw.create_window(self.windowWidth, self.windowWidth, "Space Heist", None, None)
        # Pass 2nd last parameter as 'monitor' instead of None for fullscreen experience

        if not self.window:
            glfw.terminate()
            print("Glfw window can't be created")
            exit()

        # Set initial position on the screen and activate it
        glfw.set_window_pos(self.window, 0, 0) 
        glfw.make_context_current(self.window)
        
        # Initialize ImGUI
        imgui.create_context()
        self.impl = GlfwRenderer(self.window)

        # Enable Depth and blending
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS) 


        # Set the viewport (Specifies which area to map the opengl co-ordinate system to)        
        glViewport(0, 0, self.windowWidth, self.windowHeight)

        # Delta time
        self.prevTime = glfw.get_time()

    def Close(self):
        self.impl.shutdown()
        glfw.terminate()
    
    def IsOpen(self):
        return not glfw.window_should_close(self.window)

    def StartFrame(self, c0, c1, c2, c3):
        currentTime = glfw.get_time()
        deltaTime = currentTime - self.prevTime
        self.prevTime = currentTime
        time = {"currentTime" : currentTime, "deltaTime" : deltaTime}

        glfw.poll_events()
        
        inputs = {
            "1":False,
            "W":False,
            "S":False,
            "A":False,
            "D":False,
            "Q":False,
            "E":False,
            "SPACE":False,
            "L_SHIFT":False,
            "R_CLICK":False,
            "L_CLICK":False,
            "mouseDelta": [0.0,0.0], # Get mouse offset from center per frame
            "ESCAPE":False,
            "2":False,
            "F":False,
            }
        
        if glfw.get_key(self.window, glfw.KEY_1) == glfw.PRESS:
            inputs["1"] = True
        if glfw.get_key(self.window, glfw.KEY_2) == glfw.PRESS:
            inputs["2"] = True
        if glfw.get_key(self.window, glfw.KEY_W) == glfw.PRESS:
            inputs["W"] = True
        if glfw.get_key(self.window, glfw.KEY_A) == glfw.PRESS:
            inputs["A"] = True
        if glfw.get_key(self.window, glfw.KEY_S) == glfw.PRESS:
            inputs["S"] = True
        if glfw.get_key(self.window, glfw.KEY_D) == glfw.PRESS:
            inputs["D"] = True
        if glfw.get_key(self.window, glfw.KEY_Q) == glfw.PRESS:
            inputs["Q"] = True
        if glfw.get_key(self.window, glfw.KEY_E) == glfw.PRESS:
            inputs["E"] = True
        if glfw.get_key(self.window, glfw.KEY_SPACE) == glfw.PRESS:
            inputs["SPACE"] = True
        if glfw.get_key(self.window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS:
            inputs["L_SHIFT"] = True
        if glfw.get_mouse_button(self.window, glfw.MOUSE_BUTTON_RIGHT) == glfw.PRESS:
            inputs["R_CLICK"] = True
        if glfw.get_mouse_button(self.window, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS:
            inputs["L_CLICK"] = True
        if glfw.get_key(self.window, glfw.KEY_ESCAPE) == glfw.PRESS:
            inputs["ESCAPE"] = True
        if glfw.get_key(self.window, glfw.KEY_F) == glfw.PRESS:
            inputs["F"] = True

        xpos, ypos = glfw.get_cursor_pos(self.window)
        inputs["mouseDelta"] = [xpos - self.windowWidth/2, ypos - self.windowHeight/2]

        self.impl.process_inputs()

        glClearColor(c0, c1, c2, c3)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        return inputs, time
    
    def EndFrame(self):
        # Can manually set the position of mouse to center of screen per frame
        # glfw.set_cursor_pos(self.window, self.windowWidth/2, self.windowHeight/2) 
        
        glfw.swap_buffers(self.window) 
    
