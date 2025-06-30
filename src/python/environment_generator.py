#!/usr/bin/env python3
"""
Environment Generator for Multi-Scenario Testing
===============================================

Creates different OMPL environments with various obstacle configurations
to test trajectory optimization across diverse scenarios.
"""

import os
import yaml
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple

class EnvironmentGenerator:
    """Generate different environments for trajectory optimization testing"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.build_path = self.workspace_path / "build"
        
    def create_environment_config(self, scenario_name: str, start_pos: List[float], 
                                goal_pos: List[float], obstacles: List[Dict] = None) -> str:
        """Create environment configuration file"""
        
        # Extend positions to full state (position + quaternion + velocities + drone states)
        full_start = start_pos + [0.0, 0.0, 0.0, 1.0] + [0.0] * 49  # Total 57 states
        full_goal = goal_pos + [0.0, 0.0, 0.0, 1.0] + [0.0] * 49   # Total 57 states
        
        config = {
            "type": "PayloadFourDrones",
            "model": "payload4drones",
            "start": full_start,
            "goal": full_goal,
            "dt": 0.1,
            "T": 200,  # Extended time for complex scenarios
            "integrator": "euler",
            "dynamics": True
        }
        
        if obstacles:
            config["obstacles"] = obstacles
            
        # Save configuration to organized folder
        yaml_dir = self.build_path / "yaml"
        yaml_dir.mkdir(exist_ok=True)
        config_file = yaml_dir / f"env_{scenario_name}.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
            
        return str(config_file)
    
    def generate_all_environments(self) -> Dict[str, str]:
        """Generate all test environments"""
        environments = {}
        
        print("🌍 Generating test environments...")
        
        # 1. Open Space - Simple
        environments["open_simple"] = self.create_environment_config(
            "open_simple",
            start_pos=[-10.0, -20.0, 20.0],
            goal_pos=[10.0, 20.0, 25.0],
            obstacles=[]
        )
        print("  ✅ Open space (simple)")
        
        # 2. Open Space - Long Distance
        environments["open_long"] = self.create_environment_config(
            "open_long", 
            start_pos=[-40.0, -40.0, 15.0],
            goal_pos=[40.0, 40.0, 35.0],
            obstacles=[]
        )
        print("  ✅ Open space (long distance)")
        
        # 3. Sparse Obstacles
        environments["sparse_obstacles"] = self.create_environment_config(
            "sparse_obstacles",
            start_pos=[-25.0, -30.0, 20.0],
            goal_pos=[25.0, 30.0, 30.0],
            obstacles=[
                {"type": "cylinder", "center": [0, -10, 25], "radius": 6, "height": 15},
                {"type": "cylinder", "center": [10, 10, 25], "radius": 4, "height": 20},
                {"type": "cylinder", "center": [-10, 5, 25], "radius": 5, "height": 18}
            ]
        )
        print("  ✅ Sparse obstacles")
        
        # 4. Dense Obstacles  
        environments["dense_obstacles"] = self.create_environment_config(
            "dense_obstacles",
            start_pos=[-30.0, -35.0, 20.0],
            goal_pos=[30.0, 35.0, 30.0],
            obstacles=[
                {"type": "cylinder", "center": [-15, -20, 25], "radius": 3, "height": 12},
                {"type": "cylinder", "center": [-5, -15, 25], "radius": 4, "height": 16},
                {"type": "cylinder", "center": [5, -10, 25], "radius": 3, "height": 14},
                {"type": "cylinder", "center": [15, -5, 25], "radius": 5, "height": 18},
                {"type": "cylinder", "center": [20, 5, 25], "radius": 3, "height": 15},
                {"type": "cylinder", "center": [10, 15, 25], "radius": 4, "height": 17},
                {"type": "cylinder", "center": [0, 20, 25], "radius": 3, "height": 13},
                {"type": "cylinder", "center": [-10, 10, 25], "radius": 4, "height": 16},
                {"type": "cylinder", "center": [-20, 0, 25], "radius": 3, "height": 14}
            ]
        )
        print("  ✅ Dense obstacles")
        
        # 5. Corridor Navigation
        environments["corridor"] = self.create_environment_config(
            "corridor",
            start_pos=[-35.0, 0.0, 25.0],
            goal_pos=[35.0, 0.0, 25.0],
            obstacles=[
                # Create narrow corridor
                {"type": "box", "center": [0, -15, 25], "size": [50, 3, 15]},
                {"type": "box", "center": [0, 15, 25], "size": [50, 3, 15]},
                # Add some obstacles in corridor
                {"type": "cylinder", "center": [-10, 0, 25], "radius": 2, "height": 10},
                {"type": "cylinder", "center": [10, 0, 25], "radius": 2, "height": 10}
            ]
        )
        print("  ✅ Corridor navigation")
        
        # 6. Multi-Level 
        environments["multi_level"] = self.create_environment_config(
            "multi_level",
            start_pos=[-25.0, -25.0, 15.0],
            goal_pos=[25.0, 25.0, 40.0],
            obstacles=[
                {"type": "cylinder", "center": [0, 0, 20], "radius": 8, "height": 12},
                {"type": "cylinder", "center": [-10, 10, 30], "radius": 5, "height": 10},
                {"type": "cylinder", "center": [10, -10, 35], "radius": 6, "height": 8}
            ]
        )
        print("  ✅ Multi-level navigation")
        
        # 7. Maze-like Environment
        environments["maze"] = self.create_environment_config(
            "maze",
            start_pos=[-30.0, -30.0, 25.0],
            goal_pos=[30.0, 30.0, 25.0],
            obstacles=[
                # Create maze-like structure
                {"type": "box", "center": [-15, 0, 25], "size": [3, 40, 15]},
                {"type": "box", "center": [15, 0, 25], "size": [3, 40, 15]},
                {"type": "box", "center": [0, -15, 25], "size": [40, 3, 15]},
                {"type": "box", "center": [0, 15, 25], "size": [40, 3, 15]},
                # Add internal obstacles
                {"type": "cylinder", "center": [-7, -7, 25], "radius": 3, "height": 12},
                {"type": "cylinder", "center": [7, 7, 25], "radius": 3, "height": 12}
            ]
        )
        print("  ✅ Maze environment")
        
        # 8. Extreme Challenge
        environments["extreme"] = self.create_environment_config(
            "extreme",
            start_pos=[-40.0, -40.0, 15.0],
            goal_pos=[40.0, 40.0, 45.0],
            obstacles=[
                # Multiple layers and types of obstacles
                {"type": "cylinder", "center": [-20, -20, 20], "radius": 4, "height": 12},
                {"type": "cylinder", "center": [-10, -30, 25], "radius": 3, "height": 15},
                {"type": "cylinder", "center": [0, -20, 30], "radius": 5, "height": 10},
                {"type": "cylinder", "center": [10, -10, 25], "radius": 4, "height": 18},
                {"type": "cylinder", "center": [20, 0, 20], "radius": 3, "height": 20},
                {"type": "cylinder", "center": [30, 10, 35], "radius": 6, "height": 8},
                {"type": "cylinder", "center": [20, 20, 30], "radius": 4, "height": 12},
                {"type": "cylinder", "center": [10, 30, 25], "radius": 5, "height": 15},
                {"type": "cylinder", "center": [0, 20, 40], "radius": 3, "height": 10},
                {"type": "cylinder", "center": [-10, 10, 35], "radius": 4, "height": 13},
                {"type": "cylinder", "center": [-20, 0, 25], "radius": 5, "height": 16},
                {"type": "cylinder", "center": [-30, -10, 30], "radius": 3, "height": 14}
            ]
        )
        print("  ✅ Extreme challenge")
        
        print(f"\n🎯 Generated {len(environments)} test environments")
        return environments
    
    def create_environment_summary(self, environments: Dict[str, str]):
        """Create summary of all environments"""
        summary = []
        summary.append("# Test Environments Summary")
        summary.append("=" * 50)
        summary.append("")
        
        env_descriptions = {
            "open_simple": "Simple open space - baseline test",
            "open_long": "Long distance traversal - endurance test", 
            "sparse_obstacles": "Few scattered obstacles - basic navigation",
            "dense_obstacles": "Many obstacles - complex navigation",
            "corridor": "Narrow corridor - precision navigation",
            "multi_level": "Multi-altitude - 3D navigation",
            "maze": "Maze-like structure - planning challenge",
            "extreme": "Maximum complexity - stress test"
        }
        
        summary.append("Available Test Environments:")
        summary.append("")
        
        for env_name, config_path in environments.items():
            description = env_descriptions.get(env_name, "Custom environment")
            summary.append(f"• {env_name:18} - {description}")
            summary.append(f"  Config: {config_path}")
            summary.append("")
        
        summary.append("Usage:")
        summary.append("------")
        summary.append("1. Select environment configuration")
        summary.append("2. Run OMPL planner with the config")
        summary.append("3. Optimize resulting trajectory")
        summary.append("")
        summary.append("Example:")
        summary.append("  ./PayloadFourDrones --config env_sparse_obstacles.yaml")
        summary.append("  python3 trajectory_optimizer.py --input solution.txt")
        
        # Save summary
        summary_file = self.build_path / "environments_summary.txt"
        with open(summary_file, 'w') as f:
            f.write('\n'.join(summary))
        
        print(f"📄 Environment summary saved to: {summary_file}")

def main():
    """Generate all test environments"""
    workspace = "/home/user_136/Desktop/Project-A"
    
    generator = EnvironmentGenerator(workspace)
    environments = generator.generate_all_environments()
    generator.create_environment_summary(environments)
    
    print("\n🚀 All environments ready for testing!")
    print("Use these configurations with your OMPL planner and trajectory optimizer.")

if __name__ == "__main__":
    main()
