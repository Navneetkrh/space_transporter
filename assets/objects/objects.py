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
        model_properties = load_and_process_obj(model_path, scale)
        
        # Create shader and graphics object
        self.shader = Shader(standard_shader["vertex_shader"], standard_shader["fragment_shader"])
        self.graphics_obj = Object("standard", self.shader, model_properties)
        
        # Common properties for all game objects
        self.position = np.zeros(3, dtype=np.float32)
        self.rotation = np.zeros(3, dtype=np.float32)
        self.velocity = np.zeros(3, dtype=np.float32)
        self.rotation_velocity = np.zeros(3, dtype=np.float32)
        self.acceleration = np.zeros(3, dtype=np.float32)
        self.drag_factor = 0.98  # Default drag factor
    
    def update(self, delta_time):
        # Base update method to be overridden by child classes
        self.update_position(delta_time)
        self.update_rotation(delta_time)
        self.apply_drag(self.drag_factor)
    
    def update_position(self, delta_time):
        # Update position based on velocity
        self.position += self.velocity * delta_time
        self.graphics_obj.properties['position'] = self.position
    
    def update_rotation(self, delta_time):
        # Update rotation based on rotation velocity
        self.rotation += self.rotation_velocity * delta_time
        self.graphics_obj.properties['rotation'] = self.rotation
    
    def apply_drag(self, drag_factor):
        # Apply drag to gradually slow down
        self.velocity *= drag_factor
        self.rotation_velocity *= drag_factor
    
    def Draw(self):
        self.graphics_obj.Draw()
    
    def set_position(self, position):
        self.position = np.array(position, dtype=np.float32)
        self.graphics_obj.properties['position'] = self.position
    
    def set_rotation(self, rotation):
        self.rotation = np.array(rotation, dtype=np.float32)
        self.graphics_obj.properties['rotation'] = self.rotation
    
    def set_velocity(self, velocity):
        self.velocity = np.array(velocity, dtype=np.float32)
    
    def set_rotation_velocity(self, rotation_velocity):
        self.rotation_velocity = np.array(rotation_velocity, dtype=np.float32)
    
    def add_force(self, direction, magnitude):
        force = np.array(direction, dtype=np.float32)
        # Normalize the direction vector
        if np.linalg.norm(force) > 0:
            force = force / np.linalg.norm(force)
        # Apply the force
        self.velocity += force * magnitude
    
    def add_torque(self, axis, magnitude):
        torque = np.array(axis, dtype=np.float32)
        # Normalize the axis vector
        if np.linalg.norm(torque) > 0:
            torque = torque / np.linalg.norm(torque)
        # Apply the torque
        self.rotation_velocity += torque * magnitude
    
    def set_color(self, color):
        self.graphics_obj.properties['colour'] = np.array(color, dtype=np.float32)


class Transporter(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'transporter.obj')
        # Adjust scale to make the model more visible
        super().__init__(model_path, scale=8.0)
        
        # Set initial color and position
        self.set_color(np.array([0.804, 1, 1, 1], dtype=np.float32))
        self.set_position(np.array([-30, 0, -30], dtype=np.float32))
        self.set_rotation(np.array([0, 0, np.pi], dtype=np.float32))
         
        # Physics properties
        self.max_speed = 50.0  # Maximum linear speed
        self.max_rotation_speed = 2.0  # Maximum rotation speed
        self.thrust_power = 10.0  # Acceleration power when using spacebar
        self.turn_power = 0.01  # Rotation power for flight controls
        self.drag_factor = 0.98  # Drag coefficient to slow down over time
        
        # Advanced flight properties
        self.forward_speed = 0.0  # Current forward speed
        
        # Game state properties
        self.health = 100
        self.shield = 100
        self.view = 1  # 1 for third-person, 2 for first-person
        self.target_planet = None
        self.start_planet = None
        
        # Weapon properties
        self.laser_cooldown = 0.5
        self.last_shot_time = 0.0
        
    def process_inputs(self, inputs, delta_time):
        # Process rotation inputs based on flight controls
        if inputs["W"]:  # Pitch down (rotate around X axis)
            self.add_torque([0, 1, 0], self.turn_power)
        if inputs["S"]:  # Pitch up (rotate around X axis)
            self.add_torque([0, -1, 0], self.turn_power)
        if inputs["A"]:  # Yaw left (rotate around Y axis)
            self.add_torque([0, 0, 1], self.turn_power)
        if inputs["D"]:  # Yaw right (rotate around Y axis)
            self.add_torque([0, 0, -1], self.turn_power)
        if inputs["Q"]:  # Roll left (rotate around Z axis)
            self.add_torque([0, 0, 1], self.turn_power)
        if inputs["E"]:  # Roll right (rotate around Z axis)
            self.add_torque([0, 0, -1], self.turn_power)
            
        # Process acceleration input (spacebar)
        if inputs["SPACE"]:
            # In a more advanced implementation, you'd calculate the forward vector
            # based on the current rotation matrix. For simplicity, we'll use
            # the negative Z axis as our forward direction.
            forward_direction = [0, 0, -1]
            self.add_force(forward_direction, self.thrust_power)
            
        # For shooting lasers, we'll use a different key
        if inputs.get("F", False):  # Use F key for firing
            current_time = time.time()  # You'll need to import time
            self.shoot(current_time)

    def update(self, inputs, delta_time):
        # Process inputs first
        self.process_inputs(inputs, delta_time)
        
        # Calculate forward direction based on current rotation
        # In a more complex implementation, you would use a full rotation matrix
        # For simplicity, we'll use basic transformations
       
        # Clamp velocity to max speed
        speed = np.linalg.norm(self.velocity)
        if speed > self.max_speed:
            self.velocity = (self.velocity / speed) * self.max_speed
            
        # Clamp rotation velocity to max rotation speed
        rot_speed = np.linalg.norm(self.rotation_velocity)
        if rot_speed > self.max_rotation_speed:
            self.rotation_velocity = (self.rotation_velocity / rot_speed) * self.max_rotation_speed
        
        # Update position and rotation (parent class handles this)
        super().update(delta_time)
        
        # Debug info
        print(f"Position: {self.position}")
        print(f"Velocity: {self.velocity}")
        print(f"Rotation: {self.rotation}")
        print(f"Speed: {speed:.2f} / {self.max_speed:.2f}")
    
    def can_shoot(self, current_time):
        return current_time - self.last_shot_time >= self.laser_cooldown
    
    def shoot(self, current_time):
        if self.can_shoot(current_time):
            self.last_shot_time = current_time
            print("Shooting laser!")
            # Here you would create a laser object or call a function to handle shooting
            return True
        return False
    
    def take_damage(self, amount):
        if self.shield > 0:
            self.shield -= amount
            if self.shield < 0:
                overflow = -self.shield
                self.shield = 0
                self.health -= overflow
        else:
            self.health -= amount
        
        return self.health <= 0
    
    def toggle_view(self):
        self.view = 3 - self.view  # Toggle between 1 and 2
class Pirate(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'pirate.obj')
        super().__init__(model_path)

# Update Planet class
class Planet(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'planet.obj')
        super().__init__(model_path, scale=100.0)
        
        # Set a random rotation
        self.set_rotation(np.array([
            np.random.uniform(0, np.pi*2),
            np.random.uniform(0, np.pi*2),
            np.random.uniform(0, np.pi*2)
        ], dtype=np.float32))
        
        # Set a random color (default color will be adjusted in the Game class)
        self.set_color(np.array([0.8, 0.8, 0.8, 1.0], dtype=np.float32))

class SpaceStation(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'spacestation.obj')
        super().__init__(model_path, scale=5.0)
        
        # Set initial color
        self.set_color(np.array([0.7, 0.7, 0.9, 1.0], dtype=np.float32))
        
        # Orbit properties (will be set by Game class)
        self.parent_planet = None
        self.orbit_angle = 0.0
        self.orbit_radius = 150.0
        self.orbit_speed = 0.3  # Radians per second
    
    def update(self, delta_time):
        # Only update if we have a parent planet
        if self.parent_planet is not None:
            # Update orbit angle
            self.orbit_angle += self.orbit_speed * delta_time
            
            # Calculate new position based on orbit
            planet_pos = self.parent_planet.position
            self.position = planet_pos + np.array([
                self.orbit_radius * np.cos(self.orbit_angle),
                0,  # Keep on same y-level as planet
                self.orbit_radius * np.sin(self.orbit_angle)
            ], dtype=np.float32)
            
            # Update graphics object position
            self.graphics_obj.properties['position'] = self.position
            
            # Add some rotation to the station itself
            self.rotation += np.array([0, 0.1 * delta_time, 0], dtype=np.float32)
            self.graphics_obj.properties['rotation'] = self.rotation

            
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