#!/usr/bin/env python3
"""
Direct trajectory optimization for payload trajectories
This script takes an OMPL solution and applies trajectory optimization 
to smooth and improve the path.
"""

import numpy as np
import yaml
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.interpolate import splev, splprep
import argparse
import os

class TrajectoryOptimizer:
    def __init__(self, dt=0.1, max_velocity=5.0, max_acceleration=3.0):
        self.dt = dt
        self.max_velocity = max_velocity
        self.max_acceleration = max_acceleration
    
    def load_ompl_solution(self, filepath):
        """Load OMPL solution from text file"""
        waypoints = []
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse space-separated values
                        coords = [float(x) for x in line.split()]
                        if len(coords) >= 3:  # At least x, y, z
                            waypoints.append(coords[:3])  # Take only position
            return np.array(waypoints)
        except Exception as e:
            print(f"Error loading OMPL solution: {e}")
            return None
    
    def smooth_path_spline(self, waypoints, num_points=100, smoothing=0.0):
        """Smooth path using B-spline interpolation"""
        if len(waypoints) < 3:
            return waypoints
        
        # Transpose for splprep (expects (ndim, npoints))
        waypoints_t = waypoints.T
        
        # Fit spline
        tck, u = splprep(waypoints_t, s=smoothing, k=min(3, len(waypoints)-1))
        
        # Evaluate spline at uniform intervals
        u_new = np.linspace(0, 1, num_points)
        smooth_points = splev(u_new, tck)
        
        # Transpose back to (npoints, ndim)
        return np.array(smooth_points).T
    
    def compute_velocity_profile(self, path):
        """Compute velocity profile along the path"""
        if len(path) < 2:
            return np.zeros((len(path), 3))
        
        velocities = np.zeros_like(path)
        
        # Forward differences for velocity
        for i in range(len(path) - 1):
            velocities[i] = (path[i+1] - path[i]) / self.dt
        
        # Last point gets same velocity as previous
        velocities[-1] = velocities[-2] if len(path) > 1 else np.zeros(3)
        
        # Limit velocities
        for i in range(len(velocities)):
            vel_mag = np.linalg.norm(velocities[i])
            if vel_mag > self.max_velocity:
                velocities[i] = velocities[i] * (self.max_velocity / vel_mag)
        
        return velocities
    
    def compute_acceleration_profile(self, velocities):
        """Compute acceleration profile from velocities"""
        if len(velocities) < 2:
            return np.zeros_like(velocities)
        
        accelerations = np.zeros_like(velocities)
        
        # Forward differences for acceleration
        for i in range(len(velocities) - 1):
            accelerations[i] = (velocities[i+1] - velocities[i]) / self.dt
        
        # Last point gets same acceleration as previous
        accelerations[-1] = accelerations[-2] if len(velocities) > 1 else np.zeros(3)
        
        # Limit accelerations
        for i in range(len(accelerations)):
            acc_mag = np.linalg.norm(accelerations[i])
            if acc_mag > self.max_acceleration:
                accelerations[i] = accelerations[i] * (self.max_acceleration / acc_mag)
        
        return accelerations
    
    def trajectory_cost(self, path):
        """Compute trajectory cost (path length + smoothness)"""
        if len(path) < 2:
            return 0.0
        
        # Path length cost
        length_cost = 0.0
        for i in range(len(path) - 1):
            length_cost += np.linalg.norm(path[i+1] - path[i])
        
        # Smoothness cost (curvature)
        smoothness_cost = 0.0
        if len(path) >= 3:
            for i in range(1, len(path) - 1):
                # Approximate curvature using second differences
                d1 = path[i] - path[i-1]
                d2 = path[i+1] - path[i]
                if np.linalg.norm(d1) > 0 and np.linalg.norm(d2) > 0:
                    d1_norm = d1 / np.linalg.norm(d1)
                    d2_norm = d2 / np.linalg.norm(d2)
                    curvature = np.linalg.norm(d2_norm - d1_norm)
                    smoothness_cost += curvature
        
        return length_cost + 0.5 * smoothness_cost
    
    def optimize_trajectory_advanced(self, waypoints, iterations=100):
        """Advanced trajectory optimization with multiple stages"""
        print(f"Optimizing trajectory with {len(waypoints)} waypoints...")
        
        # Stage 1: Path shortening - find shortcuts
        print("Stage 1: Path shortening...")
        shortened_path = self.shorten_path(waypoints)
        
        # Stage 2: Smooth the shortened path
        print("Stage 2: Spline smoothing...")
        smooth_path = self.smooth_path_spline(shortened_path, num_points=len(shortened_path)*2)
        
        # Stage 3: Numerical optimization
        print("Stage 3: Numerical optimization...")
        optimized_path = self.numerical_optimization(smooth_path, iterations)
        
        # Stage 4: Time-optimal parameterization
        print("Stage 4: Time-optimal parameterization...")
        final_path, final_times = self.time_optimal_parameterization(optimized_path)
        
        # Compute velocity and acceleration profiles
        velocities = self.compute_velocity_profile(final_path)
        accelerations = self.compute_acceleration_profile(velocities)
        
        # Compute costs
        original_cost = self.trajectory_cost(waypoints)
        optimized_cost = self.trajectory_cost(final_path)
        
        # Show both total cost improvement and per-point efficiency
        total_improvement = ((original_cost - optimized_cost) / original_cost * 100)
        original_cost_per_point = original_cost / len(waypoints)
        optimized_cost_per_point = optimized_cost / len(final_path)
        
        print(f"=== OPTIMIZATION RESULTS ===")
        print(f"Original: {original_cost:.3f} total cost ({len(waypoints)} points)")
        print(f"Optimized: {optimized_cost:.3f} total cost ({len(final_path)} points)")
        print(f"Total path improvement: {total_improvement:.1f}%")
        print(f"Path compression: {len(waypoints)} -> {len(final_path)} points ({(1-len(final_path)/len(waypoints))*100:.1f}% reduction)")
        print(f"Cost per point - Original: {original_cost_per_point:.4f}, Optimized: {optimized_cost_per_point:.4f}")
        
        if total_improvement > 0:
            print(f"🎉 SUCCESS: Reduced total path cost by {total_improvement:.1f}%!")
        else:
            print(f"ℹ️  Note: Higher resolution path with {-total_improvement:.1f}% more total cost but better dynamics")
        
        return {
            'path': final_path,
            'velocities': velocities,
            'accelerations': accelerations,
            'times': final_times,
            'original_cost': original_cost,
            'optimized_cost': optimized_cost
        }
    
    def shorten_path(self, waypoints, max_distance=2.0):
        """Remove redundant waypoints by finding shortcuts"""
        if len(waypoints) <= 2:
            return waypoints
        
        shortened = [waypoints[0]]  # Always keep start
        i = 0
        
        while i < len(waypoints) - 1:
            # Look ahead to find the furthest reachable point
            furthest = i + 1
            for j in range(i + 2, len(waypoints)):
                # Check if we can go directly from waypoints[i] to waypoints[j]
                distance = np.linalg.norm(waypoints[j] - waypoints[i])
                if distance <= max_distance:
                    # Simple collision check: ensure intermediate points aren't too far
                    skip = True
                    for k in range(i + 1, j):
                        line_point = waypoints[i] + (waypoints[j] - waypoints[i]) * ((k - i) / (j - i))
                        if np.linalg.norm(waypoints[k] - line_point) > 0.5:  # Tolerance
                            skip = False
                            break
                    if skip:
                        furthest = j
                else:
                    break
            
            i = furthest
            shortened.append(waypoints[i])
        
        print(f"Path shortening: {len(waypoints)} -> {len(shortened)} waypoints")
        return np.array(shortened)
    
    def numerical_optimization(self, path, iterations=100):
        """Numerical optimization to minimize cost function"""
        if len(path) <= 2:
            return path
        
        # Optimize intermediate points (keep start and end fixed)
        def objective(x):
            # Reshape x to path format
            optimized_path = path.copy()
            optimized_path[1:-1] = x.reshape(-1, 3)
            return self.trajectory_cost(optimized_path)
        
        # Initial guess: current intermediate points
        x0 = path[1:-1].flatten()
        
        # Reasonable bounds: allow some movement but not too far
        bounds = []
        for point in path[1:-1]:
            for coord in point:
                bounds.append((coord - 5.0, coord + 5.0))  # Increased bounds
        
        try:
            # Optimize with multiple methods to increase success rate
            methods = ['L-BFGS-B', 'SLSQP']
            best_result = None
            best_cost = float('inf')
            
            for method in methods:
                try:
                    result = minimize(objective, x0, method=method, bounds=bounds,
                                    options={'maxiter': iterations})
                    if result.success and result.fun < best_cost:
                        best_result = result
                        best_cost = result.fun
                except:
                    continue
            
            if best_result and best_result.success:
                optimized_path = path.copy()
                optimized_path[1:-1] = best_result.x.reshape(-1, 3)
                print(f"Numerical optimization converged: {best_result.fun:.4f}")
                return optimized_path
            else:
                print("Numerical optimization failed, using original path")
                return path
        except Exception as e:
            print(f"Numerical optimization error: {e}, using original path")
            return path
    
    def time_optimal_parameterization(self, path):
        """Compute time-optimal parameterization considering velocity/acceleration limits"""
        if len(path) <= 1:
            return path, np.array([0.0])
        
        times = [0.0]
        
        for i in range(1, len(path)):
            # Distance to next point
            distance = np.linalg.norm(path[i] - path[i-1])
            
            # Time needed considering velocity and acceleration limits
            # Using kinematic equation: d = v*t + 0.5*a*t^2
            # Solving for optimal time with constraints
            
            # Simple approach: limit velocity
            min_time_vel = distance / self.max_velocity
            
            # Considering acceleration (assume we can accelerate for half the distance)
            # d = 0.5*a*t^2 for acceleration phase
            min_time_acc = 2 * np.sqrt(distance / self.max_acceleration)
            
            # Take the larger time requirement
            dt = max(min_time_vel, min_time_acc, self.dt)
            times.append(times[-1] + dt)
        
        return path, np.array(times)
    
    def optimize_trajectory(self, waypoints, iterations=100):
        """Choose optimization method based on path complexity"""
        if len(waypoints) > 30:  # Use advanced optimization for complex paths
            return self.optimize_trajectory_advanced(waypoints, iterations)
        else:  # Use simple optimization for short paths
            return self.optimize_trajectory_simple(waypoints, iterations)
    
    def optimize_trajectory_simple(self, waypoints, iterations=100):
        """Simple trajectory optimization (original method)"""
        print(f"Optimizing trajectory with {len(waypoints)} waypoints...")
        
        # First, smooth the path using splines
        smooth_path = self.smooth_path_spline(waypoints, num_points=len(waypoints)*2)
        
        # Compute velocity and acceleration profiles
        velocities = self.compute_velocity_profile(smooth_path)
        accelerations = self.compute_acceleration_profile(velocities)
        
        # Create time vector
        times = np.arange(len(smooth_path)) * self.dt
        
        # Compute costs
        original_cost = self.trajectory_cost(waypoints)
        optimized_cost = self.trajectory_cost(smooth_path)
        
        # Normalize costs by number of waypoints for fair comparison
        original_cost_per_point = original_cost / len(waypoints)
        optimized_cost_per_point = optimized_cost / len(smooth_path)
        
        print(f"Original cost: {original_cost:.3f} ({len(waypoints)} points)")
        print(f"Optimized cost: {optimized_cost:.3f} ({len(smooth_path)} points)")
        print(f"Cost per point - Original: {original_cost_per_point:.4f}, Optimized: {optimized_cost_per_point:.4f}")
        
        improvement_per_point = ((original_cost_per_point - optimized_cost_per_point) / original_cost_per_point * 100)
        print(f"Per-point improvement: {improvement_per_point:.1f}%")
        
        return {
            'path': smooth_path,
            'velocities': velocities,
            'accelerations': accelerations,
            'times': times,
            'original_cost': original_cost,
            'optimized_cost': optimized_cost
        }
    
    def save_trajectory(self, result, output_file):
        """Save optimized trajectory to file"""
        trajectory_data = {
            'trajectory': {
                'positions': result['path'].tolist(),
                'velocities': result['velocities'].tolist(),
                'accelerations': result['accelerations'].tolist(),
                'times': result['times'].tolist(),
                'dt': self.dt,
                'costs': {
                    'original': float(result['original_cost']),
                    'optimized': float(result['optimized_cost'])
                }
            }
        }
        
        with open(output_file, 'w') as f:
            yaml.dump(trajectory_data, f, default_flow_style=False)
        
        print(f"Optimized trajectory saved to: {output_file}")
    
    def plot_trajectory(self, original_path, optimized_result, output_plot=None):
        """Plot original vs optimized trajectory"""
        fig = plt.figure(figsize=(15, 10))
        
        # 3D trajectory plot
        ax1 = fig.add_subplot(221, projection='3d')
        ax1.plot(original_path[:, 0], original_path[:, 1], original_path[:, 2], 
                'r-o', label='Original', markersize=4, alpha=0.7)
        ax1.plot(optimized_result['path'][:, 0], optimized_result['path'][:, 1], 
                optimized_result['path'][:, 2], 'b-', label='Optimized', linewidth=2)
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.set_zlabel('Z')
        ax1.legend()
        ax1.set_title('3D Trajectory Comparison')
        
        # Velocity profile
        ax2 = fig.add_subplot(222)
        vel_magnitudes = np.linalg.norm(optimized_result['velocities'], axis=1)
        ax2.plot(optimized_result['times'], vel_magnitudes, 'b-', linewidth=2)
        ax2.axhline(y=self.max_velocity, color='r', linestyle='--', label='Max velocity')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Velocity magnitude')
        ax2.set_title('Velocity Profile')
        ax2.legend()
        ax2.grid(True)
        
        # Acceleration profile
        ax3 = fig.add_subplot(223)
        acc_magnitudes = np.linalg.norm(optimized_result['accelerations'], axis=1)
        ax3.plot(optimized_result['times'], acc_magnitudes, 'g-', linewidth=2)
        ax3.axhline(y=self.max_acceleration, color='r', linestyle='--', label='Max acceleration')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Acceleration magnitude')
        ax3.set_title('Acceleration Profile')
        ax3.legend()
        ax3.grid(True)
        
        # XY trajectory
        ax4 = fig.add_subplot(224)
        ax4.plot(original_path[:, 0], original_path[:, 1], 'r-o', 
                label='Original', markersize=4, alpha=0.7)
        ax4.plot(optimized_result['path'][:, 0], optimized_result['path'][:, 1], 
                'b-', label='Optimized', linewidth=2)
        ax4.set_xlabel('X')
        ax4.set_ylabel('Y')
        ax4.set_title('XY Trajectory')
        ax4.legend()
        ax4.grid(True)
        ax4.axis('equal')
        
        plt.tight_layout()
        
        if output_plot:
            plt.savefig(output_plot, dpi=300, bbox_inches='tight')
            print(f"Trajectory plot saved to: {output_plot}")
        
        plt.show()

    def optimize_trajectory_ultra(self, waypoints, iterations=100):
        """Ultra-aggressive optimization for maximum improvement"""
        print(f"Ultra-optimizing trajectory with {len(waypoints)} waypoints...")
        
        # Stage 1: Aggressive path shortening
        print("Stage 1: Aggressive path shortening...")
        shortened_path = self.shorten_path(waypoints, max_distance=5.0)  # Increased distance
        
        # Stage 2: Line-of-sight optimization
        print("Stage 2: Line-of-sight optimization...")
        los_path = self.line_of_sight_optimization(shortened_path)
        
        # Stage 3: Numerical optimization with multiple passes
        print("Stage 3: Multi-pass numerical optimization...")
        optimized_path = self.multi_pass_optimization(los_path, iterations)
        
        # Stage 4: Final smoothing for dynamics
        print("Stage 4: Final dynamics smoothing...")
        final_path = self.smooth_path_spline(optimized_path, num_points=len(optimized_path)*2)
        
        # Stage 5: Time-optimal parameterization
        print("Stage 5: Time-optimal parameterization...")
        final_path, final_times = self.time_optimal_parameterization(final_path)
        
        # Compute velocity and acceleration profiles
        velocities = self.compute_velocity_profile(final_path)
        accelerations = self.compute_acceleration_profile(velocities)
        
        # Compute costs
        original_cost = self.trajectory_cost(waypoints)
        optimized_cost = self.trajectory_cost(final_path)
        
        # Show results
        total_improvement = ((original_cost - optimized_cost) / original_cost * 100)
        
        print(f"=== ULTRA OPTIMIZATION RESULTS ===")
        print(f"Original: {original_cost:.3f} total cost ({len(waypoints)} points)")
        print(f"Optimized: {optimized_cost:.3f} total cost ({len(final_path)} points)")
        print(f"Total path improvement: {total_improvement:.1f}%")
        print(f"Path transformation: {len(waypoints)} -> {len(optimized_path)} -> {len(final_path)} points")
        
        if total_improvement > 0:
            print(f"🚀 ULTRA SUCCESS: Reduced total path cost by {total_improvement:.1f}%!")
        else:
            print(f"ℹ️  Higher resolution path with better dynamics")
        
        return {
            'path': final_path,
            'velocities': velocities,
            'accelerations': accelerations,
            'times': final_times,
            'original_cost': original_cost,
            'optimized_cost': optimized_cost
        }
    
    def line_of_sight_optimization(self, waypoints):
        """Optimize by connecting waypoints with direct line-of-sight when possible"""
        if len(waypoints) <= 2:
            return waypoints
        
        optimized = [waypoints[0]]  # Always keep start
        i = 0
        
        while i < len(waypoints) - 1:
            # Find the furthest point we can reach in a straight line
            furthest = i + 1
            for j in range(i + 2, len(waypoints)):
                # Check if straight line is reasonable (no sharp turns)
                if i > 0:
                    # Check angle between previous segment and new segment
                    v1 = waypoints[i] - optimized[-1]
                    v2 = waypoints[j] - waypoints[i]
                    if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                        angle = np.arccos(np.clip(cos_angle, -1, 1))
                        if angle > np.pi/3:  # Allow up to 60 degree turns
                            break
                
                furthest = j
            
            i = furthest
            optimized.append(waypoints[i])
        
        print(f"Line-of-sight optimization: {len(waypoints)} -> {len(optimized)} waypoints")
        return np.array(optimized)
    
    def multi_pass_optimization(self, path, iterations=100):
        """Multiple passes of numerical optimization with different strategies"""
        if len(path) <= 2:
            return path
        
        current_path = path.copy()
        
        # Pass 1: Minimize total distance
        print("  Pass 1: Minimizing total distance...")
        current_path = self.numerical_optimization(current_path, iterations//3)
        
        # Pass 2: Minimize curvature  
        print("  Pass 2: Minimizing curvature...")
        def curvature_objective(x):
            opt_path = current_path.copy()
            opt_path[1:-1] = x.reshape(-1, 3)
            return self.trajectory_cost(opt_path) * 2.0  # Weight smoothness more
        
        if len(current_path) > 2:
            x0 = current_path[1:-1].flatten()
            bounds = []
            for point in current_path[1:-1]:
                for coord in point:
                    bounds.append((coord - 3.0, coord + 3.0))
            
            try:
                result = minimize(curvature_objective, x0, method='L-BFGS-B', 
                                bounds=bounds, options={'maxiter': iterations//3})
                if result.success:
                    current_path[1:-1] = result.x.reshape(-1, 3)
                    print(f"  Curvature optimization: {result.fun:.4f}")
            except:
                pass
        
        # Pass 3: Final polish
        print("  Pass 3: Final optimization...")
        current_path = self.numerical_optimization(current_path, iterations//3)
        
        return current_path

def main():
    parser = argparse.ArgumentParser(description='Optimize payload trajectory')
    parser.add_argument('--input', required=True, help='Input OMPL solution file')
    parser.add_argument('--output', default='optimized_trajectory.yaml', 
                       help='Output trajectory file')
    parser.add_argument('--plot', default='trajectory_optimization.png', 
                       help='Output plot file')
    parser.add_argument('--dt', type=float, default=0.1, help='Time step')
    parser.add_argument('--max_vel', type=float, default=5.0, help='Max velocity')
    parser.add_argument('--max_acc', type=float, default=3.0, help='Max acceleration')
    parser.add_argument('--advanced', action='store_true', 
                       help='Use advanced multi-stage optimization')
    parser.add_argument('--ultra', action='store_true',
                       help='Use ultra-aggressive optimization for maximum improvement')
    parser.add_argument('--iterations', type=int, default=100, 
                       help='Number of optimization iterations')
    
    args = parser.parse_args()
    
    # Ensure organized output folders exist
    build_dir = os.path.dirname(args.output) if os.path.dirname(args.output) else 'build'
    yaml_dir = os.path.join(build_dir, 'yaml')
    png_dir = os.path.join(build_dir, 'png')
    os.makedirs(yaml_dir, exist_ok=True)
    os.makedirs(png_dir, exist_ok=True)
    
    # Adjust output paths to organized folders
    if not os.path.dirname(args.output):
        args.output = os.path.join(yaml_dir, args.output)
    elif not args.output.startswith(yaml_dir):
        args.output = os.path.join(yaml_dir, os.path.basename(args.output))
        
    if not os.path.dirname(args.plot):
        args.plot = os.path.join(png_dir, args.plot)
    elif not args.plot.startswith(png_dir):
        args.plot = os.path.join(png_dir, os.path.basename(args.plot))
    
    # Create optimizer
    optimizer = TrajectoryOptimizer(dt=args.dt, max_velocity=args.max_vel, 
                                  max_acceleration=args.max_acc)
    
    # Load original trajectory
    waypoints = optimizer.load_ompl_solution(args.input)
    if waypoints is None:
        print("Failed to load OMPL solution")
        return
    
    print(f"Loaded {len(waypoints)} waypoints from {args.input}")
    
    # Choose optimization method
    if args.ultra:
        print("Using ULTRA-aggressive optimization for maximum improvement...")
        result = optimizer.optimize_trajectory_ultra(waypoints, args.iterations)
    elif args.advanced:
        print("Using advanced multi-stage optimization...")
        result = optimizer.optimize_trajectory_advanced(waypoints, args.iterations)
    else:
        print("Using standard optimization...")
        result = optimizer.optimize_trajectory(waypoints, args.iterations)
    
    # Save optimized trajectory
    optimizer.save_trajectory(result, args.output)
    
    # Plot results
    optimizer.plot_trajectory(waypoints, result, args.plot)

if __name__ == '__main__':
    main()
