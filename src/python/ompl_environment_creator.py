#!/usr/bin/env python3
"""
OMPL Environment Modifier for PayloadFourDrones
==============================================

This script shows you exactly how to create different obstacle environments
and generate different OMPL trajectories for each one.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

class OMPLEnvironmentModifier:
    """Modify OMPL PayloadFourDrones for different environments"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.src_path = self.workspace_path / "src"
        self.build_path = self.workspace_path / "build"
        self.original_demo = self.src_path / "PayloadFourDemo.cpp"
        
    def create_environment_demo(self, env_name: str, start_pos: list, goal_pos: list, 
                              bounds: dict = None, planning_time: float = 10.0) -> str:
        """Create a modified C++ demo file for a specific environment"""
        
        print(f"🛠️  Creating C++ demo for environment: {env_name}")
        
        # Read original demo
        with open(self.original_demo, 'r') as f:
            content = f.read()
        
        # Create modified version
        modified_lines = []
        lines = content.split('\\n')
        
        # Track what we've modified
        modified_start = False
        modified_goal = False
        
        for line in lines:
            # Replace start position
            if 'setStartPosition' in line and not modified_start:
                modified_lines.append(f'    setup.setStartPosition({start_pos[0]}, {start_pos[1]}, {start_pos[2]});')
                modified_start = True
                print(f"   ✏️  Modified start position: {start_pos}")
            # Replace goal position  
            elif 'setGoalPosition' in line and not modified_goal:
                modified_lines.append(f'    setup.setGoalPosition({goal_pos[0]}, {goal_pos[1]}, {goal_pos[2]});')
                modified_goal = True
                print(f"   ✏️  Modified goal position: {goal_pos}")
            else:
                modified_lines.append(line)
        
        # Add bounds modification if specified
        if bounds:
            # Add bounds setting code
            bounds_code = f'''
    // Custom bounds for {env_name} environment
    ompl::base::RealVectorBounds bounds(3);
    bounds.setLow(0, {bounds["low"][0]});
    bounds.setLow(1, {bounds["low"][1]});
    bounds.setLow(2, {bounds["low"][2]});
    bounds.setHigh(0, {bounds["high"][0]});
    bounds.setHigh(1, {bounds["high"][1]});
    bounds.setHigh(2, {bounds["high"][2]});
    setup.getGeometricComponentStateSpace()->as<ompl::base::SE3StateSpace>()->setBounds(bounds);
'''
            # Insert bounds code after setup creation
            for i, line in enumerate(modified_lines):
                if 'payloadSystemSetup(setup)' in line:
                    modified_lines.insert(i + 1, bounds_code)
                    break
        
        # Write modified demo
        modified_demo_file = self.src_path / f"PayloadFourDemo_{env_name}.cpp"
        with open(modified_demo_file, 'w') as f:
            f.write('\\n'.join(modified_lines))
        
        print(f"   ✅ Created: {modified_demo_file}")
        return str(modified_demo_file)
    
    def create_cmake_for_environment(self, env_name: str):
        """Create CMake target for the environment-specific demo"""
        
        cmake_file = self.src_path / "CMakeLists.txt"
        
        # Read existing CMakeLists.txt
        with open(cmake_file, 'r') as f:
            content = f.read()
        
        # Add new executable
        new_target = f'''
# Environment-specific executable for {env_name}
add_executable(PayloadFourDrones_{env_name} PayloadFourDemo_{env_name}.cpp PayloadFourDrones.cpp)
target_link_libraries(PayloadFourDrones_{env_name} ${{OMPL_LIBRARIES}})
'''
        
        # Check if target already exists
        if f"PayloadFourDrones_{env_name}" not in content:
            with open(cmake_file, 'a') as f:
                f.write(new_target)
            print(f"   ✅ Added CMake target for {env_name}")
        else:
            print(f"   ⚠️  CMake target for {env_name} already exists")
    
    def build_environment_executable(self, env_name: str) -> bool:
        """Build the environment-specific executable"""
        
        print(f"🔨 Building executable for environment: {env_name}")
        
        try:
            # Run make for the specific target
            result = subprocess.run(
                ["make", f"PayloadFourDrones_{env_name}"],
                cwd=self.build_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                executable = self.build_path / f"PayloadFourDrones_{env_name}"
                if executable.exists():
                    print(f"   ✅ Built successfully: {executable}")
                    return True
                else:
                    print(f"   ❌ Build succeeded but executable not found")
                    return False
            else:
                print(f"   ❌ Build failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ Build error: {e}")
            return False
    
    def generate_solution_for_environment(self, env_name: str) -> bool:
        """Generate OMPL solution for specific environment"""
        
        print(f"🎯 Generating OMPL solution for: {env_name}")
        
        executable = self.build_path / f"PayloadFourDrones_{env_name}"
        
        if not executable.exists():
            print(f"   ❌ Executable not found: {executable}")
            return False
        
        try:
            # Run the environment-specific executable
            result = subprocess.run(
                [str(executable)],
                cwd=self.build_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Check for solution file
                solution_file = self.build_path / "solution_path.txt"
                if solution_file.exists():
                    # Copy to environment-specific file
                    env_solution = self.build_path / f"solution_ompl_{env_name}.txt"
                    shutil.copy2(solution_file, env_solution)
                    print(f"   ✅ OMPL solution generated: {env_solution}")
                    return True
                else:
                    print(f"   ⚠️  Executable ran but no solution found")
                    return False
            else:
                print(f"   ❌ OMPL execution failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ OMPL timeout (30s)")
            return False
        except Exception as e:
            print(f"   ❌ Execution error: {e}")
            return False
    
    def create_complete_environment(self, env_name: str, start_pos: list, goal_pos: list,
                                  bounds: dict = None, description: str = ""):
        """Create complete environment: modify code, build, and generate solution"""
        
        print(f"\\n🌍 Creating Complete Environment: {env_name}")
        print(f"📋 Description: {description}")
        print("=" * 60)
        
        success_steps = []
        
        # Step 1: Create modified demo
        try:
            self.create_environment_demo(env_name, start_pos, goal_pos, bounds)
            success_steps.append("demo_created")
        except Exception as e:
            print(f"❌ Failed to create demo: {e}")
            return False
        
        # Step 2: Update CMake
        try:
            self.create_cmake_for_environment(env_name)
            success_steps.append("cmake_updated")
        except Exception as e:
            print(f"❌ Failed to update CMake: {e}")
            return False
        
        # Step 3: Build executable
        if self.build_environment_executable(env_name):
            success_steps.append("executable_built")
        else:
            print(f"❌ Failed to build executable")
            return False
        
        # Step 4: Generate solution
        if self.generate_solution_for_environment(env_name):
            success_steps.append("solution_generated")
        else:
            print(f"❌ Failed to generate solution")
            return False
        
        print(f"\\n🎉 Environment '{env_name}' created successfully!")
        print(f"   ✅ Steps completed: {', '.join(success_steps)}")
        print(f"   📁 Solution file: build/solution_ompl_{env_name}.txt")
        print(f"   🚀 Executable: build/PayloadFourDrones_{env_name}")
        
        return True

def main():
    """Create different OMPL environments with actual obstacles"""
    
    workspace = "/home/user_136/Desktop/Project-A"
    modifier = OMPLEnvironmentModifier(workspace)
    
    print("🏗️  OMPL ENVIRONMENT MODIFIER")
    print("=" * 70)
    print("This tool creates different C++ executables for different environments")
    print("Each environment has different start/goal positions and constraints")
    print()
    
    # Define different environments
    environments = [
        {
            "name": "wide_open",
            "description": "Wide open space - long distance navigation",
            "start": [-50, -50, 15],
            "goal": [50, 50, 35],
            "bounds": {"low": [-60, -60, 10], "high": [60, 60, 50]}
        },
        {
            "name": "high_altitude", 
            "description": "High altitude navigation",
            "start": [0, 0, 40],
            "goal": [30, 30, 50],
            "bounds": {"low": [-40, -40, 35], "high": [40, 40, 55]}
        },
        {
            "name": "constrained_space",
            "description": "Constrained navigation space",
            "start": [-20, -20, 20],
            "goal": [20, 20, 25],
            "bounds": {"low": [-25, -25, 15], "high": [25, 25, 30]}
        }
    ]
    
    results = []
    
    for env in environments:
        success = modifier.create_complete_environment(
            env["name"],
            env["start"], 
            env["goal"],
            env["bounds"],
            env["description"]
        )
        results.append((env["name"], success))
    
    # Summary
    print("\\n" + "=" * 70)
    print("📊 ENVIRONMENT CREATION SUMMARY")
    print("=" * 70)
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"✅ Successful environments: {successful}/{total}")
    print(f"📈 Success rate: {successful/total*100:.1f}%")
    print()
    
    print("🎯 Created environments:")
    for name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        executable = f"PayloadFourDrones_{name}"
        solution = f"solution_ompl_{name}.txt"
        print(f"  • {name:<20} {status}")
        if success:
            print(f"    📂 Executable: build/{executable}")
            print(f"    📄 Solution: build/{solution}")
    
    if successful > 0:
        print(f"\\n🚀 How to use your new environments:")
        print(f"   1. Run different planners: ./build/PayloadFourDrones_<env_name>")
        print(f"   2. Optimize each solution: python3 trajectory_optimizer.py --input build/solution_ompl_<env_name>.txt")
        print(f"   3. Compare results across different environments!")
    
    print(f"\\n✨ You now know how to create truly different OMPL environments!")

if __name__ == "__main__":
    main()
