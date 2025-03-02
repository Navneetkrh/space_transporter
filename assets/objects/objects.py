import random
import time
import numpy as np
import os
from utils.graphics import Object, Shader
from utils.matrix_utils import rotation_matrix, euler_to_matrix, matrix_to_euler
from assets.shaders.shaders import standard_shader,laser_shader,minimap_shader,crosshair_shader
import os
import numpy as np

def load_obj_file(file_path):
    vertices = []
    normals = []
    texture_coords = []
    faces = []
    
    with open(file_path, 'r') as f:
        for line in f:
            
            line = line.strip()
            if not line or line.startswith('#'):  
                
            
            if line.startswith('v '):
                
                parts = line[2:].strip().split()
                if len(parts) >= 3:  
                    vertices.append([float(parts[0]), float(parts[1]), float(parts[2])])
            
            
            elif line.startswith('vn '):
                parts = line[3:].strip().split()
                if len(parts) >= 3:
                    normals.append([float(parts[0]), float(parts[1]), float(parts[2])])
            
            
            elif line.startswith('vt '):
                parts = line[3:].strip().split()
                if len(parts) >= 2:
                    texture_coords.append([float(parts[0]), float(parts[1])])
            
            
            elif line.startswith('f '):
                face = []
                
                for vertex_spec in line[2:].strip().split():
                    
                    indices = vertex_spec.split('/')
                    v_idx = int(indices[0]) - 1
                    t_idx = int(indices[1]) - 1 if len(indices) > 1 and indices[1] else -1
                    n_idx = int(indices[2]) - 1 if len(indices) > 2 and indices[2] else -1
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
    def __init__(self, model_path, scale=1.0,shader=standard_shader):
        
        model_properties = load_and_process_obj(model_path, scale)
        
        
        self.shader = Shader(shader["vertex_shader"], shader["fragment_shader"])
        self.graphics_obj = Object("standard", self.shader, model_properties)
        
        
        self.position = np.zeros(3, dtype=np.float32)
        # Initialize rotation matrix as identity matrix
        self.rotation_matrix = np.identity(3, dtype=np.float32)
        # Keep rotation angles for compatibility with existing code
        self.rotation = np.zeros(3, dtype=np.float32)
        self.velocity = np.zeros(3, dtype=np.float32)
        self.rotation_velocity = np.zeros(3, dtype=np.float32)
        self.acceleration = np.zeros(3, dtype=np.float32)
        self.drag_factor = 0.98  
        self.orientation = np.identity(3, dtype=np.float32)

    def update(self, delta_time):
        self.update_position(delta_time)
        self.update_rotation(delta_time)
        self.apply_drag(self.drag_factor)
    
    def update_position(self, delta_time):
        self.position += self.velocity * delta_time
        self.graphics_obj.properties['position'] = self.position
    
    def update_rotation(self, delta_time):
        if np.any(self.rotation_velocity):
            # Create a combined delta rotation matrix directly
            delta_rotation = rotation_matrix(
                self.rotation_velocity[0] * delta_time,
                self.rotation_velocity[1] * delta_time, 
                self.rotation_velocity[2] * delta_time
            )
            
            # Apply the rotation from the right (matches the sample code's approach)
            self.orientation = self.orientation @ delta_rotation
            
            # Normalize the orientation matrix to prevent drift
            u, _, vh = np.linalg.svd(self.orientation)
            self.orientation = u @ vh
            
            # Update rotation_matrix for compatibility with our existing code
            self.rotation_matrix = self.orientation
            
            # Update Euler angles for compatibility with renderer
            self.rotation = matrix_to_euler(self.orientation)
            
        # Update the graphics object with the current Euler angles
        self.graphics_obj.properties['rotation'] = self.rotation
    
    def matrix_to_euler(self, R):
        """Convert a rotation matrix to Euler angles (ZYX convention)."""
        # Handle singularity cases (gimbal lock)
        if abs(R[2,0]) >= 1.0:
            # Gimbal lock case
            yaw = 0  # Set arbitrary
            if R[2,0] < 0:
                pitch = np.pi/2
                roll = yaw + np.arctan2(R[0,1], R[0,2])
            else:
                pitch = -np.pi/2
                roll = -yaw + np.arctan2(-R[0,1], -R[0,2])
        else:
            # Standard case
            pitch = np.arcsin(-R[2,0])
            roll = np.arctan2(R[2,1]/np.cos(pitch), R[2,2]/np.cos(pitch))
            yaw = np.arctan2(R[1,0]/np.cos(pitch), R[0,0]/np.cos(pitch))
            
        return np.array([roll, pitch, yaw], dtype=np.float32)
    
    def euler_to_matrix(self, euler):
        """Convert Euler angles (roll, pitch, yaw) to rotation matrix."""
        rx, ry, rz = euler
        
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(rx), -np.sin(rx)],
            [0, np.sin(rx),  np.cos(rx)]
        ])
        
        Ry = np.array([
            [ np.cos(ry), 0, np.sin(ry)],
            [0, 1, 0],
            [-np.sin(ry), 0, np.cos(ry)]
        ])
        
        Rz = np.array([
            [np.cos(rz), -np.sin(rz), 0],
            [np.sin(rz),  np.cos(rz), 0],
            [0, 0, 1]
        ])
        
        return Rz @ Ry @ Rx
    
    def apply_drag(self, drag_factor):
        self.velocity *= drag_factor
        self.rotation_velocity *= drag_factor
    
    def Draw(self):
        self.graphics_obj.Draw()
    
    def set_position(self, position):
        self.position = np.array(position, dtype=np.float32)
        self.graphics_obj.properties['position'] = self.position
    
    def set_rotation(self, rotation):
        """Set rotation using Euler angles (for backwards compatibility)."""
        self.rotation = np.array(rotation, dtype=np.float32)
        self.orientation = euler_to_matrix(self.rotation)
        self.rotation_matrix = self.orientation
        self.graphics_obj.properties['rotation'] = self.rotation
    
    def set_rotation_matrix(self, matrix):
        """Set rotation using a rotation matrix directly."""
        self.orientation = np.array(matrix, dtype=np.float32)
        self.rotation_matrix = self.orientation
        self.rotation = matrix_to_euler(self.orientation)
        self.graphics_obj.properties['rotation'] = self.rotation
    
    def set_velocity(self, velocity):
        self.velocity = np.array(velocity, dtype=np.float32)
    
    def set_rotation_velocity(self, rotation_velocity):
        self.rotation_velocity = np.array(rotation_velocity, dtype=np.float32)
    
    def add_force(self, direction, magnitude):
        force = np.array(direction, dtype=np.float32)
        
        if np.linalg.norm(force) > 0:
            force = force / np.linalg.norm(force)
        
        self.velocity += force * magnitude
    
    def add_torque(self, axis, magnitude):
        torque = np.array(axis, dtype=np.float32)
        
        if np.linalg.norm(torque) > 0:
            torque = torque / np.linalg.norm(torque)
        
        self.rotation_velocity += torque * magnitude
    
    def set_color(self, color):
        self.graphics_obj.properties['colour'] = np.array(color, dtype=np.float32)




class Transporter(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'transporter.obj')
        
        super().__init__(model_path, scale=8.0)
        
        
        self.set_color(np.array([0.804, 1, 1, 1], dtype=np.float32))
        self.default_position = np.array([-30, 0, -30], dtype=np.float32)
        self.default_rotation = np.array([0, 0, np.pi], dtype=np.float32)
        self.set_position(self.default_position)
        self.set_rotation(self.default_rotation)
        
        
        self.max_speed = 250.0  
        self.max_rotation_speed = 2.0  
        self.thrust_power = 5.0  
        self.turn_power = 0.0165
        self.drag_factor = 0.98  
        
        # Add acceleration tracking
        self.is_accelerating = False
        self.acceleration_time = 0.0
        
        self.forward_speed = 0.0  
        
        
        self.health = 100
        self.shield = 100
        self.view = 1  
        self.target_planet = None
        self.start_planet = None
        
        
        self.laser_cooldown = 0.5
        self.last_shot_time = 0.0

        
        self.local_forward = np.array([1, 0, 0], dtype=np.float32)
        self.local_right   = np.array([0, -1, 0], dtype=np.float32)
        self.local_up      = np.array([0, 0, -1], dtype=np.float32)
        
        
        self.forward_direction = self.local_forward.copy()
        self.right_direction = self.local_right.copy()
        self.up_direction = self.local_up.copy()
    
    def process_inputs(self, inputs, delta_time):
        # Create incremental rotation matrix directly based on inputs
        dR = np.eye(3, dtype=np.float32)
        rotation_speed = self.turn_power * 50  # Adjust for reasonable rotation speed
        
        if inputs["Q"]:
            dR = dR @ rotation_matrix(rotation_speed * delta_time, 0, 0)  # pitch down
        if inputs["E"]:
            dR = dR @ rotation_matrix(-rotation_speed * delta_time, 0, 0)  # pitch up
        if inputs["A"] :
            dR = dR @ rotation_matrix(0, 0, -rotation_speed * delta_time)  # roll left
        # elif inputs["A"] and self.local_up.dot(self.up_direction) < 0:
        #     dR = dR @ rotation_matrix(0, 0, rotation_speed * delta_time)  # roll right
        if inputs["D"] :
            dR = dR @ rotation_matrix(0, 0, rotation_speed * delta_time)  # roll right
        # elif inputs["D"] and self.local_up.dot(self.up_direction) < 0:
        #     dR = dR @ rotation_matrix(0, 0, -rotation_speed * delta_time)  # roll left
        if inputs["W"]:
            dR = dR @ rotation_matrix(0, rotation_speed * delta_time, 0)  # yaw left
        if inputs["S"]:
            dR = dR @ rotation_matrix(0, -rotation_speed * delta_time, 0)  # yaw right

        # Apply the incremental rotation to the current orientation
        self.orientation = self.orientation @ dR
        
        # Normalize to prevent drift
        u, _, vh = np.linalg.svd(self.orientation)
        self.orientation = u @ vh
        
        # Track if accelerating
        self.is_accelerating = inputs["SPACE"]
        if self.is_accelerating:
            self.acceleration_time += delta_time
        else:
            self.acceleration_time = max(0.0, self.acceleration_time - delta_time * 2)
        
        # Apply thrust in the forward direction
        if inputs["SPACE"] or inputs['L_CLICK']:
            self.add_force(self.forward_direction, self.thrust_power)
    
    def update(self, inputs, delta_time):
        # Process inputs first
        self.process_inputs(inputs, delta_time)
        
        # Update world-space direction vectors using the orientation matrix
        self.forward_direction = self.orientation @ self.local_forward
        self.right_direction = self.orientation @ self.local_right
        self.up_direction = self.orientation @ self.local_up
        
        # Ensure normalized direction vectors
        self.forward_direction /= np.linalg.norm(self.forward_direction)
        self.right_direction /= np.linalg.norm(self.right_direction)
        self.up_direction /= np.linalg.norm(self.up_direction)
        
        # Update rotation_matrix and Euler angles for compatibility
        self.rotation_matrix = self.orientation
        self.rotation = matrix_to_euler(self.orientation)
        self.graphics_obj.properties['rotation'] = self.rotation
        
        # Limit speed
        speed = np.linalg.norm(self.velocity)
        if speed > self.max_speed:
            self.velocity = (self.velocity / speed) * self.max_speed
        
        # Update position with current velocity
        self.position += self.velocity * delta_time
        self.graphics_obj.properties['position'] = self.position
        
        # Apply drag
        self.velocity *= self.drag_factor
    
    def can_shoot(self, current_time):
        
        return True
    
    def shoot(self, current_time):
        if self.can_shoot(current_time):
            # print("Pew pew!")
            self.last_shot_time = current_time
            

            laser = Laser()
            
            
            laser_offset = self.forward_direction * 5.0  
            laser_pos = self.position + laser_offset
            laser.set_position(laser_pos)
            
            
            laser.set_rotation(self.rotation.copy())
            
            
            laser_speed = laser.speed+np.linalg.norm(self.velocity)
            laser.set_velocity(self.forward_direction * laser_speed)
            
            
            # laser.lifetime = 3.0
            # laser.time_alive = 0.0
            
            return laser
        
        return None
    
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
        self.view = 3 - self.view  

class Pirate(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'pirate.obj')
        super().__init__(model_path, scale=20.0)  
        
        # Set colors and base properties
        self.set_color(np.array([0.2, 0.8, 0.7, 1.0], dtype=np.float32))
        
        # Simplified speed properties - faster pursuit speed
        self.chase_speed = random.uniform(120.0, 160.0)
        self.patrol_speed = 40.0  # Fixed slower patrol speed
        self.chase_distance = 10000.0  # Detection range
        
        # Combat properties
        self.health = 3  
        self.damage = 100  
        self.collision_radius = 80  
        
        # Movement properties
        self.direction_timer = 0.0
        self.direction_change_interval = 5.0  # Fixed interval for patrols
        self.rotation_speed = 2.0  # Faster rotation
        
        # Initialize with random direction and rotation
        self.target_direction = self.generate_random_direction()
        self.set_rotation(np.array([0, random.uniform(0, 2*np.pi), 0], dtype=np.float32))
    
    def generate_random_direction(self):
        """Generate a random normalized direction vector."""
        direction = np.array([
            random.uniform(-1.0, 1.0),
            0.0,  # Keep movement in horizontal plane
            random.uniform(-1.0, 1.0)
        ], dtype=np.float32)
        return direction / np.linalg.norm(direction)
    
    def update(self, delta_time, player_position, player_forward=None):
        # Calculate vector to player
        to_player = player_position - self.position
        distance_to_player = np.linalg.norm(to_player)
        
        if distance_to_player < self.chase_distance:
            # CHASE MODE - Direct pursuit
            self.target_direction = to_player / distance_to_player
            self.velocity = self.target_direction * self.chase_speed
        else:
            # PATROL MODE - Simple wandering
            self.direction_timer += delta_time
            if self.direction_timer >= self.direction_change_interval:
                self.target_direction = self.generate_random_direction()
                self.direction_timer = 0.0
            
            # World boundary check
            world_boundary = 4800
            for i in range(3):
                if abs(self.position[i]) > world_boundary:
                    self.target_direction[i] = -np.sign(self.position[i])
            
            self.velocity = self.target_direction * self.patrol_speed
        
        # Rotate to face movement direction
        if np.linalg.norm(self.velocity) > 0.1:
            target_yaw = np.arctan2(self.velocity[2], self.velocity[0])
            current_yaw = self.rotation[1]
            angle_diff = (target_yaw - current_yaw + np.pi) % (2 * np.pi) - np.pi
            
            # Smooth rotation
            rotation_amount = min(self.rotation_speed * delta_time, abs(angle_diff))
            if abs(angle_diff) > 0.01:
                if angle_diff > 0:
                    self.rotation[1] += rotation_amount
                else:
                    self.rotation[1] -= rotation_amount
        
        super().update(delta_time)
    
    def take_damage(self, amount):
        self.health -= amount
        return self.health <= 0


class Planet(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'planet.obj')
        super().__init__(model_path, scale=100.0)
        
        
        self.set_rotation(np.array([
            np.random.uniform(0, np.pi*2),
            np.random.uniform(0, np.pi*2),
            np.random.uniform(0, np.pi*2)
        ], dtype=np.float32))
        
        
        self.set_color(np.array([0.8, 0.8, 0.8, 1.0], dtype=np.float32))

class SpaceStation(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'spacestation.obj')
        super().__init__(model_path, scale=8.0)
        
        
        self.set_color(np.array([0.7, 0.7, 0.9, 1.0], dtype=np.float32))
        
        
        self.parent_planet = None
        self.orbit_angle = 0.0
        self.orbit_radius = 250.0
        self.orbit_speed = 0.3  
    
    def update(self, delta_time):
        
        if self.parent_planet is not None:
            
            self.orbit_angle += self.orbit_speed * delta_time
            
            
            planet_pos = self.parent_planet.position
            self.position = planet_pos + np.array([
                self.orbit_radius * np.cos(self.orbit_angle),
                0,  
                self.orbit_radius * np.sin(self.orbit_angle)
            ], dtype=np.float32)
            
            
            self.graphics_obj.properties['position'] = self.position
            
            
            self.rotation += np.array([0, 0.1 * delta_time, 0], dtype=np.float32)
            self.graphics_obj.properties['rotation'] = self.rotation

            
class MinimapArrow(GameObject):
    def __init__(self, target_object=None, color=None):
        model_path = os.path.join('assets', 'objects', 'models', 'arrow.obj')
        
        super().__init__(model_path, scale=30.0)
        
        
        self.target_object = target_object
        
        
        if color is not None:
            self.set_color(color)
        else:
            
            self.set_color(np.array([0.0, 2.0, 0.0, 1.0], dtype=np.float32))
        
        
        self.offset = np.array([0.0, 50.0, 0.0], dtype=np.float32)
        
        self.max_distance = 10000.0  
        self.min_distance = 10.0     
        
        
        self.initial_rotation = np.array([np.pi/2, 0.0, 0.0], dtype=np.float32)
        self.set_rotation(self.initial_rotation)

    def update(self, player_position, player_rotation, player_directions):
        if self.target_object is None:
            return
        
        
        to_target = self.target_object.position - player_position
        distance = np.linalg.norm(to_target)
        
        
        if (distance < self.min_distance):
            self.set_position(np.array([10000, 10000, 10000], dtype=np.float32))
            return

        
        arrow_position = player_position + np.array([0.0, self.offset[1], 0.0], dtype=np.float32)
        self.set_position(arrow_position)
        
        
        direction = to_target / distance if distance > 0 else np.array([1, 0, 0], dtype=np.float32)
        
        
        yaw = np.arctan2(direction[0], direction[2])
        pitch = np.arcsin(-direction[1]) + np.pi/4  
        
        
        self.set_rotation(np.array([pitch, yaw, 0.0], dtype=np.float32))
        
        
        self.graphics_obj.properties['scale'] = np.array([30.0, 30.0, 30.0], dtype=np.float32)

class Crosshair(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'direction_arrow.obj')
        super().__init__(model_path, scale=0.05, shader=crosshair_shader)
        
        
        self.set_color(np.array([1.0, 0.2, 0.2, 1.0], dtype=np.float32))
        
        
        self.distance_from_camera = 10.0  
        
    def update(self, camera_position, camera_forward):
        """Update crosshair position based on camera."""
        
        self.set_position(camera_position + camera_forward * self.distance_from_camera)
        
        
        direction = camera_forward / np.linalg.norm(camera_forward)
        
        
        
        pitch = np.arcsin(direction[1])
        yaw = np.arctan2(direction[0], direction[2])
        
        self.set_rotation(np.array([pitch, yaw, 0.0], dtype=np.float32))

class Laser(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'laser.obj')
        super().__init__(model_path, scale=7, shader=laser_shader)
        
        
        self.set_color(np.array([0.5, 0, 1, 1.0], dtype=np.float32))
        
        
        self.lifetime = 3.0  
        self.time_alive = 0.0
        self.speed =10000

        
    def update(self, delta_time):
        
        super().update(delta_time)
        
        
        self.time_alive += delta_time
        
        
        return self.time_alive >= self.lifetime

















