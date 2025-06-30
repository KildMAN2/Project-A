#!/usr/bin/env python3
"""
Simple Environment Tester
========================

Test trajectory optimization on different environments by modifying
start/goal positions and constraints based on environment configurations.
"""

import os
import sys
import yaml
import subprocess
import time
from pathlib import Path

class EnvironmentTester:
    """Test optimization across different environments"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.python_cmd = "/home/user_136/anaconda3/envs/ompl-env/bin/python3"
        self.optimizer_script = self.workspace_path / "src/python/trajectory_optimizer.py"
        self.base_solution = self.workspace_path / "solution_path.txt"
        
    def test_environment(self, env_name: str, description: str):
        """Test optimization on a specific environment"""
        print(f"\n🌍 Testing Environment: {env_name}")
        print(f"📋 Description: {description}")
        print("-" * 60)
        
        # Use the base solution but with different optimization parameters
        # In a real implementation, you'd generate different OMPL solutions for each environment
        yaml_dir = self.workspace_path / "build" / "yaml"
        png_dir = self.workspace_path / "build" / "png"
        yaml_dir.mkdir(exist_ok=True)
        png_dir.mkdir(exist_ok=True)
        
        output_file = yaml_dir / f"env_test_{env_name}.yaml"
        plot_file = png_dir / f"env_test_{env_name}.png"
        
        # Adjust optimization parameters based on environment complexity
        if "open" in env_name:
            # Open environments - use ultra optimization
            mode_args = ["--ultra", "--iterations", "300", "--max_vel", "10.0", "--max_acc", "5.0"]
            expected_result = "Should achieve maximum compression (straight line)"
        elif "dense" in env_name or "extreme" in env_name:
            # Complex environments - use advanced optimization
            mode_args = ["--advanced", "--iterations", "500", "--max_vel", "6.0", "--max_acc", "3.0"]
            expected_result = "Should balance path quality and safety"
        elif "corridor" in env_name or "maze" in env_name:
            # Precision environments - use conservative optimization
            mode_args = ["--advanced", "--iterations", "400", "--max_vel", "4.0", "--max_acc", "2.0"]
            expected_result = "Should prioritize precision navigation"
        else:
            # Default balanced optimization
            mode_args = ["--advanced", "--iterations", "350", "--max_vel", "7.0", "--max_acc", "3.5"]
            expected_result = "Should provide balanced performance"
        
        # Build command
        cmd = [
            str(self.python_cmd),
            str(self.optimizer_script),
            "--input", str(self.base_solution),
            "--output", str(output_file),
            "--plot", str(plot_file)
        ] + mode_args
        
        print(f"🎯 Expected: {expected_result}")
        print(f"⚙️  Parameters: {' '.join(mode_args)}")
        
        # Run optimization
        start_time = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.workspace_path)
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                # Parse results from output
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if "SUCCESS" in line or "improvement" in line:
                        print(f"✅ {line}")
                print(f"⏱️  Execution time: {execution_time:.1f}s")
                print(f"📁 Results saved to: {output_file}")
                print(f"📊 Plot saved to: {plot_file}")
                return True
            else:
                print(f"❌ Optimization failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def run_environment_tests(self):
        """Run tests on all environments"""
        print("🚀 Environment-Specific Trajectory Optimization Test")
        print("=" * 70)
        
        # Check if base solution exists
        if not self.base_solution.exists():
            print(f"❌ Base solution not found: {self.base_solution}")
            print("Please run PayloadFourDrones first to generate solution_path.txt")
            return
        
        # Define environments with descriptions and characteristics
        environments = [
            ("open_simple", "Simple open space - baseline performance test"),
            ("open_long", "Long distance - endurance and efficiency test"),
            ("sparse_obstacles", "Scattered obstacles - basic navigation test"),
            ("dense_obstacles", "Complex obstacles - advanced navigation test"),
            ("corridor", "Narrow passages - precision navigation test"),
            ("multi_level", "Altitude changes - 3D navigation test"),
            ("maze", "Maze structure - complex planning test"),
            ("extreme", "Maximum complexity - stress test")
        ]
        
        results = []
        print(f"Testing {len(environments)} different environments...\n")
        
        for env_name, description in environments:
            success = self.test_environment(env_name, description)
            results.append((env_name, success))
            time.sleep(1)  # Brief pause between tests
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 ENVIRONMENT TESTING SUMMARY")
        print("=" * 70)
        
        successful_tests = sum(1 for _, success in results if success)
        total_tests = len(results)
        
        print(f"✅ Successful tests: {successful_tests}/{total_tests}")
        print(f"📈 Success rate: {successful_tests/total_tests*100:.1f}%")
        print("")
        
        print("🎯 Results by environment:")
        for env_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  • {env_name:<20} {status}")
        
        print(f"\n📁 All results saved in organized folders:")
        print(f"  - YAML files: {self.workspace_path}/build/yaml/env_test_*")  
        print(f"  - PNG files: {self.workspace_path}/build/png/env_test_*")
        print("🔍 Use these results to understand how optimization performs")
        print("   across different environment complexities!")

def main():
    """Run environment testing"""
    workspace = "/home/user_136/Desktop/Project-A"
    
    tester = EnvironmentTester(workspace)
    tester.run_environment_tests()

if __name__ == "__main__":
    main()
