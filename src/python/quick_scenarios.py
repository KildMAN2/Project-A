#!/usr/bin/env python3
"""
Quick Different Scenarios Generator
==================================

Creates trajectories with different characteristics by varying:
- Path length
- Direction changes  
- Altitude variations
- Complexity levels
"""

import numpy as np
from pathlib import Path

def create_trajectory(name: str, waypoints: list, workspace_path: str):
    """Create a trajectory file with specific waypoints"""
    
    build_path = Path(workspace_path) / "build"
    solution_file = build_path / f"solution_{name}.txt"
    
    with open(solution_file, 'w') as f:
        for waypoint in waypoints:
            # OMPL format: position + 54 zeros for other states
            line = f"{waypoint[0]} {waypoint[1]} {waypoint[2]}" + " 0.0" * 54
            f.write(line + "\n")
    
    print(f"✅ Created {name}: {len(waypoints)} waypoints")
    return str(solution_file)

def main():
    workspace = "/home/user_136/Desktop/Project-A"
    
    print("🎯 Creating Quick Different Scenarios")
    print("=" * 50)
    
    # 1. Simple straight line
    simple_waypoints = [
        [-10, -10, 20],
        [10, 10, 25]
    ]
    create_trajectory("simple_line", simple_waypoints, workspace)
    
    # 2. Complex zigzag path
    zigzag_waypoints = [
        [-30, -30, 20],
        [-15, -10, 22],
        [0, -30, 25],
        [15, -10, 28],
        [30, -30, 30],
        [15, 10, 32],
        [0, 30, 28],
        [-15, 10, 25],
        [-30, 30, 22]
    ]
    create_trajectory("complex_zigzag", zigzag_waypoints, workspace)
    
    # 3. Steep climb
    climb_waypoints = [
        [0, 0, 15],
        [5, 5, 25],
        [10, 10, 35],
        [15, 15, 45]
    ]
    create_trajectory("steep_climb", climb_waypoints, workspace)
    
    # 4. Long horizontal path
    long_waypoints = [
        [-50, 0, 25],
        [-30, 5, 25],
        [-10, -3, 25],
        [10, 7, 25],
        [30, -2, 25],
        [50, 0, 25]
    ]
    create_trajectory("long_horizontal", long_waypoints, workspace)
    
    # 5. Spiral path
    spiral_waypoints = []
    for i in range(8):
        angle = i * np.pi / 4
        radius = 5 + i * 2
        x = radius * np.cos(angle)
        y = radius * np.sin(angle) 
        z = 20 + i * 2
        spiral_waypoints.append([x, y, z])
    create_trajectory("spiral_path", spiral_waypoints, workspace)
    
    print(f"\n🚀 Now test each scenario:")
    print(f"   python3 trajectory_optimizer.py --input build/solution_simple_line.txt --ultra")
    print(f"   python3 trajectory_optimizer.py --input build/solution_complex_zigzag.txt --advanced") 
    print(f"   python3 trajectory_optimizer.py --input build/solution_steep_climb.txt --advanced")
    print(f"   python3 trajectory_optimizer.py --input build/solution_long_horizontal.txt --ultra")
    print(f"   python3 trajectory_optimizer.py --input build/solution_spiral_path.txt --advanced")

if __name__ == "__main__":
    main()
