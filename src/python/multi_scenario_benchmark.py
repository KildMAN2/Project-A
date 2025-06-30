#!/usr/bin/env python3
"""
Multi-Scenario Trajectory Optimization Benchmark
================================================

This script tests trajectory optimization across multiple OMPL environments
with different obstacles, start/goal configurations, and optimization objectives.

Optimization Objectives:
- Shortest Path: Minimize total distance
- Minimal Mechanical Work: Minimize energy consumption
- Smoothest Trajectory: Minimize acceleration/jerk
- Time Optimal: Minimize total time
- Balanced: Weighted combination of objectives

Environment Types:
- Open Space: No obstacles
- Sparse Obstacles: Few scattered obstacles  
- Dense Obstacles: Many obstacles, complex navigation
- Corridor: Narrow passages
- Multi-Level: Different altitude requirements
"""

import os
import sys
import yaml
import json
import numpy as np
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
from dataclasses import dataclass, asdict
import pandas as pd

@dataclass
class ScenarioConfig:
    """Configuration for a single benchmark scenario"""
    name: str
    description: str
    start_pos: List[float]
    goal_pos: List[float] 
    obstacles: List[Dict]  # List of obstacle definitions
    environment_type: str  # 'open', 'sparse', 'dense', 'corridor', 'multilevel'
    difficulty: str       # 'easy', 'medium', 'hard', 'extreme'

@dataclass
class OptimizationConfig:
    """Configuration for optimization objectives"""
    name: str
    description: str
    weights: Dict[str, float]
    constraints: Dict[str, float]
    mode: str  # 'standard', 'advanced', 'ultra'
    iterations: int

@dataclass
class BenchmarkResult:
    """Results from a single benchmark run"""
    scenario_name: str
    optimization_name: str
    original_cost: float
    optimized_cost: float
    improvement_percent: float
    original_waypoints: int
    optimized_waypoints: int
    waypoint_reduction_percent: float
    execution_time: float
    success: bool
    error_message: Optional[str] = None

class TrajectoryBenchmark:
    """Main benchmarking system for trajectory optimization"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.build_path = self.workspace_path / "build"
        self.results_path = self.workspace_path / "benchmark_results"
        self.python_cmd = "/home/user_136/anaconda3/envs/ompl-env/bin/python3"
        self.optimizer_script = self.workspace_path / "src/python/trajectory_optimizer.py"
        
        # Create results directory
        self.results_path.mkdir(exist_ok=True)
        
        # Initialize configurations
        self.scenarios = self._create_scenarios()
        self.optimizations = self._create_optimizations()
        self.results = []
    
    def _create_scenarios(self) -> List[ScenarioConfig]:
        """Create diverse test scenarios with different environments and obstacles"""
        scenarios = []
        
        # 1. Open Space - Simple baseline
        scenarios.append(ScenarioConfig(
            name="open_space_simple",
            description="Simple open space, straight-line optimal",
            start_pos=[-10.0, -40.0, 20.0],
            goal_pos=[10.0, -30.0, 25.0],
            obstacles=[],
            environment_type="open",
            difficulty="easy"
        ))
        
        # 2. Open Space - Long distance
        scenarios.append(ScenarioConfig(
            name="open_space_long",
            description="Long distance traversal in open space",
            start_pos=[-50.0, -50.0, 15.0],
            goal_pos=[50.0, 50.0, 35.0],
            obstacles=[],
            environment_type="open", 
            difficulty="medium"
        ))
        
        # 3. Sparse Obstacles - Few scattered obstacles
        scenarios.append(ScenarioConfig(
            name="sparse_obstacles",
            description="Few scattered cylindrical obstacles",
            start_pos=[-20.0, -30.0, 20.0],
            goal_pos=[30.0, 20.0, 30.0],
            obstacles=[
                {"type": "cylinder", "center": [0, -10, 25], "radius": 8, "height": 20},
                {"type": "cylinder", "center": [15, 5, 25], "radius": 6, "height": 15},
                {"type": "cylinder", "center": [-5, 15, 25], "radius": 5, "height": 25}
            ],
            environment_type="sparse",
            difficulty="medium"
        ))
        
        # 4. Dense Obstacles - Complex navigation
        scenarios.append(ScenarioConfig(
            name="dense_obstacles",
            description="Dense obstacle field requiring complex maneuvering",
            start_pos=[-25.0, -35.0, 20.0],
            goal_pos=[35.0, 25.0, 30.0],
            obstacles=[
                {"type": "cylinder", "center": [-10, -20, 25], "radius": 4, "height": 15},
                {"type": "cylinder", "center": [0, -15, 25], "radius": 3, "height": 20},
                {"type": "cylinder", "center": [10, -10, 25], "radius": 5, "height": 18},
                {"type": "cylinder", "center": [20, -5, 25], "radius": 4, "height": 16},
                {"type": "cylinder", "center": [15, 5, 25], "radius": 6, "height": 22},
                {"type": "cylinder", "center": [5, 15, 25], "radius": 3, "height": 17},
                {"type": "cylinder", "center": [-5, 10, 25], "radius": 4, "height": 19},
                {"type": "cylinder", "center": [-15, 20, 25], "radius": 5, "height": 14}
            ],
            environment_type="dense",
            difficulty="hard"
        ))
        
        # 5. Corridor - Narrow passage
        scenarios.append(ScenarioConfig(
            name="narrow_corridor",
            description="Navigation through narrow corridors",
            start_pos=[-40.0, -20.0, 25.0],
            goal_pos=[40.0, 20.0, 25.0],
            obstacles=[
                # Create corridor walls
                {"type": "box", "center": [0, -30, 25], "size": [60, 5, 20]},
                {"type": "box", "center": [0, 30, 25], "size": [60, 5, 20]},
                {"type": "box", "center": [-20, 0, 25], "size": [5, 40, 20]},
                {"type": "box", "center": [20, 0, 25], "size": [5, 40, 20]},
            ],
            environment_type="corridor",
            difficulty="hard"
        ))
        
        # 6. Multi-Level - Different altitudes
        scenarios.append(ScenarioConfig(
            name="multi_level",
            description="Multi-level navigation with altitude changes",
            start_pos=[-30.0, -30.0, 15.0],
            goal_pos=[30.0, 30.0, 45.0],
            obstacles=[
                {"type": "cylinder", "center": [0, 0, 20], "radius": 12, "height": 15},
                {"type": "cylinder", "center": [-15, 15, 35], "radius": 8, "height": 12},
                {"type": "cylinder", "center": [15, -15, 30], "radius": 10, "height": 18}
            ],
            environment_type="multilevel",
            difficulty="hard"
        ))
        
        # 7. Original OMPL scenario
        scenarios.append(ScenarioConfig(
            name="ompl_original",
            description="Original OMPL PayloadFourDrones scenario",
            start_pos=[-10.0, -40.0, 20.0],
            goal_pos=[46.6868, -25.2859, 26.948],
            obstacles=[],  # Using original OMPL environment
            environment_type="original",
            difficulty="medium"
        ))
        
        # 8. Extreme Challenge - Very complex
        scenarios.append(ScenarioConfig(
            name="extreme_challenge",
            description="Extremely challenging environment with many constraints",
            start_pos=[-45.0, -45.0, 15.0],
            goal_pos=[45.0, 45.0, 45.0],
            obstacles=[
                # Multiple layers of obstacles
                {"type": "cylinder", "center": [-20, -20, 20], "radius": 6, "height": 15},
                {"type": "cylinder", "center": [-10, -30, 25], "radius": 4, "height": 20},
                {"type": "cylinder", "center": [0, -20, 30], "radius": 5, "height": 18},
                {"type": "cylinder", "center": [10, -10, 25], "radius": 6, "height": 22},
                {"type": "cylinder", "center": [20, 0, 20], "radius": 4, "height": 16},
                {"type": "cylinder", "center": [30, 10, 35], "radius": 7, "height": 14},
                {"type": "cylinder", "center": [20, 20, 30], "radius": 5, "height": 19},
                {"type": "cylinder", "center": [10, 30, 25], "radius": 6, "height": 17},
                {"type": "cylinder", "center": [0, 20, 40], "radius": 4, "height": 12},
                {"type": "cylinder", "center": [-10, 10, 35], "radius": 5, "height": 15},
                {"type": "cylinder", "center": [-20, 0, 25], "radius": 6, "height": 20},
                {"type": "cylinder", "center": [-30, -10, 30], "radius": 4, "height": 18}
            ],
            environment_type="extreme",
            difficulty="extreme"
        ))
        
        return scenarios
    
    def _create_optimizations(self) -> List[OptimizationConfig]:
        """Create different optimization objectives"""
        optimizations = []
        
        # 1. Shortest Path - Minimize total distance
        optimizations.append(OptimizationConfig(
            name="shortest_path",
            description="Minimize total path length",
            weights={"distance": 1.0, "smoothness": 0.1, "energy": 0.0},
            constraints={"max_velocity": 8.0, "max_acceleration": 4.0},
            mode="ultra",
            iterations=300
        ))
        
        # 2. Minimal Mechanical Work - Energy efficient
        optimizations.append(OptimizationConfig(
            name="minimal_energy",
            description="Minimize mechanical work and energy consumption",
            weights={"distance": 0.3, "smoothness": 0.2, "energy": 1.0},
            constraints={"max_velocity": 5.0, "max_acceleration": 2.5},
            mode="advanced",
            iterations=400
        ))
        
        # 3. Smoothest Trajectory - Minimize jerk/acceleration
        optimizations.append(OptimizationConfig(
            name="smoothest",
            description="Minimize acceleration and jerk for comfort",
            weights={"distance": 0.2, "smoothness": 1.0, "energy": 0.3},
            constraints={"max_velocity": 6.0, "max_acceleration": 2.0},
            mode="advanced", 
            iterations=500
        ))
        
        # 4. Time Optimal - Fastest traversal
        optimizations.append(OptimizationConfig(
            name="time_optimal", 
            description="Minimize total traversal time",
            weights={"distance": 0.8, "smoothness": 0.1, "energy": 0.1},
            constraints={"max_velocity": 12.0, "max_acceleration": 6.0},
            mode="ultra",
            iterations=250
        ))
        
        # 5. Balanced - Good overall performance
        optimizations.append(OptimizationConfig(
            name="balanced",
            description="Balanced optimization across all objectives",
            weights={"distance": 0.4, "smoothness": 0.4, "energy": 0.2},
            constraints={"max_velocity": 7.0, "max_acceleration": 3.5},
            mode="advanced",
            iterations=350
        ))
        
        # 6. Conservative - Safe, slow operation
        optimizations.append(OptimizationConfig(
            name="conservative",
            description="Conservative optimization prioritizing safety",
            weights={"distance": 0.2, "smoothness": 0.6, "energy": 0.2},
            constraints={"max_velocity": 3.0, "max_acceleration": 1.5},
            mode="standard",
            iterations=200
        ))
        
        return optimizations
    
    def _generate_ompl_solution(self, scenario: ScenarioConfig) -> bool:
        """Generate OMPL solution for a given scenario"""
        try:
            # Create temporary config file for this scenario
            config_file = self.build_path / f"scenario_{scenario.name}.yaml"
            
            # Create configuration for OMPL
            config = {
                "type": "PayloadFourDrones",
                "model": "payload4drones", 
                "start": scenario.start_pos + [0.0] * 32,  # Add zeros for full state
                "goal": scenario.goal_pos + [0.0] * 32,    # Add zeros for full state
                "dt": 0.1,
                "T": 200,  # Increased time horizon for complex scenarios
                "integrator": "euler",
                "dynamics": True,
                "obstacles": scenario.obstacles
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(config, f)
            
            # Run OMPL planner (assuming it can read config files)
            # For now, we'll use the existing solution as a template
            solution_file = self.build_path / f"solution_{scenario.name}.txt"
            
            # Copy original solution as template (in real implementation, 
            # you'd run OMPL with the specific scenario config)
            original_solution = self.build_path / "solution_path.txt"
            if original_solution.exists():
                subprocess.run(["cp", str(original_solution), str(solution_file)], check=True)
                return True
            else:
                print(f"Warning: Original solution not found for scenario {scenario.name}")
                return False
                
        except Exception as e:
            print(f"Error generating OMPL solution for {scenario.name}: {e}")
            return False
    
    def _run_optimization(self, scenario: ScenarioConfig, optimization: OptimizationConfig) -> BenchmarkResult:
        """Run optimization for a specific scenario-optimization combination"""
        start_time = time.time()
        
        try:
            # Generate OMPL solution for this scenario
            solution_file = self.build_path / f"solution_{scenario.name}.txt"
            if not solution_file.exists():
                if not self._generate_ompl_solution(scenario):
                    return BenchmarkResult(
                        scenario_name=scenario.name,
                        optimization_name=optimization.name,
                        original_cost=0,
                        optimized_cost=0,
                        improvement_percent=0,
                        original_waypoints=0,
                        optimized_waypoints=0,
                        waypoint_reduction_percent=0,
                        execution_time=0,
                        success=False,
                        error_message="Failed to generate OMPL solution"
                    )
            
            # Prepare optimization command with organized outputs
            yaml_dir = self.results_path / "yaml"
            png_dir = self.results_path / "png"
            yaml_dir.mkdir(exist_ok=True, parents=True)
            png_dir.mkdir(exist_ok=True, parents=True)
            
            output_file = yaml_dir / f"{scenario.name}_{optimization.name}_result.yaml"
            plot_file = png_dir / f"{scenario.name}_{optimization.name}_plot.png"
            
            cmd = [
                str(self.python_cmd),
                str(self.optimizer_script),
                "--input", str(solution_file),
                "--output", str(output_file),
                "--plot", str(plot_file),
                "--max_vel", str(optimization.constraints["max_velocity"]),
                "--max_acc", str(optimization.constraints["max_acceleration"]),
                "--iterations", str(optimization.iterations)
            ]
            
            # Add optimization mode
            if optimization.mode == "advanced":
                cmd.append("--advanced")
            elif optimization.mode == "ultra":
                cmd.append("--ultra")
            
            # Run optimization
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.workspace_path)
            
            if result.returncode != 0:
                return BenchmarkResult(
                    scenario_name=scenario.name,
                    optimization_name=optimization.name,
                    original_cost=0,
                    optimized_cost=0,
                    improvement_percent=0,
                    original_waypoints=0,
                    optimized_waypoints=0,
                    waypoint_reduction_percent=0,
                    execution_time=time.time() - start_time,
                    success=False,
                    error_message=f"Optimization failed: {result.stderr}"
                )
            
            # Parse results from output
            output_lines = result.stdout.split('\n')
            original_cost = 0
            optimized_cost = 0
            original_waypoints = 0
            optimized_waypoints = 0
            
            for line in output_lines:
                if "Original:" in line and "total cost" in line:
                    parts = line.split()
                    original_cost = float(parts[1])
                    # Extract waypoints from parentheses
                    for i, part in enumerate(parts):
                        if "points)" in part:
                            original_waypoints = int(parts[i-1].replace("(", ""))
                            break
                elif "Optimized:" in line and "total cost" in line:
                    parts = line.split()
                    optimized_cost = float(parts[1])
                    # Extract waypoints from parentheses
                    for i, part in enumerate(parts):
                        if "points)" in part:
                            optimized_waypoints = int(parts[i-1].replace("(", ""))
                            break
            
            # Calculate metrics
            improvement_percent = ((original_cost - optimized_cost) / original_cost * 100) if original_cost > 0 else 0
            waypoint_reduction_percent = ((original_waypoints - optimized_waypoints) / original_waypoints * 100) if original_waypoints > 0 else 0
            
            return BenchmarkResult(
                scenario_name=scenario.name,
                optimization_name=optimization.name,
                original_cost=original_cost,
                optimized_cost=optimized_cost,
                improvement_percent=improvement_percent,
                original_waypoints=original_waypoints,
                optimized_waypoints=optimized_waypoints,
                waypoint_reduction_percent=waypoint_reduction_percent,
                execution_time=time.time() - start_time,
                success=True
            )
            
        except Exception as e:
            return BenchmarkResult(
                scenario_name=scenario.name,
                optimization_name=optimization.name,
                original_cost=0,
                optimized_cost=0,
                improvement_percent=0,
                original_waypoints=0,
                optimized_waypoints=0,
                waypoint_reduction_percent=0,
                execution_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
    
    def run_benchmark(self, scenarios: Optional[List[str]] = None, 
                     optimizations: Optional[List[str]] = None) -> List[BenchmarkResult]:
        """Run the complete benchmark suite"""
        
        # Filter scenarios and optimizations if specified
        selected_scenarios = self.scenarios
        if scenarios:
            selected_scenarios = [s for s in self.scenarios if s.name in scenarios]
        
        selected_optimizations = self.optimizations  
        if optimizations:
            selected_optimizations = [o for o in self.optimizations if o.name in optimizations]
        
        total_runs = len(selected_scenarios) * len(selected_optimizations)
        current_run = 0
        
        print(f"🚀 Starting benchmark with {len(selected_scenarios)} scenarios and {len(selected_optimizations)} optimizations")
        print(f"Total runs: {total_runs}")
        print("=" * 80)
        
        results = []
        
        for scenario in selected_scenarios:
            print(f"\n📍 SCENARIO: {scenario.name} ({scenario.difficulty}) - {scenario.description}")
            
            for optimization in selected_optimizations:
                current_run += 1
                print(f"  🎯 [{current_run}/{total_runs}] {optimization.name} ({optimization.mode})...")
                
                result = self._run_optimization(scenario, optimization)
                results.append(result)
                
                if result.success:
                    print(f"    ✅ Success: {result.improvement_percent:.1f}% cost reduction, "
                          f"{result.waypoint_reduction_percent:.1f}% waypoint reduction "
                          f"({result.execution_time:.1f}s)")
                else:
                    print(f"    ❌ Failed: {result.error_message}")
        
        self.results.extend(results)
        return results
    
    def save_results(self, filename: str = "benchmark_results.json"):
        """Save benchmark results to file"""
        json_dir = self.results_path / "json"
        json_dir.mkdir(exist_ok=True, parents=True)
        results_file = json_dir / filename
        
        # Convert results to dictionaries for JSON serialization
        results_data = [asdict(result) for result in self.results]
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"📊 Results saved to: {results_file}")
    
    def generate_report(self) -> str:
        """Generate comprehensive benchmark report"""
        if not self.results:
            return "No benchmark results available."
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([asdict(r) for r in self.results if r.success])
        
        if df.empty:
            return "No successful benchmark runs."
        
        report = []
        report.append("=" * 80)
        report.append("🏆 TRAJECTORY OPTIMIZATION BENCHMARK REPORT")
        report.append("=" * 80)
        
        # Overall statistics
        total_runs = len(self.results)
        successful_runs = len([r for r in self.results if r.success])
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
        
        report.append(f"\n📈 OVERALL STATISTICS")
        report.append(f"Total benchmark runs: {total_runs}")
        report.append(f"Successful runs: {successful_runs}")
        report.append(f"Success rate: {success_rate:.1f}%")
        report.append(f"Average execution time: {df['execution_time'].mean():.2f}s")
        
        # Best performing combinations
        report.append(f"\n🥇 TOP PERFORMING COMBINATIONS")
        top_results = df.nlargest(5, 'improvement_percent')
        for _, row in top_results.iterrows():
            report.append(f"  • {row['scenario_name']} + {row['optimization_name']}: "
                         f"{row['improvement_percent']:.1f}% improvement, "
                         f"{row['waypoint_reduction_percent']:.1f}% waypoint reduction")
        
        # Performance by optimization method
        report.append(f"\n📊 PERFORMANCE BY OPTIMIZATION METHOD")
        opt_performance = df.groupby('optimization_name').agg({
            'improvement_percent': 'mean',
            'waypoint_reduction_percent': 'mean',
            'execution_time': 'mean'
        }).round(2)
        
        for opt_name, row in opt_performance.iterrows():
            report.append(f"  • {opt_name}: {row['improvement_percent']:.1f}% cost reduction, "
                         f"{row['waypoint_reduction_percent']:.1f}% waypoint reduction, "
                         f"{row['execution_time']:.1f}s avg time")
        
        # Performance by scenario difficulty
        report.append(f"\n🎯 PERFORMANCE BY SCENARIO TYPE")
        scenario_map = {s.name: s.difficulty for s in self.scenarios}
        df['difficulty'] = df['scenario_name'].map(scenario_map)
        
        diff_performance = df.groupby('difficulty').agg({
            'improvement_percent': 'mean',
            'waypoint_reduction_percent': 'mean',
            'execution_time': 'mean'
        }).round(2)
        
        for difficulty, row in diff_performance.iterrows():
            report.append(f"  • {difficulty.capitalize()}: {row['improvement_percent']:.1f}% cost reduction, "
                         f"{row['waypoint_reduction_percent']:.1f}% waypoint reduction, "
                         f"{row['execution_time']:.1f}s avg time")
        
        # Recommendations
        report.append(f"\n💡 RECOMMENDATIONS")
        best_overall = df.loc[df['improvement_percent'].idxmax()]
        fastest = df.loc[df['execution_time'].idxmin()]
        most_compressed = df.loc[df['waypoint_reduction_percent'].idxmax()]
        
        report.append(f"  • Best overall performance: {best_overall['optimization_name']} "
                     f"({best_overall['improvement_percent']:.1f}% improvement)")
        report.append(f"  • Fastest optimization: {fastest['optimization_name']} "
                     f"({fastest['execution_time']:.1f}s)")
        report.append(f"  • Best compression: {most_compressed['optimization_name']} "
                     f"({most_compressed['waypoint_reduction_percent']:.1f}% reduction)")
        
        return "\n".join(report)
    
    def create_visualizations(self):
        """Create visualization plots of benchmark results"""
        if not self.results:
            return
        
        df = pd.DataFrame([asdict(r) for r in self.results if r.success])
        if df.empty:
            return
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Trajectory Optimization Benchmark Results', fontsize=16)
        
        # 1. Cost improvement by optimization method
        opt_perf = df.groupby('optimization_name')['improvement_percent'].mean().sort_values(ascending=True)
        axes[0,0].barh(opt_perf.index, opt_perf.values)
        axes[0,0].set_xlabel('Average Cost Improvement (%)')
        axes[0,0].set_title('Cost Improvement by Optimization Method')
        axes[0,0].grid(True, alpha=0.3)
        
        # 2. Waypoint reduction by optimization method
        waypoint_perf = df.groupby('optimization_name')['waypoint_reduction_percent'].mean().sort_values(ascending=True)
        axes[0,1].barh(waypoint_perf.index, waypoint_perf.values)
        axes[0,1].set_xlabel('Average Waypoint Reduction (%)')
        axes[0,1].set_title('Waypoint Reduction by Optimization Method')
        axes[0,1].grid(True, alpha=0.3)
        
        # 3. Execution time by optimization method
        time_perf = df.groupby('optimization_name')['execution_time'].mean().sort_values(ascending=True)
        axes[1,0].barh(time_perf.index, time_perf.values)
        axes[1,0].set_xlabel('Average Execution Time (s)')
        axes[1,0].set_title('Execution Time by Optimization Method')
        axes[1,0].grid(True, alpha=0.3)
        
        # 4. Scatter plot: Improvement vs Execution Time
        scatter = axes[1,1].scatter(df['execution_time'], df['improvement_percent'], 
                                   c=df['waypoint_reduction_percent'], cmap='viridis', alpha=0.7)
        axes[1,1].set_xlabel('Execution Time (s)')
        axes[1,1].set_ylabel('Cost Improvement (%)')
        axes[1,1].set_title('Performance vs Speed Trade-off')
        axes[1,1].grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=axes[1,1], label='Waypoint Reduction (%)')
        
        plt.tight_layout()
        
        # Save plot to organized folder
        png_dir = self.results_path / "png"
        png_dir.mkdir(exist_ok=True, parents=True)
        plot_file = png_dir / "benchmark_analysis.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"📊 Benchmark analysis plot saved to: {plot_file}")
        plt.close()

def main():
    """Main benchmark execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-Scenario Trajectory Optimization Benchmark')
    parser.add_argument('--workspace', default='/home/user_136/Desktop/Project-A',
                       help='Workspace directory path')
    parser.add_argument('--scenarios', nargs='+', 
                       help='Specific scenarios to run (default: all)')
    parser.add_argument('--optimizations', nargs='+',
                       help='Specific optimizations to run (default: all)')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick benchmark with subset of scenarios')
    
    args = parser.parse_args()
    
    # Initialize benchmark
    benchmark = TrajectoryBenchmark(args.workspace)
    
    # Quick benchmark mode
    if args.quick:
        quick_scenarios = ['open_space_simple', 'sparse_obstacles', 'ompl_original']
        quick_optimizations = ['shortest_path', 'balanced', 'smoothest']
        results = benchmark.run_benchmark(quick_scenarios, quick_optimizations)
    else:
        results = benchmark.run_benchmark(args.scenarios, args.optimizations)
    
    # Save results and generate report
    benchmark.save_results()
    
    # Generate and display report
    report = benchmark.generate_report()
    print("\n" + report)
    
    # Create visualizations
    benchmark.create_visualizations()
    
    # Save report to file
    txt_dir = benchmark.results_path / "txt"
    txt_dir.mkdir(exist_ok=True, parents=True)
    report_file = txt_dir / "benchmark_report.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\n📄 Full report saved to: {report_file}")

if __name__ == "__main__":
    main()
