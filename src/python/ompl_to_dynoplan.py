#!/usr/bin/env python3
"""
Convert OMPL PayloadFourDrones solution to Dynoplan format for optimization
"""

import numpy as np
import json
import yaml
import sys
from pathlib import Path

# Add dynoplan to path
sys.path.insert(0, "/home/user_136/dynoplan/dynobench/src")

import dynobench.robots.payload as payload_module
from dynobench.planners.trajectory_optimization import TrajectoryOptimizer
from dynobench.planners.utils import save_result_to_yaml

def read_ompl_solution(filepath):
    """Read OMPL solution file and parse states"""
    states = []
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Parse the state values
                values = [float(x) for x in line.split()]
                states.append(values)
    
    return np.array(states)

def convert_ompl_to_dynoplan_format(ompl_states, dt=0.1):
    """
    Convert OMPL states to Dynoplan trajectory format
    
    OMPL PayloadFourDrones state format:
    - Payload: position (3), quaternion (4), velocity (3), angular_velocity (3) = 13
    - Per drone: quaternion (4), angular_velocity (3), cable_angles (2), cable_velocities (2) = 11
    - Total: 13 + 4*11 = 57 states
    
    Dynoplan PayloadFourDrones format may be different - need to check
    """
    
    trajectory = {
        'states': [],
        'controls': [],
        'times': [],
        'dt': dt
    }
    
    for i, state in enumerate(ompl_states):
        # Extract payload state (first 13 elements)
        payload_pos = state[0:3]      # x, y, z
        payload_quat = state[3:7]     # qx, qy, qz, qw
        payload_vel = state[7:10]     # vx, vy, vz
        payload_omega = state[10:13]  # wx, wy, wz
        
        # For Dynoplan, we might need to reformat this
        # This is a simplified conversion - you may need to adjust based on exact format
        dyno_state = np.concatenate([
            payload_pos,
            payload_quat,
            payload_vel,
            payload_omega
        ])
        
        trajectory['states'].append(dyno_state.tolist())
        trajectory['times'].append(i * dt)
        
        # For controls, we can use zero or estimate from state differences
        if i < len(ompl_states) - 1:
            # Estimate control (simplified)
            control = np.zeros(16)  # 4 drones * 4 controls each (thrust + 3 torques)
            trajectory['controls'].append(control.tolist())
    
    return trajectory

def optimize_with_dynoplan(trajectory_data, output_file="optimized_payload.yaml"):
    """Use Dynoplan to optimize the trajectory"""
    
    # Create environment
    env = payload_module.PayloadFourDrones()
    
    # Set start and goal from trajectory
    if len(trajectory_data['states']) > 0:
        start_state = trajectory_data['states'][0]
        goal_state = trajectory_data['states'][-1]
        
        # Set environment start/goal (adjust indices as needed)
        env.start = start_state[:7]  # position + quaternion
        env.goal = goal_state[:7]
    
    # Create trajectory optimizer
    optimizer = TrajectoryOptimizer(env)
    
    # Set initial guess from OMPL solution
    optimizer.set_initial_trajectory(
        states=trajectory_data['states'],
        controls=trajectory_data['controls'],
        dt=trajectory_data['dt']
    )
    
    # Run optimization
    print("🚀 Running Dynoplan trajectory optimization...")
    result = optimizer.optimize()
    
    if result.success:
        print("✅ Optimization successful!")
        save_result_to_yaml(result, output_file)
        print(f"💾 Optimized trajectory saved to {output_file}")
        return result
    else:
        print("❌ Optimization failed")
        return None

def main():
    # Paths
    build_dir = Path("/home/user_136/Desktop/Project-A/build")
    ompl_solution_file = build_dir / "solution_path.txt"
    
    if not ompl_solution_file.exists():
        print(f"❌ OMPL solution file not found: {ompl_solution_file}")
        print("Please run your PayloadFourDrones planner first!")
        return
    
    print(f"📂 Reading OMPL solution from: {ompl_solution_file}")
    
    # Read and convert OMPL solution
    ompl_states = read_ompl_solution(ompl_solution_file)
    print(f"📊 Found {len(ompl_states)} states in OMPL solution")
    
    # Convert to Dynoplan format
    trajectory = convert_ompl_to_dynoplan_format(ompl_states)
    
    # Optimize with Dynoplan
    result = optimize_with_dynoplan(trajectory, "optimized_payload_trajectory.yaml")
    
    if result:
        print("🎉 Successfully optimized trajectory with Dynoplan!")
    else:
        print("⚠️  Optimization failed, but conversion completed")

if __name__ == "__main__":
    main()
