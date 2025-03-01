import random
import time
import numpy as np
import os
from utils.graphics import Object, Shader
from assets.shaders.shaders import standard_shader,laser_shader,minimap_shader,crosshair_shader

def load_obj_file(file_path):
    vertices = []
    normals = []
    texture_coords = []
    faces = []
    
    with open(file_path, 'r') as f:
        for line in f:
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Handle vertex data
            if line.startswith('v '):
                # Split on whitespace and take only coordinates (ignore comments)
                parts = line[2:].strip().split()
                if len(parts) >= 3:  # Make sure we have at least x, y, z
                    vertices.append([float(parts[0]), float(parts[1]), float(parts[2])])
            
            # Handle normal data
            elif line.startswith('vn '):
                parts = line[3:].strip().split()
                if len(parts) >= 3:
                    normals.append([float(parts[0]), float(parts[1]), float(parts[2])])
            
            # Handle texture coordinate data
            elif line.startswith('vt '):
                parts = line[3:].strip().split()
                if len(parts) >= 2:
                    texture_coords.append([float(parts[0]), float(parts[1])])
            
            # Handle face data
            elif line.startswith('f '):
                face = []
                # Split by whitespace and process each vertex specification
                for vertex_spec in line[2:].strip().split():
                    # Handle different formats: v, v/vt, v//vn, v/vt/vn
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
        # Use the existing load_and_process_obj function to get properties
        model_properties = load_and_process_obj(model_path, scale)
        
        # Create shader and graphics object
        self.shader = Shader(shader["vertex_shader"], shader["fragment_shader"])
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


import os
import numpy as np

class Transporter(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'transporter.obj')
        # Adjust scale to make the model more visible
        super().__init__(model_path, scale=8.0)
        
        # Set initial color and position
        self.set_color(np.array([0.804, 1, 1, 1], dtype=np.float32))
        self.default_position = np.array([-30, 0, -30], dtype=np.float32)
        self.default_rotation = np.array([0, 0, np.pi], dtype=np.float32)
        self.set_position(self.default_position)
        self.set_rotation(self.default_rotation)
        
        # Physics properties
        self.max_speed = 200.0  # Maximum linear speed
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

        # Local (model-space) directions:
        self.local_forward = np.array([1, 0, 0], dtype=np.float32)
        self.local_right   = np.array([0, -1, 0], dtype=np.float32)
        self.local_up      = np.array([0, 0, -1], dtype=np.float32)
        
        # Initialize world-space direction vectors (they will be updated)
        self.forward_direction = self.local_forward.copy()
        self.right_direction = self.local_right.copy()
        self.up_direction = self.local_up.copy()
    
    def process_inputs(self, inputs, delta_time):
        # Process rotation inputs (on it's own axis)
        if inputs["W"] :  # Pitch down (rotate around Y axis)
            self.add_torque([0, 1, 0], self.turn_power)
        if inputs["S"] :  # Pitch up (rotate around Y axis)
            self.add_torque([0, -1, 0], self.turn_power)
        if inputs["A"] and self.local_up.dot(self.up_direction)>0:  # Yaw left (rotate around Z axis)
            self.add_torque([0, 0, -1], self.turn_power)
        elif inputs["A"] and self.local_up.dot(self.up_direction)<0:  # Yaw left (rotate around Z axis)
            self.add_torque([0, 0, 1], self.turn_power)
        if inputs["D"] and self.local_up.dot(self.up_direction)>0:  # Yaw right (rotate around Z axis)
            self.add_torque([0, 0, 1], self.turn_power)
        elif inputs["D"] and self.local_up.dot(self.up_direction)<0:  # Yaw right (rotate around Z axis)
            self.add_torque([0, 0, -1], self.turn_power)
        if inputs["Q"]:  # Roll left (rotate around X axis)
            self.add_torque([1, 0, 0], self.turn_power)
        if inputs["E"]:  # Roll right (rotate around X axis)
            self.add_torque([-1, 0, 0], self.turn_power)
            
        # Process acceleration input (spacebar)
        if inputs["SPACE"]:
            # Apply thrust in the current forward direction (updated in update)
            self.add_force(self.forward_direction, self.thrust_power)
        
    

    
    def update(self, inputs, delta_time):
        # Process inputs first
        self.process_inputs(inputs, delta_time)
        
        # Update world-space direction vectors based on current rotation.
        # Retrieve Euler angles (assumed order: [pitch, yaw, roll])
        rx, ry, rz = self.rotation

        # Create rotation matrices for each axis:
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
        
        # Combine rotations.
        # One common convention is R = Rz @ Ry @ Rx (roll, then yaw, then pitch).
        rot_matrix = Rz @ Ry @ Rx
        
        # Update direction vectors by transforming local axes:
        self.forward_direction = rot_matrix @ self.local_forward
        self.right_direction   = rot_matrix @ self.local_right
        self.up_direction      = rot_matrix @ self.local_up
        
        # Normalize the direction vectors:
        self.forward_direction /= np.linalg.norm(self.forward_direction)
        self.right_direction   /= np.linalg.norm(self.right_direction)
        self.up_direction      /= np.linalg.norm(self.up_direction)
        
        # Clamp velocity to max speed
        speed = np.linalg.norm(self.velocity)
        if speed > self.max_speed:
            self.velocity = (self.velocity / speed) * self.max_speed
            
        # Clamp rotation velocity to max rotation speed
        rot_speed = np.linalg.norm(self.rotation_velocity)
        if rot_speed > self.max_rotation_speed:
            self.rotation_velocity = (self.rotation_velocity / rot_speed) * self.max_rotation_speed
        
        # Call the parent's update to handle position and rotation integration
        super().update(delta_time)
    
    def can_shoot(self, current_time):
        # return current_time - self.last_shot_time >= self.laser_cooldown
        return True
    
    def shoot(self, current_time):
        if self.can_shoot(current_time):
            print("Pew pew!")
            self.last_shot_time = current_time
            
            # Create a laser object
            from assets.objects.objects import Laser
            laser = Laser()
            
            # Position the laser slightly in front of the transporter
            laser_offset = self.forward_direction * 10.0  # Offset distance
            laser_pos = self.position + laser_offset
            laser.set_position(laser_pos)
            
            # Set the laser's rotation to match the transporter's
            laser.set_rotation(self.rotation.copy())
            
            # Give the laser velocity in the forward direction
            laser_speed = 1000.0 +np.linalg.norm(self.velocity)# Adjust as needed
            laser.set_velocity(self.forward_direction * laser_speed)
            
            # Set a lifetime for the laser (in seconds)
            laser.lifetime = 3.0
            laser.time_alive = 0.0
            
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
        self.view = 3 - self.view  # Toggle between 1 and 2

class Pirate(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'pirate.obj')
        # Increase pirate size significantly
        super().__init__(model_path, scale=20.0)  # Changed from 5.0 to 20.0
        
        # Set bluish-green color for pirates
        self.set_color(np.array([0.2, 0.8, 0.7, 1.0], dtype=np.float32))
        
        # Pirate properties
        self.base_speed = 100.0  # Increased base speed (was 30.0)
        self.speed = self.base_speed + random.uniform(-20.0, 80.0)  # More variability in higher range
        self.patrol_speed = self.base_speed * 0.3  # Slower when patrolling
        self.chase_distance = 30000.0  # Distance at which pirates detect players
        self.health = 3  # Hit points
        self.damage = 100  # Damage dealt on collision
        self.rotation_speed = 1.0 + random.uniform(-0.5, 0.5)  # For natural movement
        self.collision_radius = 80  # Bigger collision hitbox (was implicitly 20.0)
        
        # Patrol behavior properties
        self.patrol_direction = self.generate_random_direction()
        self.direction_change_time = random.uniform(3.0, 8.0)  # Time before changing direction
        self.time_since_direction_change = 0.0
        self.is_patrolling = True
        
        # Add some random rotation for variety
        self.set_rotation(np.array([
            random.uniform(0, np.pi*2),
            random.uniform(0, np.pi*2),
            random.uniform(0, np.pi*2)
        ], dtype=np.float32))
        
        # Last known player forward vector
        self.player_forward = None
    
    def generate_random_direction(self):
        """Generate a random normalized direction vector."""
        direction = np.array([
            random.uniform(-1.0, 1.0),
            random.uniform(-0.2, 0.2),  # Less vertical movement
            random.uniform(-1.0, 1.0)
        ], dtype=np.float32)
        
        # Normalize the direction
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction = direction / norm
        else:
            direction = np.array([1.0, 0.0, 0.0], dtype=np.float32)
            
        return direction
    
    def update(self, delta_time, player_position, player_forward=None):
        # Store player's forward vector if provided
        if player_forward is not None:
            self.player_forward = player_forward
        
        # Calculate vector to player
        to_player = player_position - self.position
        distance_to_player = np.linalg.norm(to_player)
        
        # Check if player is looking at pirate
        player_can_see_pirate = True
        if self.player_forward is not None:
            # Normalize direction to player
            direction_to_pirate = to_player / distance_to_player if distance_to_player > 0 else np.zeros(3)
            
            # If dot product is negative, player is facing away from pirate
            dot_product = np.dot(self.player_forward, direction_to_pirate)
            player_can_see_pirate = dot_product > 0
        
        # Only chase if within chase distance AND player is looking at pirate
        if distance_to_player < self.chase_distance and player_can_see_pirate:
            self.is_patrolling = False
            
            # Normalize the direction vector
            if distance_to_player > 0:
                direction = to_player / distance_to_player
            else:
                direction = np.array([1.0, 0.0, 0.0], dtype=np.float32)
            
            # Calculate an interception angle (30-60 degrees from direct approach)
            # This creates a flanking behavior rather than direct following
            intercept_angle = np.random.uniform(np.pi/6, np.pi/3)  # 30-60 degrees
            
            # Randomly choose left or right interception
            if np.random.random() > 0.5:
                intercept_angle = -intercept_angle
                
            # Create rotation matrix for the interception angle around Y axis
            cos_angle = np.cos(intercept_angle)
            sin_angle = np.sin(intercept_angle)
            rot_matrix = np.array([
                [cos_angle, 0, sin_angle],
                [0, 1, 0],
                [-sin_angle, 0, cos_angle]
            ])
            
            # Rotate the direction vector by the interception angle
            approach_direction = rot_matrix @ direction
                    
            # Move toward player with adjusted direction
            self.velocity = approach_direction * self.speed
            
            # Gradually rotate to face the intercept direction
            target_rotation = np.arctan2(approach_direction[2], approach_direction[0])
            current_rotation = self.rotation[1]
            
            # Calculate shortest angle difference
            angle_diff = (target_rotation - current_rotation + np.pi) % (2 * np.pi) - np.pi
            
            # Gradually rotate toward the target
            rotation_step = self.rotation_speed * delta_time
            if abs(angle_diff) > rotation_step:
                if angle_diff > 0:
                    self.rotation[1] += rotation_step
                else:
                    self.rotation[1] -= rotation_step
            else:
                self.rotation[1] = target_rotation
        else:
            # Start or continue patrolling in random directions
            self.is_patrolling = True
            self.patrol(delta_time)
        
        # Call parent update to handle movement
        super().update(delta_time)
    
    def patrol(self, delta_time):
        """Handle random patrol movement when not chasing player."""
        # Update direction change timer
        self.time_since_direction_change += delta_time
        
        # Change direction periodically or when hitting world boundaries
        if self.time_since_direction_change >= self.direction_change_time:
            self.patrol_direction = self.generate_random_direction()
            self.time_since_direction_change = 0.0
            self.direction_change_time = random.uniform(3.0, 8.0)  # Randomize next change time
        
        # Check if pirate is near world boundaries and change direction if needed
        world_boundary = 4800  # Slightly inside the world bounds to avoid getting stuck
        for i in range(3):
            if abs(self.position[i]) > world_boundary:
                # Change direction away from the boundary
                self.patrol_direction[i] = -np.sign(self.position[i]) * abs(self.patrol_direction[i])
                self.time_since_direction_change = 0.0
        
        # Set velocity for patrol movement
        self.velocity = self.patrol_direction * self.patrol_speed
        
        # Gradually rotate to face the patrol direction
        target_rotation = np.arctan2(self.patrol_direction[2], self.patrol_direction[0])
        current_rotation = self.rotation[1]
        
        # Calculate shortest angle difference
        angle_diff = (target_rotation - current_rotation + np.pi) % (2 * np.pi) - np.pi
        
        # Gradually rotate toward the target direction
        rotation_step = (self.rotation_speed * 0.5) * delta_time  # Slower rotation when patrolling
        if abs(angle_diff) > rotation_step:
            if angle_diff > 0:
                self.rotation[1] += rotation_step
            else:
                self.rotation[1] -= rotation_step
        else:
            self.rotation[1] = target_rotation
    
    def take_damage(self, amount):
        self.health -= amount
        return self.health <= 0

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
    def __init__(self, target_object=None, color=None):
        model_path = os.path.join('assets', 'objects', 'models', 'arrow.obj')
        # Increase scale to make the arrow much larger
        super().__init__(model_path, scale=30.0)
        
        # Store target object to point to
        self.target_object = target_object
        
        # Make the arrow a very bright color for visibility
        if color is not None:
            self.set_color(color)
        else:
            # Very bright green
            self.set_color(np.array([0.0, 2.0, 0.0, 1.0], dtype=np.float32))
        
        # Position minimap arrow farther above player for better visibility
        self.offset = np.array([0.0, 50.0, 0.0], dtype=np.float32)
        # Increase max distance to always show the arrow
        self.max_distance = 10000.0  # Much larger range
        self.min_distance = 10.0     # Smaller min distance
        
        # Add rotation to make arrow point downward initially
        self.initial_rotation = np.array([np.pi/2, 0.0, 0.0], dtype=np.float32)
        self.set_rotation(self.initial_rotation)

    def update(self, player_position, player_rotation, player_directions):
        if self.target_object is None:
            return
        
        # Calculate vector to target
        to_target = self.target_object.position - player_position
        distance = np.linalg.norm(to_target)
        
        # Only hide when extremely close
        if distance < self.min_distance:
            self.set_position(np.array([10000, 10000, 10000], dtype=np.float32))
            return

        # Always position arrow directly above player
        arrow_position = player_position + np.array([0.0, self.offset[1], 0.0], dtype=np.float32)
        self.set_position(arrow_position)
        
        # Make arrow point toward target
        direction = to_target / distance if distance > 0 else np.array([1, 0, 0], dtype=np.float32)
        
        # Calculate rotations - add a constant offset to pitch to make it point down more
        yaw = np.arctan2(direction[0], direction[2])
        pitch = np.arcsin(-direction[1]) + np.pi/4  # Point down more
        
        # Apply rotations
        self.set_rotation(np.array([pitch, yaw, 0.0], dtype=np.float32))
        
        # Set a fixed large scale regardless of distance
        self.graphics_obj.properties['scale'] = np.array([30.0, 30.0, 30.0], dtype=np.float32)

class Crosshair(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'crosshair.obj')
        super().__init__(model_path, scale=0.1)

class Laser(GameObject):
    def __init__(self):
        model_path = os.path.join('assets', 'objects', 'models', 'planet.obj')
        super().__init__(model_path, scale=5, shader=laser_shader)
        
        # Set laser color (bright green)
        self.set_color(np.array([1, 0, 0.3, 1.0], dtype=np.float32))
        
        # Laser properties
        self.lifetime = 5.0  # Seconds before disappearing
        self.time_alive = 0.0
        self.speed =10000

        
    def update(self, delta_time):
        # Update position based on velocity
        super().update(delta_time)
        
        # Track lifetime
        self.time_alive += delta_time
        
        # Return True if the laser should be removed
        return self.time_alive >= self.lifetime
        
###############################################################

# Write logic to load OBJ Files:

# Will depend on type of object. For example if normals needed along with vertex positions

# then will need to load slightly differently.

# Can use the provided OBJ files from assignment_2_template/assets/objects/models/

# Can also download other assets or model yourself in modelling softwares like blender

###############################################################

# Create Transporter, Pirates, Stars(optional), Minimap arrow, crosshair, planet, spacestation, laser

###############################################################