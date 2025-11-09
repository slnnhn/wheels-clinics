#!/bin/bash
################################################################################
# Mobile Clinic Optimization Pipeline
#
# This script runs the complete optimization pipeline:
# 1. Generate test data (if needed)
# 2. Create clusters (K-means)
# 3. Generate coverage matrix
# 4. Run optimization
# 5. Launch interactive dashboard
#
# Usage:
#   ./run_optimization_pipeline.sh [num_units] [cost_per_unit]
#
# Examples:
#   ./run_optimization_pipeline.sh              # Default: 200 units, $10,000 each
#   ./run_optimization_pipeline.sh 150          # 150 units, $10,000 each
#   ./run_optimization_pipeline.sh 150 15000    # 150 units, $15,000 each
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default parameters
NUM_UNITS=${1:-200}
COST_PER_UNIT=${2:-10000}

# Functions
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_step() {
    echo -e "\n${GREEN}▶ $1${NC}\n"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed or not in PATH"
        exit 1
    fi
}

# Start
clear
print_header "Mobile Clinic Optimization Pipeline"
echo ""
echo "Configuration:"
echo "  Number of mobile units: $NUM_UNITS"
echo "  Cost per unit: \$$COST_PER_UNIT"
echo "  Total budget: \$$((NUM_UNITS * COST_PER_UNIT))"
echo ""

# Check prerequisites
print_step "Checking prerequisites..."
check_command python3
check_command pip

# Check Python packages
print_step "Checking Python dependencies..."
python3 -c "import pandas, numpy, sklearn, geopandas, pulp, dash" 2>/dev/null
if [ $? -ne 0 ]; then
    print_warning "Some Python packages are missing. Installing..."
    pip install -r requirements.txt
    print_success "Dependencies installed"
else
    print_success "All dependencies are installed"
fi

# Step 1: Check for data or generate test data
print_header "Step 1: Data Preparation"

if [ -f "clustered_children_1000.csv" ]; then
    print_success "Clustered data already exists (clustered_children_1000.csv)"
    read -p "Do you want to regenerate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        REGENERATE=true
    else
        REGENERATE=false
    fi
else
    REGENERATE=true
fi

if [ "$REGENERATE" = true ]; then
    # Check if raw data exists
    if [ ! -f "mwi_children_under_five_2020.csv" ] || [ $(wc -c < "mwi_children_under_five_2020.csv") -lt 1000 ]; then
        print_warning "Raw data not available (Git LFS file)"
        print_step "Generating synthetic test data..."
        python3 generate_test_data.py
        if [ $? -eq 0 ]; then
            print_success "Test data generated"
        else
            print_error "Failed to generate test data"
            exit 1
        fi
    fi

    # Step 2: Create clusters
    print_header "Step 2: K-means Clustering"
    print_step "Clustering 100,000 points into 1,000 demand centers..."
    python3 cluster_children_data.py
    if [ $? -eq 0 ]; then
        print_success "Clustering complete"
    else
        print_error "Clustering failed"
        exit 1
    fi
fi

# Step 3: Generate coverage matrix
print_header "Step 3: Coverage Matrix Generation"

if [ -f "coverage_matrix.csv" ] && [ -f "coverage_dict.json" ]; then
    print_success "Coverage matrix already exists"
    read -p "Do you want to regenerate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        REGENERATE_COVERAGE=true
    else
        REGENERATE_COVERAGE=false
    fi
else
    REGENERATE_COVERAGE=true
fi

if [ "$REGENERATE_COVERAGE" = true ]; then
    print_step "Creating 5km coverage buffers and matrix..."
    python3 create_coverage_matrix.py
    if [ $? -eq 0 ]; then
        print_success "Coverage matrix created"
    else
        print_error "Coverage matrix generation failed"
        exit 1
    fi
fi

# Step 4: Run optimization
print_header "Step 4: Optimization"
print_step "Running PuLP solver with $NUM_UNITS units at \$$COST_PER_UNIT each..."
python3 optimize_facility_location.py $NUM_UNITS $COST_PER_UNIT
if [ $? -eq 0 ]; then
    print_success "Optimization complete"
else
    print_error "Optimization failed"
    exit 1
fi

# Display results summary
print_header "Optimization Results"
if [ -f "optimization_solution.json" ]; then
    python3 << 'EOF'
import json
with open('optimization_solution.json') as f:
    sol = json.load(f)
print(f"\n✓ Facilities placed: {sol['num_facilities']}")
print(f"✓ People covered: {sol['covered_population']:,} / {sol['total_population']:,} ({sol['coverage_percentage']:.2f}%)")
print(f"✓ Total cost: ${sol['total_cost']:,}")
print(f"✓ Cost per child served: ${sol['cost_per_child_served']:.2f}")
print(f"✓ Mean distance: {sol['mean_distance_km']:.2f} km")
print(f"✓ Solve time: {sol['solve_time_seconds']:.2f} seconds\n")
EOF
fi

# Step 5: Launch dashboard
print_header "Step 5: Interactive Dashboard"
echo ""
echo "The optimization pipeline is complete!"
echo ""
echo "Generated files:"
echo "  ✓ clustered_children_1000.csv"
echo "  ✓ coverage_matrix.csv"
echo "  ✓ optimal_facility_locations.csv"
echo "  ✓ demand_coverage.csv"
echo "  ✓ optimization_solution.json"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Ready to launch dashboard!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
read -p "Launch interactive dashboard now? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    print_step "Starting dashboard server..."
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Dashboard will be available at: http://127.0.0.1:8050${NC}"
    echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    python3 visualize_optimization_dashboard.py
else
    echo ""
    print_success "Pipeline complete! To launch dashboard later, run:"
    echo "  python3 visualize_optimization_dashboard.py"
    echo ""
fi
