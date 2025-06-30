#!/bin/bash

# Setup script for integrating PayloadFourDrones with Dynoplan

echo "🔧 Setting up PayloadFourDrones + Dynoplan integration..."

# Define paths
PROJECT_DIR="/home/user_136/Desktop/Project-A"
DYNOPLAN_DIR="/home/user_136/dynoplan"
BUILD_DIR="$PROJECT_DIR/build"

# Check if Dynoplan exists
if [ ! -d "$DYNOPLAN_DIR" ]; then
    echo "❌ Dynoplan not found at $DYNOPLAN_DIR"
    echo "Please clone and build Dynoplan first:"
    echo "  git clone https://github.com/quimortiz/dynoplan.git /home/user_136/dynoplan"
    echo "  cd /home/user_136/dynoplan"
    echo "  mkdir build && cd build"
    echo "  cmake .. && make"
    exit 1
fi

# Check if Dynoplan is built
if [ ! -f "$DYNOPLAN_DIR/build/test/main_tdbastar" ]; then
    echo "❌ Dynoplan not built. Please build it first:"
    echo "  cd $DYNOPLAN_DIR/build"
    echo "  make"
    exit 1
fi

# Check if PayloadFourDrones solution exists
if [ ! -f "$BUILD_DIR/solution_path.txt" ]; then
    echo "⚠️  No PayloadFourDrones solution found at $BUILD_DIR/solution_path.txt"
    echo "Please run your PayloadFourDrones planner first:"
    echo "  cd $BUILD_DIR"
    echo "  ./PayloadFourDrones"
    echo ""
    echo "After that, you can run the optimization."
else
    echo "✅ Found PayloadFourDrones solution"
fi

# Make optimization script executable
chmod +x "$PROJECT_DIR/src/python/optimize_payload_simple.py"

echo ""
echo "🎯 Setup complete! To optimize your trajectory:"
echo "  1. First run your PayloadFourDrones planner:"
echo "     cd $BUILD_DIR && ./PayloadFourDrones"
echo ""
echo "  2. Then optimize with Dynoplan:"
echo "     cd $PROJECT_DIR"
echo "     python3 src/python/optimize_payload_simple.py"
echo ""
echo "📚 Alternative: Use Dynoplan's native payload planner:"
echo "     python3 src/python/plan_payload4.py"
echo ""
echo "🔗 Dynoplan repository: https://github.com/quimortiz/dynoplan"
