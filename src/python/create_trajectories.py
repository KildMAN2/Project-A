#!/usr/bin/env python3
"""
Create Different Trajectory Files for Multi-Objective Testing
============================================================

Creates several different trajectory files with different complexities,
then tests all optimization objectives on each one.
"""

import numpy as np
from pathlib import Path

def create_trajectory_file(name: str, waypoints: list, workspace_path: str):
    """Create a trajectory file with given waypoints"""
    build_path = Path(workspace_path) / "build"
    txt_dir = build_path / "txt"
    txt_dir.mkdir(exist_ok=True)
    file_path = txt_dir / f"trajectory_{name}.txt"
    
    with open(file_path, 'w') as f:
        for i, waypoint in enumerate(waypoints):
            # Format: x y z (3D position for each waypoint)
            f.write(f"{waypoint[0]:.6f} {waypoint[1]:.6f} {waypoint[2]:.6f}\n")
    
    print(f"Created trajectory: {file_path} ({len(waypoints)} waypoints)")
    return str(file_path)

def generate_different_trajectories(workspace_path: str):
    """Generate various trajectory files with different characteristics"""
    
    print("🎨 Creating Different Trajectory Files")
    print("=" * 50)
    
    trajectory_files = {}
    
    # 1. Simple straight line (minimal optimization potential)
    simple_waypoints = [
        [-10.0, -20.0, 20.0],  # Start
        [10.0, 20.0, 25.0]     # Goal
    ]
    trajectory_files["simple"] = create_trajectory_file("simple", simple_waypoints, workspace_path)
    
    # 2. Short zigzag path (moderate optimization potential)
    zigzag_waypoints = [
        [-15.0, -25.0, 20.0],
        [-5.0, -15.0, 22.0],
        [5.0, -5.0, 24.0],
        [15.0, 5.0, 26.0],
        [25.0, 15.0, 28.0]
    ]
    trajectory_files["zigzag"] = create_trajectory_file("zigzag", zigzag_waypoints, workspace_path)
    
    # 3. Complex detour (high optimization potential)
    detour_waypoints = [
        [-20.0, -30.0, 20.0],  # Start
        [-15.0, -25.0, 21.0],
        [-10.0, -20.0, 22.0],
        [-5.0, -10.0, 23.0],
        [0.0, 0.0, 24.0],      # Middle waypoint
        [5.0, 10.0, 25.0],
        [10.0, 20.0, 26.0],
        [15.0, 25.0, 27.0],
        [20.0, 30.0, 28.0]     # Goal
    ]
    trajectory_files["detour"] = create_trajectory_file("detour", detour_waypoints, workspace_path)
    
    # 4. Vertical climb (altitude optimization)
    climb_waypoints = [
        [0.0, 0.0, 15.0],      # Start low
        [2.0, 2.0, 20.0],
        [4.0, 4.0, 25.0],
        [6.0, 6.0, 30.0],
        [8.0, 8.0, 35.0],
        [10.0, 10.0, 40.0]     # End high
    ]
    trajectory_files["climb"] = create_trajectory_file("climb", climb_waypoints, workspace_path)
    
    # 5. Dense waypoint path (compression potential)
    dense_waypoints = []
    for i in range(20):
        t = i / 19.0  # Parameter from 0 to 1
        x = -20.0 + 40.0 * t
        y = -20.0 + 40.0 * t + 10.0 * np.sin(2 * np.pi * t * 3)  # Sinusoidal path
        z = 20.0 + 10.0 * t
        dense_waypoints.append([x, y, z])
    trajectory_files["dense"] = create_trajectory_file("dense", dense_waypoints, workspace_path)
    
    # 6. Original OMPL trajectory (for comparison)
    original_path = Path(workspace_path) / "solution_path.txt"
    if original_path.exists():
        trajectory_files["original"] = str(original_path)
        print(f"Using original trajectory: {original_path}")
    
    print(f"\n✅ Created {len(trajectory_files)} different trajectory files")
    return trajectory_files

if __name__ == "__main__":
    workspace = "/home/user_136/Desktop/Project-A"
    generate_different_trajectories(workspace)
