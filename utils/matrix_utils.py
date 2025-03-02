import numpy as np

def rotation_matrix(rx, ry, rz):
    """Create a rotation matrix from Euler angles (in radians)"""
    cx, cy, cz = np.cos([rx, ry, rz])
    sx, sy, sz = np.sin([rx, ry, rz])
    
    # Rotation matrices for each axis
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    
    # Combined rotation matrix (ZYX order)
    return Rz @ Ry @ Rx

def euler_to_matrix(euler):
    """Convert Euler angles (roll, pitch, yaw) to rotation matrix."""
    return rotation_matrix(euler[0], euler[1], euler[2])
    
def matrix_to_euler(R):
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
