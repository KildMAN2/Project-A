#!/usr/bin/env python3
"""
Simple converter from OMPL PayloadFourDrones to Dynoplan format
Uses Dynoplan's command-line tools for optimization
"""

import json
import subprocess
from pathlib import Path
import sys

def read_ompl_solution(filepath):
    """Read OMPL solution file and return list of states"""
    states = []
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                values = [float(x) for x in line.split()]
                states.append(values)
    
    return states

def create_dynoplan_config(states, output_dir):
    """Create Dynoplan configuration files in the expected format"""
    
    if len(states) == 0:
        print("❌ No states found in solution")
        return None, None
    
    # Extract start and goal positions (first 3 elements: x, y, z)
    start_pos = [round(float(x), 6) for x in states[0][:3]]
    goal_pos = [round(float(x), 6) for x in states[-1][:3]]
    
    # Create trajectory YAML in Dynoplan format
    trajectory_data = {
        "cost": 0,
        "feasible": 0,
        "result": {
            "actions": [[1.0, 1.0, 1.0, 1.0] for _ in range(len(states)-1)],  # 4 thrust values
            "states": [[round(float(x), 6) for x in state[:3]] for state in states]  # Only position for now
        }
    }
    
    trajectory_file = output_dir / "trajectory_initial.yaml"
    with open(trajectory_file, 'w') as f:
        import yaml
        yaml.dump(trajectory_data, f, default_flow_style=False)
    
    # Create problem configuration YAML
    problem_config = {
        "environment": {
            "name": "payloadfourdrones_custom",
            "robot_type": "payloadfourdrones",
            "start": start_pos,
            "goal": goal_pos,
            "time_limit": 10.0,
            "delta": 0.1,
            "max_steps": len(states),
            "min": [-50.0, -50.0, 0.0],
            "max": [50.0, 50.0, 30.0]
        }
    }
    
    config_file = output_dir / "problem_config.yaml"
    with open(config_file, 'w') as f:
        import yaml
        yaml.dump(problem_config, f, default_flow_style=False)
    
    return trajectory_file, config_file

def run_dynoplan_optimization(trajectory_file, config_file, output_file, dynoplan_build_dir):
    """Run Dynoplan optimization using command line"""
    
    # Path to Dynoplan's optimization executable
    dynoplan_exe = dynoplan_build_dir / "test" / "main_optimization"
    
    if not dynoplan_exe.exists():
        print(f"❌ Dynoplan executable not found: {dynoplan_exe}")
        print("Trying alternative executables...")
        
        # Try main_tdbastar
        dynoplan_exe = dynoplan_build_dir / "test" / "main_tdbastar"
        if not dynoplan_exe.exists():
            print(f"❌ Alternative executable not found: {dynoplan_exe}")
            return False
    
    # For trajectory optimization, we need different parameters
    cmd = [
        str(dynoplan_exe),
        "-i", str(config_file),  # Input is the problem config
        "-o", str(output_file),
        "--time_limit", "10.0"
    ]
    
    print(f"🚀 Running Dynoplan optimization: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Optimization completed successfully!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Optimization failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    # Configuration
    project_dir = Path("/home/user_136/Desktop/Project-A")
    build_dir = project_dir / "build"
    dynoplan_dir = Path("/home/user_136/dynoplan")
    dynoplan_build_dir = dynoplan_dir / "build"
    
    # Input file
    ompl_solution_file = build_dir / "solution_path.txt"
    
    if not ompl_solution_file.exists():
        print(f"❌ OMPL solution file not found: {ompl_solution_file}")
        print("Please run your PayloadFourDrones planner first!")
        return
    
    print(f"📂 Reading OMPL solution from: {ompl_solution_file}")
    
    # Read OMPL solution
    states = read_ompl_solution(ompl_solution_file)
    print(f"📊 Found {len(states)} states in OMPL solution")
    
    if len(states) == 0:
        print("❌ No valid states found in solution file")
        return
    
    # Create Dynoplan config files
    trajectory_file, config_file = create_dynoplan_config(states, build_dir)
    
    if trajectory_file is None:
        return
    
    print(f"📝 Created trajectory file: {trajectory_file}")
    print(f"📝 Created config file: {config_file}")
    
    # Run optimization
    output_file = build_dir / "optimized_payload_trajectory.json"
    success = run_dynoplan_optimization(
        trajectory_file, 
        config_file, 
        output_file, 
        dynoplan_build_dir
    )
    
    if success:
        print(f"🎉 Optimized trajectory saved to: {output_file}")
    else:
        print("⚠️  Optimization failed, but files were created for manual inspection")

if __name__ == "__main__":
    main()
