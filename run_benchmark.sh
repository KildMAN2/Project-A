#!/bin/bash
# Multi-Scenario Trajectory Optimization Benchmark Runner
# ====================================================
# 
# This script runs comprehensive benchmarks of trajectory optimization
# across multiple scenarios with different environments and objectives.

set -e  # Exit on any error

# Configuration
WORKSPACE="/home/user_136/Desktop/Project-A"
PYTHON_CMD="/home/user_136/anaconda3/envs/ompl-env/bin/python3"
BENCHMARK_SCRIPT="$WORKSPACE/src/python/multi_scenario_benchmark.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}================================================${NC}"
    echo -e "${CYAN}🚀 Multi-Scenario Trajectory Optimization Benchmark${NC}"
    echo -e "${CYAN}================================================${NC}"
}

print_section() {
    echo -e "\n${BLUE}$1${NC}"
    echo -e "${BLUE}$(printf '=%.0s' {1..50})${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_section "Checking Prerequisites"
    
    # Check Python environment
    if [ ! -f "$PYTHON_CMD" ]; then
        print_error "Python environment not found: $PYTHON_CMD"
        exit 1
    fi
    print_success "Python environment found"
    
    # Check workspace
    if [ ! -d "$WORKSPACE" ]; then
        print_error "Workspace not found: $WORKSPACE"
        exit 1
    fi
    print_success "Workspace found"
    
    # Check if OMPL solution exists
    if [ ! -f "$WORKSPACE/solution_path.txt" ]; then
        print_warning "OMPL solution not found. Generating..."
        cd "$WORKSPACE/build"
        if [ -f "./PayloadFourDrones" ]; then
            ./PayloadFourDrones > /dev/null 2>&1 || print_warning "PayloadFourDrones execution had warnings"
            if [ -f "$WORKSPACE/solution_path.txt" ]; then
                print_success "OMPL solution generated"
            else
                print_error "Failed to generate OMPL solution"
                exit 1
            fi
        else
            print_error "PayloadFourDrones executable not found. Please build the project first."
            exit 1
        fi
    else
        print_success "OMPL solution found"
    fi
    
    # Check benchmark script
    if [ ! -f "$BENCHMARK_SCRIPT" ]; then
        print_error "Benchmark script not found: $BENCHMARK_SCRIPT"
        exit 1
    fi
    print_success "Benchmark script found"
    
    # Install Python dependencies
    print_section "Installing Python Dependencies"
    $PYTHON_CMD -m pip install pandas matplotlib seaborn > /dev/null 2>&1 || print_warning "Some packages may already be installed"
    print_success "Dependencies checked"
}

# Function to run quick benchmark (subset of scenarios)
run_quick_benchmark() {
    print_section "Running Quick Benchmark"
    echo "Testing core functionality with representative scenarios..."
    
    cd "$WORKSPACE"
    $PYTHON_CMD "$BENCHMARK_SCRIPT" --quick
    
    print_success "Quick benchmark completed"
}

# Function to run full benchmark
run_full_benchmark() {
    print_section "Running Full Benchmark Suite"
    echo "Testing all scenarios and optimization methods..."
    echo "⏱️  This may take 10-30 minutes depending on your system."
    
    cd "$WORKSPACE"
    $PYTHON_CMD "$BENCHMARK_SCRIPT"
    
    print_success "Full benchmark completed"
}

# Function to run custom benchmark
run_custom_benchmark() {
    print_section "Running Custom Benchmark"
    echo "Available scenarios:"
    echo "  • open_space_simple     - Simple open space baseline"
    echo "  • open_space_long       - Long distance traversal"
    echo "  • sparse_obstacles      - Few scattered obstacles"
    echo "  • dense_obstacles       - Complex obstacle navigation"
    echo "  • narrow_corridor       - Tight corridor navigation"
    echo "  • multi_level          - Multi-altitude navigation"
    echo "  • ompl_original        - Original OMPL scenario"
    echo "  • extreme_challenge    - Most difficult scenario"
    echo ""
    echo "Available optimizations:"
    echo "  • shortest_path        - Minimize distance"
    echo "  • minimal_energy       - Minimize energy consumption"
    echo "  • smoothest           - Minimize acceleration/jerk"
    echo "  • time_optimal        - Minimize time"
    echo "  • balanced            - Balanced optimization"
    echo "  • conservative        - Safe, conservative optimization"
    echo ""
    
    read -p "Enter scenarios (space-separated, or press Enter for all): " scenarios
    read -p "Enter optimizations (space-separated, or press Enter for all): " optimizations
    
    cd "$WORKSPACE"
    if [ -n "$scenarios" ] && [ -n "$optimizations" ]; then
        $PYTHON_CMD "$BENCHMARK_SCRIPT" --scenarios $scenarios --optimizations $optimizations
    elif [ -n "$scenarios" ]; then
        $PYTHON_CMD "$BENCHMARK_SCRIPT" --scenarios $scenarios
    elif [ -n "$optimizations" ]; then
        $PYTHON_CMD "$BENCHMARK_SCRIPT" --optimizations $optimizations
    else
        $PYTHON_CMD "$BENCHMARK_SCRIPT"
    fi
    
    print_success "Custom benchmark completed"
}

# Function to show results
show_results() {
    print_section "Benchmark Results"
    
    RESULTS_DIR="$WORKSPACE/benchmark_results"
    
    if [ -d "$RESULTS_DIR" ]; then
        echo "📊 Results available in: $RESULTS_DIR"
        echo ""
        
        # Show report if available
        if [ -f "$RESULTS_DIR/benchmark_report.txt" ]; then
            echo "📄 Latest Benchmark Report:"
            echo "$(head -n 30 "$RESULTS_DIR/benchmark_report.txt")"
            echo ""
            echo "📄 Full report: $RESULTS_DIR/benchmark_report.txt"
        fi
        
        # List result files
        echo "📁 Available result files:"
        ls -la "$RESULTS_DIR"/*.json "$RESULTS_DIR"/*.png "$RESULTS_DIR"/*.txt 2>/dev/null || echo "No result files found"
        
    else
        print_warning "No benchmark results found. Please run a benchmark first."
    fi
}

# Function to clean results
clean_results() {
    print_section "Cleaning Results"
    
    RESULTS_DIR="$WORKSPACE/benchmark_results"
    
    if [ -d "$RESULTS_DIR" ]; then
        read -p "⚠️  This will delete all benchmark results. Continue? (y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            rm -rf "$RESULTS_DIR"
            print_success "Results cleaned"
        else
            echo "Cancelled"
        fi
    else
        print_warning "No results directory found"
    fi
}

# Function to show help
show_help() {
    print_header
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  quick      Run quick benchmark (3 scenarios, 3 optimizations)"
    echo "  full       Run full benchmark suite (all scenarios and optimizations)"
    echo "  custom     Run custom benchmark with user-selected scenarios"
    echo "  results    Show latest benchmark results"
    echo "  clean      Clean all benchmark results"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 quick                    # Quick test"
    echo "  $0 full                     # Complete benchmark"
    echo "  $0 custom                   # Interactive selection"
    echo "  $0 results                  # View results"
    echo ""
    echo "Benchmark Features:"
    echo "  🎯 Multiple Scenarios: Open space, obstacles, corridors, multi-level"
    echo "  ⚡ Multiple Objectives: Shortest path, energy optimal, smooth, time optimal"
    echo "  📊 Comprehensive Analysis: Performance metrics, visualizations, reports"
    echo "  🔍 Real-world Testing: Different obstacle densities and complexities"
}

# Main script logic
main() {
    case "${1:-help}" in
        "quick")
            print_header
            check_prerequisites
            run_quick_benchmark
            show_results
            ;;
        "full")
            print_header
            check_prerequisites
            run_full_benchmark
            show_results
            ;;
        "custom")
            print_header
            check_prerequisites
            run_custom_benchmark
            show_results
            ;;
        "results")
            print_header
            show_results
            ;;
        "clean")
            print_header
            clean_results
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
