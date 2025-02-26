from OpenGL.GL import *
from utils.window_manager import Window
from game import Game

class App:
    def __init__(self):
        self.window = Window()
        self.game = Game(self.window.windowHeight, self.window.windowWidth, self.window.impl)

    def RenderLoop(self):

        while self.window.IsOpen():
            inputs, time = self.window.StartFrame(0.0, 0.0, 0.0, 1.0)
            self.game.ProcessFrame(inputs, time)
            self.window.EndFrame()
        
        self.window.Close()

if __name__ == "__main__":
    app = App()
    app.RenderLoop()


