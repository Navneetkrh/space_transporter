import ctypes
import numpy as np
import copy
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

class VBO:
    def __init__(self, vertices):
        self.ID = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.ID)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    def Use(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.ID)
    def Delete(self):
        glDeleteBuffers(1, (self.ID,))

class IBO:
    def __init__(self, indices):
        self.ID = glGenBuffers(1)
        self.count = len(indices)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ID)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
    def Use(self):
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ID)
    def Delete(self):
        glDeleteBuffers(1, (self.ID,))

class VAO:
    def __init__(self, vbo : VBO):
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        vbo.Use()
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, ctypes.c_uint(6 * ctypes.sizeof(ctypes.c_float)), ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, ctypes.c_uint(6 * ctypes.sizeof(ctypes.c_float)), ctypes.c_void_p(3 * ctypes.sizeof(ctypes.c_float)))
    def Use(self):
        glBindVertexArray(self.vao)
    def Delete(self):
        glDeleteVertexArrays(1, (self.vao,))

class Shader:
    def __init__(self, vertex_shader, fragment_shader):
        self.ID = compileProgram(compileShader(vertex_shader, GL_VERTEX_SHADER), compileShader(fragment_shader, GL_FRAGMENT_SHADER))
        self.Use()
    def Use(self):
        glUseProgram(self.ID)
    def Delete(self):
        glDeleteProgram((self.ID,))

class Camera:
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.position = np.array([50,0,0], dtype=np.float32)
        self.lookAt = np.array([0,0,0], dtype=np.float32)
        self.up = np.array([0,0,1], dtype=np.float32)
        self.near = 1.0
        self.far = 10000.0
        self.fov = 90

        self.f = 1.0

    def Update(self, shader):
        shader.Use()

        # View matrix

        viewTranslate = np.array([  [1, 0, 0, -self.position[0]],
                                    [0, 1, 0, -self.position[1]],
                                    [0, 0, 1, -self.position[2]],
                                    [0, 0, 0, 1]], dtype = np.float32)
        
        n = - self.lookAt / np.linalg.norm(self.lookAt)
        
        u = np.cross(self.up, n)
        u = u / np.linalg.norm(u)

        v = np.cross(n, u)
        v = v / np.linalg.norm(v)

        viewRotate = np.array([[u[0], u[1], u[2],0],
                            [v[0], v[1], v[2],0],
                            [n[0], n[1], n[2],0],
                            [  0,    0,    0, 1]], dtype = np.float32)

        viewMatrix = viewRotate @ viewTranslate
        
        # Projection matrix

        orthoTranslate = np.array([  [1,0,0,0],
                                    [0,1,0,0],
                                    [0,0,1, (self.near + self.far)/2.0],
                                    [0,0,0,1]], dtype = np.float32)
        
        fovRadians = np.radians(self.fov/2)
        cameraHeight = 2 * self.f * np.tan(fovRadians)
        cameraWidth = (self.width/self.height) * cameraHeight
        orthoScale = np.array([ [2.0/cameraWidth, 0, 0, 0],
                                [0, 2.0/cameraHeight, 0, 0],
                                [0, 0, -2.0/(self.far - self.near), 0],
                                [0, 0, 0, 1]], dtype = np.float32)


        projectionMatrix = orthoScale @ orthoTranslate

        viewMatrixLocation = glGetUniformLocation(shader.ID, "viewMatrix".encode('utf-8'))
        glUniformMatrix4fv(viewMatrixLocation, 1, GL_TRUE, viewMatrix)

        projectionMatrixLocation = glGetUniformLocation(shader.ID, "projectionMatrix".encode('utf-8'))
        glUniformMatrix4fv(projectionMatrixLocation, 1, GL_TRUE, projectionMatrix)

        focalLengthLocation = glGetUniformLocation(shader.ID, "focalLength".encode('utf-8'))
        glUniform1f(focalLengthLocation, self.f)

class Object:
    def __init__(self, objType, shader, properties):
        self.properties = copy.deepcopy(properties)

        self.vbo = VBO(self.properties['vertices'])
        self.ibo = IBO(self.properties['indices'])
        self.vao = VAO(self.vbo, self.vbl)

        self.properties.pop('vertices')
        self.properties.pop('indices')

        # Create shaders
        self.shader = shader

    def Draw(self): # Suggestion: Can assosiate new class variable 'self.objType' to write different Draw logic for different types of objects
        position = self.properties['position']
        rotation = self.properties['rotation']
        scale = self.properties['scale']

        translation_matrix = np.array([[1,0,0, position[0]],
                                    [0,1,0, position[1]],
                                    [0,0,1, position[2]],
                                    [0,0,0,1]], dtype = np.float32)
        
        rotation_z_matrix = np.array([
                                    [np.cos(rotation[2]), -np.sin(rotation[2]), 0, 0],
                                    [np.sin(rotation[2]), np.cos(rotation[2]), 0, 0],
                                    [0, 0, 1, 0],
                                    [0, 0, 0, 1]
                                ], dtype=np.float32)
        rotation_x_matrix = np.array([
                                    [1, 0, 0, 0],
                                    [0, np.cos(rotation[0]), -np.sin(rotation[0]), 0],
                                    [0, np.sin(rotation[0]), np.cos(rotation[0]), 0],
                                    [0, 0, 0, 1]
                                ], dtype=np.float32)
        rotation_y_matrix = np.array([
                                    [np.cos(rotation[1]), 0, np.sin(rotation[1]), 0],
                                    [0, 1, 0, 0],
                                    [-np.sin(rotation[1]), 0, np.cos(rotation[1]), 0],
                                    [0, 0, 0, 1]
                                ], dtype=np.float32)

        scale_matrix = np.array([[scale[0], 0,0,0],
                                [0,scale[1],0,0],
                                [0,0,scale[2],0],
                                [0,0,0,1]], dtype = np.float32)
        
        rotationMatrix = rotation_z_matrix @ rotation_y_matrix @ rotation_x_matrix # Roll then pitch then yaw in order (right to left applied)
        self.modelMatrix = translation_matrix @ rotationMatrix @ scale_matrix

        # Bind the shader, set uniforms, bind vao (automatically binds vbo) and ibo
        self.shader.Use()
        modelMatrixLocation = glGetUniformLocation(self.shader.ID, "modelMatrix".encode('utf-8'))
        glUniformMatrix4fv(modelMatrixLocation, 1, GL_TRUE, self.modelMatrix)
        
        colourLocation = glGetUniformLocation(self.shader.ID, "objectColour".encode('utf-8'))
        glUniform4f(colourLocation, self.properties["colour"][0], 
                    self.properties["colour"][1], 
                    self.properties["colour"][2], 
                    self.properties["colour"][3])
        self.vao.Use()
        self.ibo.Use()

        # Issue Draw call with primitive type
        glDrawElements(GL_TRIANGLES, self.ibo.count, GL_UNSIGNED_INT, None)