# Mobile Clinic Optimization with Interactive Dashboard

This module provides PuLP-based optimization and an interactive dashboard for the mobile clinic facility location problem.

## Overview

The optimization solver maximizes population coverage subject to a constraint on the number of mobile units. The interactive dashboard allows you to visualize results, adjust parameters, and re-run optimization in real-time.

## Files

### Optimization Scripts

1. **`optimize_facility_location.py`** - PuLP optimization solver
   - Solves maximal coverage location problem
   - Calculates distance metrics and cost analysis
   - Generates solution files

2. **`visualize_optimization_dashboard.py`** - Interactive Dash dashboard
   - Web-based visualization with Plotly maps
   - Parameter controls (number of units, cost per unit)
   - Real-time optimization execution
   - Summary statistics panel

## Quick Start

### Step 1: Generate Coverage Matrix

```bash
# Generate test data (if needed)
python3 generate_test_data.py

# Create clusters
python3 cluster_children_data.py

# Create coverage matrix (5km radius, 200 units)
python3 create_coverage_matrix.py
```

### Step 2: Run Optimization

```bash
# Run with default parameters (200 units, $10,000 per unit)
python3 optimize_facility_location.py

# Or specify custom parameters
python3 optimize_facility_location.py 150 15000  # 150 units at $15,000 each
```

### Step 3: Launch Interactive Dashboard

```bash
python3 visualize_optimization_dashboard.py
```

Then open your browser to: **http://127.0.0.1:8050**

## Dashboard Features

### Left Panel - Controls

1. **Number of Mobile Units Slider**
   - Range: 10 - 500 units
   - Step: 10 units
   - Default: 200 units

2. **Cost per Unit Input**
   - Enter cost in dollars
   - Default: $10,000

3. **Run Optimization Button**
   - Executes PuLP solver with current parameters
   - Shows progress status
   - Updates map and statistics

### Map Visualization

**Elements:**
- **Gray boundaries**: Malawi Traditional Authorities
- **Green markers**: Covered demand points (size = population)
- **Red markers**: Uncovered demand points
- **Red stars**: Selected mobile unit locations

**Interactions:**
- Hover over markers for details
- Zoom and pan the map
- Click legend to toggle layers

### Summary Panel

**Coverage Metrics:**
- People served (total and percentage)
- Demand points covered / total
- Coverage rate

**Cost Analysis:**
- Total cost
- Cost per unit
- Cost per child served

**Distance Metrics:**
- Mean distance to nearest facility
- Coverage radius

**Performance:**
- Optimization solve time

## Optimization Problem Formulation

### Objective Function

```
Maximize: Σ (population_i × covered_i)
```

Where `covered_i = 1` if demand point i is covered by at least one selected facility

### Constraints

1. **Facility Limit**:
   ```
   Σ x_j = num_facilities
   ```
   Select exactly the specified number of facilities

2. **Coverage Definition**:
   ```
   covered_i ≤ Σ (x_j × a_ij)
   ```
   Where `a_ij = 1` if candidate j can serve demand i (within 5km), 0 otherwise

### Decision Variables

- `x_j ∈ {0, 1}`: Binary variable, 1 if facility placed at candidate site j
- `covered_i ∈ {0, 1}`: Binary variable, 1 if demand point i is covered

## Output Files

After running optimization, the following files are generated:

### 1. `optimal_facility_locations.csv`

Selected facility locations with coverage statistics:

```csv
cluster_id,latitude,longitude,population,selected,facility_id,people_served
169,-15.332761,34.936636,160,True,0,160
482,-10.628651,34.107225,150,True,1,150
...
```

Columns:
- `cluster_id`: Original cluster/site ID
- `latitude`, `longitude`: Geographic coordinates
- `population`: Population at this location
- `selected`: True for selected facilities
- `facility_id`: Facility number (0 to n-1)
- `people_served`: Number of people this facility serves

### 2. `demand_coverage.csv`

Coverage status for all demand points:

```csv
cluster_id,latitude,longitude,population,covered,nearest_facility_id,distance_to_facility_km
0,-16.711945,34.977903,119,True,0,0.0
1,-12.848457,33.565787,94,False,None,None
...
```

Columns:
- `covered`: True if demand point is covered
- `nearest_facility_id`: ID of nearest selected facility
- `distance_to_facility_km`: Distance to nearest facility

### 3. `optimization_solution.json`

Complete solution summary:

```json
{
  "num_facilities": 200,
  "cost_per_unit": 10000.0,
  "total_cost": 2000000.0,
  "covered_population": 24571,
  "coverage_percentage": 24.57,
  "mean_distance_km": 0.0,
  "cost_per_child_served": 81.40,
  "solve_time_seconds": 0.15,
  "selected_site_ids": [0, 4, 5, ...]
}
```

### 4. `optimization_statistics.txt`

Human-readable summary statistics

## Current Results (200 units, 5km radius)

With the current setup:

| Metric | Value |
|--------|-------|
| Facilities placed | 200 |
| Total cost | $2,000,000 |
| Population covered | 24,571 / 100,000 (24.57%) |
| Demand points covered | 200 / 1,000 (20%) |
| Mean distance | 0.00 km* |
| Cost per child | $81.40 |
| Solve time | ~0.15 seconds |

*Note: Mean distance is 0 km because with 5km radius and points spaced 6-10km apart, each facility only covers its own location. See recommendations below.

## Recommendations

### For Better Coverage Overlap

The current 5km radius provides no coverage overlap (see `CURRENT_SETUP_SUMMARY.md`). For a more meaningful optimization:

**Option 1: Increase coverage radius**
```bash
# Edit create_coverage_matrix.py
sed -i 's/buffer_radius_km=5/buffer_radius_km=10/g' create_coverage_matrix.py

# Regenerate coverage matrix
python3 create_coverage_matrix.py

# Run optimization
python3 optimize_facility_location.py
```

**Option 2: Create more clusters (fewer than 1000)**
```bash
# Edit cluster_children_data.py to use fewer clusters (e.g., 200-300)
# This will create larger clusters that are closer together
```

**Option 3: Accept current constraints**
- With 5km radius and 200 units, coverage is straightforward
- Optimization simply selects the 200 highest-population sites
- Suitable if 5km is a hard constraint

## Solver Performance

**CBC Solver (default):**
- Open source MILP solver included with PuLP
- Fast for problems of this size (~0.15 seconds)
- Guaranteed optimal solutions

**For larger problems:**
- Gurobi (commercial, free academic license)
- CPLEX (commercial)
- SCIP (open source)

To use a different solver:
```python
# In optimize_facility_location.py, change:
prob.solve(PULP_CBC_CMD(msg=1, timeLimit=300))

# To:
prob.solve(GUROBI(msg=1, timeLimit=300))
```

## Troubleshooting

### Dashboard won't start

```bash
# Check if port 8050 is already in use
lsof -i :8050

# Or use a different port:
# Edit visualize_optimization_dashboard.py, line:
app.run_server(debug=True, host='0.0.0.0', port=8051)
```

### Optimization takes too long

```bash
# Reduce time limit in optimize_facility_location.py:
prob.solve(PULP_CBC_CMD(msg=1, timeLimit=60))  # 1 minute instead of 5
```

### Out of memory

```bash
# For very large problems, use a smaller coverage matrix
# or reduce the number of demand points/candidates
```

## Advanced Usage

### Running optimization from Python

```python
from optimize_facility_location import main as run_optimization

# Run with custom parameters
solution = run_optimization(num_facilities=150, cost_per_unit=12000)

print(f"Coverage: {solution['coverage_percentage']:.2f}%")
print(f"Total cost: ${solution['total_cost']:,}")
```

### Accessing solution data

```python
import pandas as pd
import json

# Load facility locations
facilities = pd.read_csv('optimal_facility_locations.csv')

# Load solution summary
with open('optimization_solution.json') as f:
    solution = json.load(f)

# Load coverage data
coverage = pd.read_csv('demand_coverage.csv')

# Analyze results
covered = coverage[coverage['covered'] == True]
print(f"Covered: {len(covered)} demand points")
```

## References

- **PuLP Documentation**: https://coin-or.github.io/pulp/
- **Dash Documentation**: https://dash.plotly.com/
- **Facility Location Problems**: Classic operations research optimization problems
- **Maximal Coverage Location Problem (MCLP)**: Church & ReVelle (1974)

## Next Steps

1. **Adjust parameters** using the dashboard
2. **Try different coverage radii** for better overlap
3. **Add constraints** (e.g., minimum coverage requirements)
4. **Multi-objective optimization** (coverage + equity + accessibility)
5. **Scenario analysis** (compare different configurations)
