import numpy as np
import os

def load_obj_file(file_path):
    vertices = []
    normals = []
    texture_coords = []
    faces = []
    
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('v '):
                vertices.append([float(x) for x in line[2:].split()])
            elif line.startswith('vn '):
                normals.append([float(x) for x in line[3:].split()])
            elif line.startswith('vt '):
                texture_coords.append([float(x) for x in line[3:].split()])
            elif line.startswith('f '):
                face = []
                for vertex in line[2:].split():
                    indices = vertex.split('/')
                    # Convert to 0-based indexing
                    v_idx = int(indices[0]) - 1
                    t_idx = int(indices[1]) - 1 if indices[1] else -1
                    n_idx = int(indices[2]) - 1 if len(indices) > 2 else -1
                    face.append((v_idx, t_idx, n_idx))
                faces.append(face)
    
    return np.array(vertices), np.array(normals), np.array(texture_coords), faces

class GameObject:
    def __init__(self, model_path, scale=1.0):
        self.vertices, self.normals, self.tex_coords, self.faces = load_obj_file(model_path)
        self.position = np.zeros(3)
        self.rotation = np.zeros(3)
        self.scale = np.array([scale, scale, scale])

class Transporter(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'transporter.obj')
        super().__init__(model_path)

class Pirate(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'pirate.obj')
        super().__init__(model_path)

class Planet(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'planet.obj')
        super().__init__(model_path, scale=100.0)

class SpaceStation(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'station.obj')
        super().__init__(model_path, scale=5.0)

class MinimapArrow(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'arrow.obj')
        super().__init__(model_path, scale=0.5)

class Crosshair(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'crosshair.obj')
        super().__init__(model_path, scale=0.1)

class Laser(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'laser.obj')
        super().__init__(model_path, scale=0.2)
        
###############################################################

# Write logic to load OBJ Files:

# Will depend on type of object. For example if normals needed along with vertex positions

# then will need to load slightly differently.

# Can use the provided OBJ files from assignment_2_template/assets/objects/models/

# Can also download other assets or model yourself in modelling softwares like blender

###############################################################

# Create Transporter, Pirates, Stars(optional), Minimap arrow, crosshair, planet, spacestation, laser

###############################################################