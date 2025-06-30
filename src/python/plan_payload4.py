import sys
sys.path.insert(0, "/home/user_136/dynoplan/dynobench/src")  # Adjust if needed

import dynobench.robots.payload as payload_module
from dynobench.planners.dbastar import Planner as DBAstarPlanner
from dynobench.planners.utils import save_result_to_yaml

# Create robot/environment
env = payload_module.PayloadFourDrones()
env.start = [-10, -40, 20, 0, 0, 0, 1]
env.goal  = [10, -40, 20, 0, 0, 0, 1]

# Create planner
planner = DBAstarPlanner(env)

# Optional tuning
planner.max_it = 5000
planner.delta = 0.2
planner.num_primitives = 300
planner.use_collision_shape = False

# Run planner
print("🚀 Running planner...")
success = planner.run()

if success:
    print("✅ Planning successful!")
    save_result_to_yaml(planner.get_result(), "solution_guess.yaml")
    print("💾 Saved to solution_guess.yaml")
else:
    print("❌ Planner failed to find a solution.")
