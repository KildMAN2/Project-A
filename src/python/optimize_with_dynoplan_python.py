#!/usr/bin/env python3
"""
Simple Python interface to Dynoplan for trajectory optimization
"""

import sys
import os
import numpy as np
import yaml
import json

# Add Dynoplan Python path
sys.path.append('/home/user_136/dynoplan/build')
sys.path.append('/home/user_136/dynoplan/dynobench')

try:
    import pydynobench
    print("Successfully imported pydynobench")
except ImportError as e:
    print(f"Failed to import pydynobench: {e}")
    print("Falling back to direct trajectory smoothing...")

def load_ompl_solution(solution_file):
    """Load OMPL solution from file"""
    states = []
    with open(solution_file, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                # Parse each line as a state
                parts = line.strip().split()
                if len(parts) >= 13:  # Minimum expected state size
                    state = [float(x) for x in parts[:13]]
                    states.append(state)
    return np.array(states)

def simple_trajectory_smoothing(states, iterations=10):
    """Apply simple smoothing to trajectory"""
    if len(states) < 3:
        return states
    
    smoothed = states.copy()
    
    for _ in range(iterations):
        for i in range(1, len(smoothed) - 1):
            # Simple averaging with neighbors
            alpha = 0.1  # Smoothing factor
            smoothed[i] = (1 - 2*alpha) * smoothed[i] + alpha * smoothed[i-1] + alpha * smoothed[i+1]
    
    return smoothed

def convert_to_dynoplan_format(states, dt=0.1):
    """Convert trajectory to Dynoplan-compatible format"""
    trajectory = []
    
    for i, state in enumerate(states):
        # Convert state to Dynoplan format
        if len(state) >= 13:
            # Standard quad format: [x,y,z, qx,qy,qz,qw, vx,vy,vz, wx,wy,wz]
            trajectory_point = {
                'time': i * dt,
                'state': state.tolist(),
                'control': [0.0, 0.0, 0.0, 9.81]  # Basic hover control
            }
        else:
            # Fallback format
            trajectory_point = {
                'time': i * dt,
                'state': state.tolist(),
                'control': [0.0] * 4
            }
        
        trajectory.append(trajectory_point)
    
    return trajectory

def optimize_trajectory_simple(input_file, output_file):
    """Simple trajectory optimization without full Dynoplan"""
    print(f"Loading trajectory from {input_file}")
    
    # Load OMPL solution
    states = load_ompl_solution(input_file)
    print(f"Loaded {len(states)} states")
    
    if len(states) == 0:
        print("No states found in input file")
        return False
    
    # Apply smoothing
    print("Applying trajectory smoothing...")
    smoothed_states = simple_trajectory_smoothing(states)
    
    # Convert to Dynoplan format
    trajectory = convert_to_dynoplan_format(smoothed_states)
    
    # Create output structure
    output_data = {
        'name': 'optimized_payload_trajectory',
        'robot_type': 'quad3d_v0',
        'trajectory': trajectory,
        'total_time': len(trajectory) * 0.1,
        'cost': np.sum(np.linalg.norm(np.diff(smoothed_states[:, :3], axis=0), axis=1)),
        'optimization_method': 'simple_smoothing'
    }
    
    # Save optimized trajectory
    with open(output_file, 'w') as f:
        yaml.dump(output_data, f, default_flow_style=False)
    
    print(f"Optimized trajectory saved to {output_file}")
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python optimize_with_dynoplan_python.py <input_solution> <output_trajectory>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found")
        sys.exit(1)
    
    success = optimize_trajectory_simple(input_file, output_file)
    
    if success:
        print("Trajectory optimization completed successfully!")
    else:
        print("Trajectory optimization failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
