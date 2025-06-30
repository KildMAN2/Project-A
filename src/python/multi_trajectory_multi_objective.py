#!/usr/bin/env python3
"""
Multi-Trajectory Multi-Objective Optimization Test
=================================================

Tests all 6 optimization objectives on each of the different trajectories
we generated, showing how optimization performance varies across trajectory types.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt

class MultiTrajectoryOptimizer:
    """Test all optimization objectives on all different trajectories"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.python_cmd = "/home/user_136/anaconda3/envs/ompl-env/bin/python3"
        self.optimizer_script = self.workspace_path / "src/python/trajectory_optimizer.py"
        self.comparison_script = self.workspace_path / "src/python/optimization_comparison.py"
        self.results = {}
        
    def get_available_trajectories(self) -> List[Tuple[str, str]]:
        """Get all available trajectory files"""
        trajectories = []
        
        # Look for trajectory files from our previous generation
        build_path = self.workspace_path / "build"
        
        # Pattern: trajectory_[scenario].txt
        for file_path in build_path.glob("trajectory_*.txt"):
            scenario_name = file_path.stem.replace("trajectory_", "")
            if scenario_name != "initial":  # Skip the conversion file
                trajectories.append((scenario_name, str(file_path)))
        
        # Add the original OMPL solution
        original_path = self.workspace_path / "solution_path.txt"
        if original_path.exists():
            trajectories.append(("original_ompl", str(original_path)))
        
        return trajectories
    
    def run_optimization_on_trajectory(self, traj_name: str, traj_path: str, opt_name: str, 
                                     opt_config: Dict) -> Dict:
        """Run a specific optimization on a specific trajectory"""
        
        # Create organized output directories
        yaml_dir = self.workspace_path / "build" / "yaml"
        png_dir = self.workspace_path / "build" / "png"
        yaml_dir.mkdir(exist_ok=True)
        png_dir.mkdir(exist_ok=True)
        
        output_file = yaml_dir / f"multi_test_{traj_name}_{opt_name}.yaml"
        plot_file = png_dir / f"multi_test_{traj_name}_{opt_name}.png"
        
        # Build command based on optimization configuration
        cmd = [
            str(self.python_cmd),
            str(self.optimizer_script),
            "--input", traj_path,
            "--output", str(output_file),
            "--plot", str(plot_file),
            "--max_vel", str(opt_config["max_vel"]),
            "--max_acc", str(opt_config["max_acc"]),
            "--iterations", str(opt_config["iterations"])
        ]
        
        if opt_config["mode"] == "advanced":
            cmd.append("--advanced")
        elif opt_config["mode"] == "ultra":
            cmd.append("--ultra")
        
        # Run optimization
        start_time = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.workspace_path)
            execution_time = time.time() - start_time
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr,
                    "execution_time": execution_time
                }
            
            # Parse results
            output_lines = result.stdout.split('\n')
            original_cost = 0
            optimized_cost = 0
            original_waypoints = 0
            optimized_waypoints = 0
            
            for line in output_lines:
                if "Original:" in line and "total cost" in line:
                    parts = line.split()
                    original_cost = float(parts[1])
                    for i, part in enumerate(parts):
                        if "points)" in part:
                            original_waypoints = int(parts[i-1].replace("(", ""))
                            break
                elif "Optimized:" in line and "total cost" in line:
                    parts = line.split()
                    optimized_cost = float(parts[1])
                    for i, part in enumerate(parts):
                        if "points)" in part:
                            optimized_waypoints = int(parts[i-1].replace("(", ""))
                            break
            
            improvement = ((original_cost - optimized_cost) / original_cost * 100) if original_cost > 0 else 0
            waypoint_reduction = ((original_waypoints - optimized_waypoints) / original_waypoints * 100) if original_waypoints > 0 else 0
            
            return {
                "success": True,
                "original_cost": original_cost,
                "optimized_cost": optimized_cost,
                "improvement_percent": improvement,
                "original_waypoints": original_waypoints,
                "optimized_waypoints": optimized_waypoints,
                "waypoint_reduction_percent": waypoint_reduction,
                "execution_time": execution_time,
                "output_file": str(output_file),
                "plot_file": str(plot_file)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    def run_complete_test(self):
        """Run all optimizations on all trajectories"""
        
        print("🚀 Multi-Trajectory Multi-Objective Optimization Test")
        print("=" * 70)
        
        # Get available trajectories
        trajectories = self.get_available_trajectories()
        if not trajectories:
            print("❌ No trajectory files found!")
            print("Please run the true_environment_tester.py first to generate different trajectories.")
            return
        
        print(f"Found {len(trajectories)} different trajectories:")
        for traj_name, traj_path in trajectories:
            print(f"  • {traj_name}: {traj_path}")
        print()
        
        # Define optimization configurations
        optimizations = {
            "shortest_path": {
                "description": "Minimize total distance",
                "max_vel": 10.0, "max_acc": 5.0, "mode": "ultra", "iterations": 300
            },
            "energy_efficient": {
                "description": "Minimize energy consumption", 
                "max_vel": 4.0, "max_acc": 2.0, "mode": "advanced", "iterations": 400
            },
            "smoothest": {
                "description": "Minimize acceleration/jerk",
                "max_vel": 5.0, "max_acc": 1.5, "mode": "advanced", "iterations": 500
            },
            "time_optimal": {
                "description": "Minimize total time",
                "max_vel": 15.0, "max_acc": 8.0, "mode": "ultra", "iterations": 250
            },
            "balanced": {
                "description": "Balanced optimization",
                "max_vel": 7.0, "max_acc": 3.5, "mode": "advanced", "iterations": 350
            },
            "conservative": {
                "description": "Safe operation",
                "max_vel": 3.0, "max_acc": 1.0, "mode": "standard", "iterations": 200
            }
        }
        
        total_tests = len(trajectories) * len(optimizations)
        current_test = 0
        
        print(f"Running {total_tests} optimization tests...")
        print("=" * 70)
        
        # Run all combinations
        for traj_name, traj_path in trajectories:
            print(f"\n📍 TRAJECTORY: {traj_name}")
            print(f"   Source: {traj_path}")
            print("-" * 50)
            
            if traj_name not in self.results:
                self.results[traj_name] = {}
            
            for opt_name, opt_config in optimizations.items():
                current_test += 1
                print(f"  🎯 [{current_test}/{total_tests}] {opt_name} - {opt_config['description']}")
                
                result = self.run_optimization_on_trajectory(traj_name, traj_path, opt_name, opt_config)
                self.results[traj_name][opt_name] = result
                
                if result["success"]:
                    print(f"    ✅ {result['improvement_percent']:.1f}% improvement, "
                          f"{result['waypoint_reduction_percent']:.1f}% compression "
                          f"({result['execution_time']:.1f}s)")
                else:
                    print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
                
                time.sleep(0.5)  # Brief pause
        
        self.generate_comprehensive_report()
        self.create_comparison_visualizations()
        self.save_all_results()
    
    def generate_comprehensive_report(self):
        """Generate detailed report across all trajectories and optimizations"""
        
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE OPTIMIZATION ANALYSIS")
        print("=" * 70)
        
        # Overall statistics
        total_tests = sum(len(opts) for opts in self.results.values())
        successful_tests = sum(
            sum(1 for result in opts.values() if result.get("success", False))
            for opts in self.results.values()
        )
        
        print(f"\n📈 OVERALL STATISTICS")
        print(f"Total tests run: {total_tests}")
        print(f"Successful tests: {successful_tests}")
        print(f"Success rate: {successful_tests/total_tests*100:.1f}%")
        
        # Results by trajectory type
        print(f"\n🎯 RESULTS BY TRAJECTORY TYPE")
        print("-" * 50)
        for traj_name, optimizations in self.results.items():
            successful_opts = [opt for opt, result in optimizations.items() if result.get("success", False)]
            if successful_opts:
                avg_improvement = sum(
                    self.results[traj_name][opt]["improvement_percent"] 
                    for opt in successful_opts
                ) / len(successful_opts)
                
                avg_compression = sum(
                    self.results[traj_name][opt]["waypoint_reduction_percent"]
                    for opt in successful_opts
                ) / len(successful_opts)
                
                print(f"• {traj_name:<20}: {avg_improvement:>6.1f}% avg improvement, "
                      f"{avg_compression:>6.1f}% avg compression")
        
        # Results by optimization method
        print(f"\n⚡ RESULTS BY OPTIMIZATION METHOD")
        print("-" * 50)
        
        opt_names = set()
        for optimizations in self.results.values():
            opt_names.update(optimizations.keys())
        
        for opt_name in sorted(opt_names):
            results_for_opt = []
            for traj_name, optimizations in self.results.items():
                if opt_name in optimizations and optimizations[opt_name].get("success", False):
                    results_for_opt.append(optimizations[opt_name])
            
            if results_for_opt:
                avg_improvement = sum(r["improvement_percent"] for r in results_for_opt) / len(results_for_opt)
                avg_compression = sum(r["waypoint_reduction_percent"] for r in results_for_opt) / len(results_for_opt)
                avg_time = sum(r["execution_time"] for r in results_for_opt) / len(results_for_opt)
                
                print(f"• {opt_name:<20}: {avg_improvement:>6.1f}% improvement, "
                      f"{avg_compression:>6.1f}% compression, {avg_time:>6.1f}s avg time")
        
        # Best combinations
        print(f"\n🏆 TOP PERFORMING COMBINATIONS")
        print("-" * 50)
        
        all_combinations = []
        for traj_name, optimizations in self.results.items():
            for opt_name, result in optimizations.items():
                if result.get("success", False):
                    all_combinations.append((
                        traj_name, opt_name, result["improvement_percent"], 
                        result["waypoint_reduction_percent"], result["execution_time"]
                    ))
        
        # Sort by improvement percentage
        top_combinations = sorted(all_combinations, key=lambda x: x[2], reverse=True)[:5]
        
        for i, (traj, opt, improvement, compression, exec_time) in enumerate(top_combinations, 1):
            print(f"{i}. {traj} + {opt}: {improvement:.1f}% improvement, "
                  f"{compression:.1f}% compression ({exec_time:.1f}s)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 50)
        
        if top_combinations:
            best_overall = top_combinations[0]
            print(f"• Best overall: {best_overall[1]} on {best_overall[0]} "
                  f"({best_overall[2]:.1f}% improvement)")
        
        # Find most consistent optimization
        opt_consistency = {}
        for opt_name in sorted(opt_names):
            improvements = []
            for traj_name, optimizations in self.results.items():
                if opt_name in optimizations and optimizations[opt_name].get("success", False):
                    improvements.append(optimizations[opt_name]["improvement_percent"])
            
            if improvements:
                opt_consistency[opt_name] = {
                    "avg": sum(improvements) / len(improvements),
                    "std": (sum((x - sum(improvements)/len(improvements))**2 for x in improvements) / len(improvements))**0.5
                }
        
        if opt_consistency:
            most_consistent = min(opt_consistency.items(), key=lambda x: x[1]["std"])
            print(f"• Most consistent: {most_consistent[0]} "
                  f"(avg {most_consistent[1]['avg']:.1f}% ± {most_consistent[1]['std']:.1f}%)")
    
    def create_comparison_visualizations(self):
        """Create comprehensive visualization plots"""
        
        # Prepare data for plotting
        traj_names = list(self.results.keys())
        opt_names = set()
        for optimizations in self.results.values():
            opt_names.update(optimizations.keys())
        opt_names = sorted(list(opt_names))
        
        # Create improvement matrix
        improvement_matrix = []
        compression_matrix = []
        time_matrix = []
        
        for traj_name in traj_names:
            improvement_row = []
            compression_row = []
            time_row = []
            
            for opt_name in opt_names:
                if (opt_name in self.results[traj_name] and 
                    self.results[traj_name][opt_name].get("success", False)):
                    result = self.results[traj_name][opt_name]
                    improvement_row.append(result["improvement_percent"])
                    compression_row.append(result["waypoint_reduction_percent"])
                    time_row.append(result["execution_time"])
                else:
                    improvement_row.append(0)
                    compression_row.append(0)
                    time_row.append(0)
            
            improvement_matrix.append(improvement_row)
            compression_matrix.append(compression_row)
            time_matrix.append(time_row)
        
        # Create plots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Multi-Trajectory Multi-Objective Optimization Results', fontsize=16)
        
        # 1. Improvement heatmap
        im1 = axes[0,0].imshow(improvement_matrix, cmap='RdYlGn', aspect='auto')
        axes[0,0].set_title('Cost Improvement (%) by Trajectory and Optimization')
        axes[0,0].set_xticks(range(len(opt_names)))
        axes[0,0].set_xticklabels(opt_names, rotation=45, ha='right')
        axes[0,0].set_yticks(range(len(traj_names)))
        axes[0,0].set_yticklabels(traj_names)
        plt.colorbar(im1, ax=axes[0,0])
        
        # Add text annotations
        for i in range(len(traj_names)):
            for j in range(len(opt_names)):
                if improvement_matrix[i][j] > 0:
                    axes[0,0].text(j, i, f'{improvement_matrix[i][j]:.1f}%', 
                                 ha='center', va='center', fontsize=8)
        
        # 2. Compression heatmap
        im2 = axes[0,1].imshow(compression_matrix, cmap='Blues', aspect='auto')
        axes[0,1].set_title('Waypoint Reduction (%) by Trajectory and Optimization')
        axes[0,1].set_xticks(range(len(opt_names)))
        axes[0,1].set_xticklabels(opt_names, rotation=45, ha='right')
        axes[0,1].set_yticks(range(len(traj_names)))
        axes[0,1].set_yticklabels(traj_names)
        plt.colorbar(im2, ax=axes[0,1])
        
        # 3. Average performance by optimization
        opt_avg_improvement = []
        opt_avg_compression = []
        
        for j, opt_name in enumerate(opt_names):
            improvements = [improvement_matrix[i][j] for i in range(len(traj_names)) if improvement_matrix[i][j] > 0]
            compressions = [compression_matrix[i][j] for i in range(len(traj_names)) if compression_matrix[i][j] > 0]
            
            opt_avg_improvement.append(sum(improvements) / len(improvements) if improvements else 0)
            opt_avg_compression.append(sum(compressions) / len(compressions) if compressions else 0)
        
        axes[1,0].bar(opt_names, opt_avg_improvement, color='skyblue', alpha=0.7)
        axes[1,0].set_title('Average Cost Improvement by Optimization Method')
        axes[1,0].set_ylabel('Average Improvement (%)')
        axes[1,0].tick_params(axis='x', rotation=45)
        axes[1,0].grid(True, alpha=0.3)
        
        # 4. Average performance by trajectory
        traj_avg_improvement = []
        traj_avg_compression = []
        
        for i, traj_name in enumerate(traj_names):
            improvements = [improvement_matrix[i][j] for j in range(len(opt_names)) if improvement_matrix[i][j] > 0]
            compressions = [compression_matrix[i][j] for j in range(len(opt_names)) if compression_matrix[i][j] > 0]
            
            traj_avg_improvement.append(sum(improvements) / len(improvements) if improvements else 0)
            traj_avg_compression.append(sum(compressions) / len(compressions) if compressions else 0)
        
        axes[1,1].bar(traj_names, traj_avg_improvement, color='lightgreen', alpha=0.7)
        axes[1,1].set_title('Average Cost Improvement by Trajectory Type')
        axes[1,1].set_ylabel('Average Improvement (%)')
        axes[1,1].tick_params(axis='x', rotation=45)
        axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        # Save plot to organized folder
        png_dir = self.workspace_path / "build" / "png"
        png_dir.mkdir(exist_ok=True)
        plot_file = png_dir / "multi_trajectory_analysis.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"\n📊 Comprehensive analysis plot saved to: {plot_file}")
        plt.close()
    
    def save_all_results(self):
        """Save all results to JSON file"""
        json_dir = self.workspace_path / "build" / "json"
        json_dir.mkdir(exist_ok=True)
        results_file = json_dir / "multi_trajectory_results.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 All results saved to: {results_file}")
        print(f"📁 Individual result files: build/yaml/multi_test_*")
        print(f"📊 Individual plots: build/png/multi_test_*.png")

def main():
    """Run comprehensive multi-trajectory multi-objective test"""
    workspace = "/home/user_136/Desktop/Project-A"
    
    optimizer = MultiTrajectoryOptimizer(workspace)
    optimizer.run_complete_test()
    
    print("\n🎉 Complete multi-trajectory multi-objective analysis finished!")
    print("This shows how different optimization strategies perform on different trajectory types.")

if __name__ == "__main__":
    main()
