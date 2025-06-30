#!/bin/bash

# Configuration
VENV_DIR="venv"  # Name of the virtual environment directory
PROJECT_SOURCE_DIR="/home/user_136/Desktop/OMPL_DRONES"  # Path to your CMake project

echo "===== Setting up virtual environment ====="

# 1. Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment. Exiting."
        exit 1
    fi
else
    echo "Virtual environment already exists."
fi

# 2. Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# 3. Upgrade pip (optional but recommended)
echo "Upgrading pip..."
pip install --upgrade pip

# 4. Install numpy if not installed
echo "Checking if NumPy is installed..."
python3 -c "import numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "NumPy not found. Installing NumPy..."
    pip install numpy
else
    echo "NumPy already installed."
fi

# 5. Prepare a clean build directory
echo "Preparing clean build directory..."
BUILD_DIR="build"
rm -rf "$BUILD_DIR"
mkdir "$BUILD_DIR"
cd "$BUILD_DIR"

# 6. Run cmake
echo "Running cmake..."
cmake "$PROJECT_SOURCE_DIR"

# 7. Done
echo "===== Setup complete! You can now run 'make' ====="

