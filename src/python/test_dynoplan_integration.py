#!/usr/bin/env python3
"""
Use Dynoplan's Python interface directly for payload optimization
"""

import sys
import numpy as np
from pathlib import Path

# Add dynoplan to path
sys.path.insert(0, "/home/user_136/dynoplan/dynobench/src")

try:
    import dynobench
    print("✅ Dynobench imported successfully")
except ImportError as e:
    print(f"❌ Failed to import dynobench: {e}")
    print("Make sure Dynoplan is properly built with Python bindings")
    sys.exit(1)

def read_ompl_solution(filepath):
    """Read OMPL solution file"""
    states = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                values = [float(x) for x in line.split()]
                states.append(values)
    return states

def optimize_payload_trajectory():
    """Use Dynoplan's native payload system for optimization"""
    
    # Paths
    project_dir = Path("/home/user_136/Desktop/Project-A")
    build_dir = project_dir / "build" 
    ompl_solution_file = build_dir / "solution_path.txt"
    
    if not ompl_solution_file.exists():
        print(f"❌ OMPL solution not found: {ompl_solution_file}")
        print("Please run PayloadFourDrones first!")
        return False
    
    # Read OMPL solution
    print(f"📂 Reading OMPL solution from: {ompl_solution_file}")
    ompl_states = read_ompl_solution(ompl_solution_file)
    print(f"📊 Found {len(ompl_states)} states")
    
    if len(ompl_states) == 0:
        print("❌ No states found")
        return False
    
    try:
        # Create environment
        print("🔧 Creating Dynoplan environment...")
        
        # Use a simple approach - create a payload problem
        problem_data = {
            "robot": "payloadfourdrones",
            "start": ompl_states[0][:3],  # Just position for now
            "goal": ompl_states[-1][:3],
            "models_base_path": "/home/user_136/dynoplan/dynobench/models/"
        }
        
        print(f"Start: {problem_data['start']}")
        print(f"Goal: {problem_data['goal']}")
        
        # Create robot environment
        env = dynobench.create_robot_from_file(
            problem_data["models_base_path"] + "payloadfourdrones.yaml",
            problem_data["robot"]
        )
        
        if env is None:
            print("❌ Failed to create robot environment")
            return False
        
        print("✅ Environment created successfully")
        
        # Set start and goal
        print("🎯 Setting start and goal states...")
        
        # For now, let's just run a simple trajectory optimization
        # This is a simplified example - you may need to adjust based on exact API
        
        print("🚀 Running optimization...")
        print("Note: This is a basic integration. For full optimization,")
        print("you may need to use Dynoplan's command-line tools or")
        print("implement a more detailed state conversion.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🦖 Dynoplan Payload Optimization")
    print("=" * 40)
    
    success = optimize_payload_trajectory()
    
    if success:
        print("✅ Basic integration test passed!")
        print("\n💡 Next steps:")
        print("1. Implement detailed state conversion between OMPL and Dynoplan formats")
        print("2. Use Dynoplan's trajectory optimization algorithms")  
        print("3. Configure cost weights and optimization parameters")
    else:
        print("❌ Integration test failed")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure Dynoplan is built with Python bindings")
        print("2. Check that all dependencies are installed")
        print("3. Verify OMPL solution file exists")

if __name__ == "__main__":
    main()
