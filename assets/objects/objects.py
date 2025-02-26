import numpy as np
import os
from utils.graphics import Object, Shader
from assets.shaders.shaders import standard_shader

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

def load_and_process_obj(model_path, scale=1.0):
    vertices, normals, _, faces = load_obj_file(model_path)
    
    vertices_with_normals = []
    indices = []
    index = 0
    
    for face in faces:
        for vertex_data in face:
            v_idx, _, n_idx = vertex_data
            vertex = vertices[v_idx]
            normal = normals[n_idx] if n_idx != -1 else [0, 0, 1]
            vertices_with_normals.extend([*vertex, *normal])
            indices.append(index)
            index += 1
    
    properties = {
        'vertices': np.array(vertices_with_normals, dtype=np.float32),
        'indices': np.array(indices, dtype=np.uint32),
        'position': np.zeros(3),
        'rotation': np.zeros(3),
        'scale': np.array([scale, scale, scale]),
        'colour': np.array([1.0, 1.0, 1.0, 1.0])
    }
    
    return properties

class GameObject:
    def __init__(self, model_path, scale=1.0):
        # Use the existing load_and_process_obj function to get properties
        self.properties = load_and_process_obj(model_path, scale)
        
        # Create shader and graphics object
        self.shader = Shader(standard_shader["vertex_shader"], standard_shader["fragment_shader"])
        self.graphics_obj = Object("standard", self.shader, self.properties)
    
    def update(self, delta_time):
        pass
    
    def Draw(self):
        self.graphics_obj.Draw()
    
    def set_position(self, position):
        self.graphics_obj.properties['position'] = np.array(position, dtype=np.float32)
    
    def set_rotation(self, rotation):
        self.graphics_obj.properties['rotation'] = np.array(rotation, dtype=np.float32)
    
    def set_color(self, color):
        self.graphics_obj.properties['colour'] = np.array(color, dtype=np.float32)

class Transporter(GameObject):
    def __init__(self):


        model_path = os.path.join('assets', 'objects', 'models', 'transporter.obj')
        # Adjust scale to make the model more visible (original seems too small)
        super().__init__(model_path, scale=8.0)
        
        # Set initial color to white to match the model
        self.set_color(np.array([0.804, 0.498, 0.196, 1], dtype=np.float32))
         
        # Physics properties
        self.properties['velocity'] = np.zeros(3, dtype=np.float32)
        self.properties['acceleration'] = np.zeros(3, dtype=np.float32)
        self.properties['max_speed'] = 50.0
        self.properties['rotation_speed'] = 20.0
        
        # Game state properties
        self.properties['health'] = 100
        self.properties['shield'] = 100
        self.properties['view'] = 1  # 1 for third-person, 2 for first-person
        self.properties['target_planet'] = None
        self.properties['start_planet'] = None
        
        # Initial orientation (make it face forward)
        self.set_position(np.array([100,100.0, 100.0], dtype=np.float32))
        self.set_rotation(np.array([0, 0, np.pi], dtype=np.float32))
        
        # Weapon properties
        self.properties['laser_cooldown'] = 0.5
        self.properties['last_shot_time'] = 0.0
    def process_inputs(self, inputs, delta_time):
        # Process inputs to update transporter's state
        # This will involve updating velocity, rotation, and potentially shooting lasers
        # For example:
        if inputs["A"]:
            self.accelerate(np.array([1, 0, 0]))
        if inputs["D"]:
            self.accelerate(np.array([-1, 0, 0]))
        if inputs["W"]:
            self.accelerate(np.array([1, 0, 0]))
        if inputs["S"]:
            self.accelerate(np.array([-1,0, 0]))
        if inputs["Q"]:
            self.rotate(np.array([0, 0, 1]))
        if inputs["E"]:
            self.rotate(np.array([0, 0, -1]))
        if inputs["SPACE"]:
            self.shoot()

    def update(self,inputs, delta_time):
        # Update transporter's state based on inputs and physics
        self.process_inputs(inputs, delta_time)

              
        # Update position based on velocity
        # print(type(self.properties['velocity'] ),print(type(delta_time),print(delta_time)))
        self.properties['position'] += self.properties['velocity'] * delta_time
        
        # Apply drag/friction to gradually slow down
        drag_factor = 0.98
        self.properties['velocity'] *= drag_factor
        
        # Clamp velocity to max speed
        speed = np.linalg.norm(self.properties['velocity'])
        if speed > self.properties['max_speed']:
            self.properties['velocity'] = (self.properties['velocity'] / speed) * self.properties['max_speed']
    
    def accelerate(self, direction):
        acceleration = 20.0  # Acceleration rate
        self.properties['velocity'] += direction * acceleration
    
    def rotate(self, angles):
        self.properties['rotation'] += angles * self.properties['rotation_speed']
    
    def can_shoot(self, current_time):
        return current_time - self.properties['last_shot_time'] >= self.properties['laser_cooldown']
    
    def shoot(self, current_time):
        if self.can_shoot(current_time):
            self.properties['last_shot_time'] = current_time
            return True
        return False
    
    def take_damage(self, amount):
        if self.properties['shield'] > 0:
            self.properties['shield'] -= amount
            if self.properties['shield'] < 0:
                overflow = -self.properties['shield']
                self.properties['shield'] = 0
                self.properties['health'] -= overflow
        else:
            self.properties['health'] -= amount
        
        return self.properties['health'] <= 0
    
    def toggle_view(self):
        self.properties['view'] = 3 - self.properties['view']  # Toggle between 1 and 2
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