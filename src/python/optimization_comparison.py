#!/usr/bin/env python3
"""
Simple Multi-Objective Trajectory Optimization Test
==================================================

Tests different optimization objectives on the same OMPL trajectory:
- Shortest Path (distance minimization)
- Energy Efficient (work minimization) 
- Smoothest (acceleration/jerk minimization)
- Time Optimal (speed maximization)
- Balanced (combined objectives)
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt

class OptimizationComparison:
    """Compare different optimization objectives on the same trajectory"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.python_cmd = "/home/user_136/anaconda3/envs/ompl-env/bin/python3"
        self.optimizer_script = self.workspace_path / "src/python/trajectory_optimizer.py"
        self.input_file = self.workspace_path / "solution_path.txt"
        self.results = {}
        
    def run_optimization_test(self, name: str, description: str, max_vel: float, 
                            max_acc: float, mode: str, iterations: int) -> Dict:
        """Run a single optimization test"""
        print(f"🎯 Testing {name}: {description}")
        
        # Use organized folder structure
        yaml_dir = self.workspace_path / "build" / "yaml"
        png_dir = self.workspace_path / "build" / "png"
        yaml_dir.mkdir(exist_ok=True)
        png_dir.mkdir(exist_ok=True)
        
        output_file = yaml_dir / f"test_{name}.yaml"
        plot_file = png_dir / f"test_{name}.png"
        
        # Build command
        cmd = [
            str(self.python_cmd),
            str(self.optimizer_script),
            "--input", str(self.input_file),
            "--output", str(output_file),
            "--plot", str(plot_file),
            "--max_vel", str(max_vel),
            "--max_acc", str(max_acc),
            "--iterations", str(iterations)
        ]
        
        if mode == "advanced":
            cmd.append("--advanced")
        elif mode == "ultra":
            cmd.append("--ultra")
        
        # Run optimization
        start_time = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.workspace_path)
            execution_time = time.time() - start_time
            
            if result.returncode != 0:
                print(f"  ❌ Failed: {result.stderr}")
                return {"success": False, "error": result.stderr}
            
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
            
            result_data = {
                "success": True,
                "description": description,
                "original_cost": original_cost,
                "optimized_cost": optimized_cost,
                "improvement_percent": improvement,
                "original_waypoints": original_waypoints,
                "optimized_waypoints": optimized_waypoints,
                "waypoint_reduction_percent": waypoint_reduction,
                "execution_time": execution_time,
                "max_velocity": max_vel,
                "max_acceleration": max_acc,
                "mode": mode,
                "iterations": iterations
            }
            
            print(f"  ✅ Success: {improvement:.1f}% improvement, {waypoint_reduction:.1f}% fewer waypoints ({execution_time:.1f}s)")
            return result_data
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self):
        """Run all optimization objective tests"""
        print("🚀 Multi-Objective Trajectory Optimization Test")
        print("=" * 60)
        
        # Check input file exists
        if not self.input_file.exists():
            print(f"❌ Input file not found: {self.input_file}")
            print("Please run PayloadFourDrones first to generate solution_path.txt")
            return
        
        # Test configurations: [name, description, max_vel, max_acc, mode, iterations]
        tests = [
            ("shortest_path", "Minimize total distance (ultra-aggressive)", 10.0, 5.0, "ultra", 300),
            ("energy_efficient", "Minimize energy consumption (conservative)", 4.0, 2.0, "advanced", 400), 
            ("smoothest", "Minimize acceleration/jerk (comfort)", 5.0, 1.5, "advanced", 500),
            ("time_optimal", "Minimize total time (maximum speed)", 15.0, 8.0, "ultra", 250),
            ("balanced", "Balanced optimization (practical)", 7.0, 3.5, "advanced", 350),
            ("conservative", "Safe operation (minimum risk)", 3.0, 1.0, "standard", 200)
        ]
        
        print(f"Running {len(tests)} optimization tests...\n")
        
        for name, description, max_vel, max_acc, mode, iterations in tests:
            result = self.run_optimization_test(name, description, max_vel, max_acc, mode, iterations)
            self.results[name] = result
            time.sleep(0.5)  # Brief pause between tests
        
        self.generate_comparison_report()
        self.create_comparison_plots()
    
    def generate_comparison_report(self):
        """Generate comparison report"""
        print("\n" + "=" * 60)
        print("📊 OPTIMIZATION COMPARISON REPORT")
        print("=" * 60)
        
        successful_results = {k: v for k, v in self.results.items() if v.get("success", False)}
        
        if not successful_results:
            print("❌ No successful optimizations to compare")
            return
        
        print(f"\n✅ Successfully tested {len(successful_results)} optimization objectives\n")
        
        # Detailed results
        print("🎯 DETAILED RESULTS:")
        print("-" * 80)
        print(f"{'Objective':<18} {'Improvement':<12} {'Waypoints':<12} {'Time':<8} {'Description'}")
        print("-" * 80)
        
        for name, result in successful_results.items():
            if result["success"]:
                print(f"{name:<18} {result['improvement_percent']:>8.1f}%    "
                      f"{result['waypoint_reduction_percent']:>8.1f}%    "
                      f"{result['execution_time']:>5.1f}s   {result['description'][:30]}")
        
        # Rankings
        print(f"\n🏆 PERFORMANCE RANKINGS:")
        
        # Best cost improvement
        best_improvement = max(successful_results.items(), key=lambda x: x[1]["improvement_percent"])
        print(f"  🥇 Best Cost Reduction: {best_improvement[0]} ({best_improvement[1]['improvement_percent']:.1f}%)")
        
        # Best waypoint reduction
        best_compression = max(successful_results.items(), key=lambda x: x[1]["waypoint_reduction_percent"])
        print(f"  🥇 Best Compression: {best_compression[0]} ({best_compression[1]['waypoint_reduction_percent']:.1f}%)")
        
        # Fastest execution
        fastest = min(successful_results.items(), key=lambda x: x[1]["execution_time"])
        print(f"  🥇 Fastest Execution: {fastest[0]} ({fastest[1]['execution_time']:.1f}s)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if best_improvement[1]["improvement_percent"] > 10:
            print(f"  • For maximum quality: Use '{best_improvement[0]}' (best overall improvement)")
        
        if fastest[1]["execution_time"] < 5:
            print(f"  • For speed: Use '{fastest[0]}' (fastest execution)")
        
        balanced_result = successful_results.get("balanced", {})
        if balanced_result.get("success", False):
            print(f"  • For daily use: Use 'balanced' ({balanced_result['improvement_percent']:.1f}% improvement, {balanced_result['execution_time']:.1f}s)")
        
        # Save results to file
        json_dir = self.workspace_path / "build" / "json"
        json_dir.mkdir(exist_ok=True)
        results_file = json_dir / "optimization_comparison.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed results saved to: {results_file}")
    
    def create_comparison_plots(self):
        """Create comparison visualization"""
        successful_results = {k: v for k, v in self.results.items() if v.get("success", False)}
        
        if len(successful_results) < 2:
            print("⚠️  Not enough successful results for visualization")
            return
        
        # Prepare data
        names = list(successful_results.keys())
        improvements = [successful_results[name]["improvement_percent"] for name in names]
        waypoint_reductions = [successful_results[name]["waypoint_reduction_percent"] for name in names]
        execution_times = [successful_results[name]["execution_time"] for name in names]
        
        # Create comparison plots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Multi-Objective Trajectory Optimization Comparison', fontsize=16)
        
        # 1. Cost improvement comparison
        axes[0,0].bar(names, improvements, color='skyblue', alpha=0.7)
        axes[0,0].set_ylabel('Cost Improvement (%)')
        axes[0,0].set_title('Cost Reduction by Objective')
        axes[0,0].tick_params(axis='x', rotation=45)
        axes[0,0].grid(True, alpha=0.3)
        
        # 2. Waypoint reduction comparison  
        axes[0,1].bar(names, waypoint_reductions, color='lightgreen', alpha=0.7)
        axes[0,1].set_ylabel('Waypoint Reduction (%)')
        axes[0,1].set_title('Path Compression by Objective')
        axes[0,1].tick_params(axis='x', rotation=45)
        axes[0,1].grid(True, alpha=0.3)
        
        # 3. Execution time comparison
        axes[1,0].bar(names, execution_times, color='salmon', alpha=0.7)
        axes[1,0].set_ylabel('Execution Time (s)')
        axes[1,0].set_title('Speed by Objective')
        axes[1,0].tick_params(axis='x', rotation=45)
        axes[1,0].grid(True, alpha=0.3)
        
        # 4. Performance trade-off scatter
        axes[1,1].scatter(execution_times, improvements, s=100, alpha=0.7, c=waypoint_reductions, cmap='viridis')
        axes[1,1].set_xlabel('Execution Time (s)')
        axes[1,1].set_ylabel('Cost Improvement (%)')
        axes[1,1].set_title('Performance vs Speed Trade-off')
        axes[1,1].grid(True, alpha=0.3)
        
        # Add labels to scatter plot
        for i, name in enumerate(names):
            axes[1,1].annotate(name, (execution_times[i], improvements[i]), 
                             xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        plt.tight_layout()
        
        # Save plot
        png_dir = self.workspace_path / "build" / "png"
        png_dir.mkdir(exist_ok=True)
        plot_file = png_dir / "optimization_comparison.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"📊 Comparison plot saved to: {plot_file}")
        plt.close()

def main():
    """Main execution"""
    workspace = "/home/user_136/Desktop/Project-A"
    
    comparison = OptimizationComparison(workspace)
    comparison.run_all_tests()

if __name__ == "__main__":
    main()
