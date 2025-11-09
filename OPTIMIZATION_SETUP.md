# Facility Location Optimization Setup

This document explains the coverage matrix setup for the mobile clinic optimization problem.

## Problem Overview

**Objective**: Select 30 optimal locations from 1,000 candidate sites to place mobile health clinics that maximize coverage of children under 5 in Malawi.

### Problem Parameters

- **Demand Points**: 1,000 (clustered population centers)
- **Candidate Sites**: 1,000 (same locations as demand points)
- **Mobile Units**: 30 (to be optimally placed)
- **Coverage Radius**: 15 km per mobile unit
- **Total Population**: 100,000 children under 5

## Coverage Matrix Generation

### Step 1: Analyze Distances

Run `analyze_coverage_distances.py` to understand point spacing:

```bash
python3 analyze_coverage_distances.py
```

**Key Findings:**
- Minimum nearest neighbor distance: 6.48 km
- Mean nearest neighbor distance: 9.44 km
- Median nearest neighbor distance: 9.46 km
- **Recommended buffer radius: 15 km** (provides 5-6x coverage overlap)

### Step 2: Create Coverage Matrix

Run `create_coverage_matrix.py` to generate optimization inputs:

```bash
python3 create_coverage_matrix.py
```

**What it does:**
1. Creates 15km circular buffers around each candidate site using shapely
2. Determines which demand points fall within each buffer (spatial intersection)
3. Builds coverage dictionary: `{demand_point_id: [candidate_site_ids]}`
4. Builds reverse dictionary: `{candidate_site_id: [demand_point_ids]}`
5. Calculates total population each candidate site can serve
6. Ranks top 30 sites by population coverage

## Output Files

### For Optimization Algorithms

1. **`coverage_matrix.csv`** (6,360 rows)
   ```csv
   demand_point_id,candidate_site_id
   0,123
   0,0
   0,444
   ...
   ```
   Binary relationship: demand point i is covered by candidate site j

2. **`coverage_dict.json`**
   ```json
   {
     "0": [123, 0, 444, 268, 633],
     "1": [653, 893, 432, 637, 896, 1, 678],
     ...
   }
   ```
   For each demand point: list of candidate sites within 15km

3. **`reverse_coverage_dict.json`**
   ```json
   {
     "0": [0, 123, 268, 444, 633],
     "1": [1, 432, 637, 653, 678, 893, 896],
     ...
   }
   ```
   For each candidate site: list of demand points it can serve

4. **`optimization_input_data.json`**
   - Complete dataset including coordinates, population, coverage relationships
   - Ready to feed into optimization solver

### For Analysis

5. **`candidate_sites_population_coverage.csv`**
   ```csv
   candidate_site_id,total_population_covered
   127,944
   52,936
   319,915
   ...
   ```
   Population each candidate site can serve (sorted descending)

6. **`top_30_candidate_sites.csv`**
   ```csv
   rank,candidate_site_id,population_covered,latitude,longitude,num_demand_points_covered
   1,127,944,-14.023515,34.979059,8
   2,52,936,-15.807231,34.772061,8
   3,319,915,-14.083241,33.446819,8
   ...
   ```
   Top 30 sites by greedy population coverage

7. **`coverage_statistics.txt`**
   - Summary statistics and coverage analysis

## Coverage Matrix Structure

### Matrix Dimensions
- **Rows**: 1,000 demand points
- **Columns**: 1,000 candidate sites
- **Non-zero entries**: 6,360 (63.6% coverage density)

### Coverage Statistics

**Demand Point Perspective:**
- Each demand point is covered by **1-9 candidate sites** (avg: 6.36)
- All 1,000 demand points have at least one candidate within 15km
- No uncovered demand points ✓

**Candidate Site Perspective:**
- Each candidate site can serve **1-9 demand points** (avg: 6.36)
- Population covered per site ranges from **15 to 944 children**
- Average population per site: **638 children**
- Median population per site: **655 children**

## Greedy Baseline Solution

Simply selecting the **top 30 sites by population coverage** (greedy approach):

- **Demand points covered**: 211 / 1,000 (21.1%)
- **Population covered**: 25,745 / 100,000 (25.75%)
- **Uncovered population**: 74,255 children

**Note**: An optimization algorithm should achieve better coverage than this greedy baseline.

## Optimization Problem Formulation

### Set Cover / Maximal Coverage Problem

**Decision Variables:**
- `x_j ∈ {0, 1}` for each candidate site j (1 if selected, 0 otherwise)

**Objective Function:**
```
Maximize: Σ (population_i × coverage_i)
```
where `coverage_i = 1` if demand point i is covered by at least one selected site

**Constraints:**
1. **Facility limit**: `Σ x_j = 30` (select exactly 30 sites)
2. **Coverage**: Demand point i is covered if `Σ (x_j × a_ij) ≥ 1`
   - where `a_ij = 1` if candidate j can serve demand i (within 15km), 0 otherwise

### Alternative Formulation: P-Median Problem

**Objective Function:**
```
Minimize: Σ_i Σ_j (distance_ij × demand_i × x_ij)
```

**Constraints:**
1. `Σ_j x_j = 30` (select 30 facilities)
2. `Σ_j y_ij = 1` for all i (each demand assigned to exactly one facility)
3. `y_ij ≤ x_j` (can only assign to selected facilities)
4. `y_ij = 0` if `distance_ij > 15km` (coverage radius constraint)

## Using the Coverage Data

### Python Example

```python
import json
import pandas as pd

# Load coverage matrix
coverage_df = pd.read_csv('coverage_matrix.csv')

# Load coverage dictionaries
with open('coverage_dict.json') as f:
    demand_to_candidates = json.load(f)

with open('reverse_coverage_dict.json') as f:
    candidate_to_demands = json.load(f)

# Load demand data with population
optimization_data = json.load(open('optimization_input_data.json'))
demand_points = pd.DataFrame(optimization_data['demand_points'])

# Example: Find which candidates can serve demand point 0
candidates_for_demand_0 = demand_to_candidates['0']
print(f"Demand point 0 can be served by sites: {candidates_for_demand_0}")

# Example: Find which demands are served by candidate 127
demands_for_candidate_127 = candidate_to_demands['127']
print(f"Candidate 127 can serve demands: {demands_for_candidate_127}")

# Calculate population served by candidate 127
pop_127 = demand_points[demand_points['cluster_id'].isin(demands_for_candidate_127)]['population'].sum()
print(f"Candidate 127 serves {pop_127} children")
```

### Optimization with PuLP (Python)

```python
from pulp import *
import json
import pandas as pd

# Load data
with open('reverse_coverage_dict.json') as f:
    site_coverage = json.load(f)

demand_df = pd.read_csv('clustered_children_1000.csv')
num_sites = len(demand_df)
num_facilities = 30

# Create optimization problem
prob = LpProblem("Mobile_Clinic_Location", LpMaximize)

# Decision variables
x = LpVariable.dicts("site", range(num_sites), cat='Binary')
y = LpVariable.dicts("covered", range(num_sites), cat='Binary')

# Objective: maximize covered population
prob += lpSum([demand_df.iloc[i]['population'] * y[i] for i in range(num_sites)])

# Constraint: select exactly 30 sites
prob += lpSum([x[j] for j in range(num_sites)]) == num_facilities

# Constraint: demand is covered if at least one covering site is selected
for i in range(num_sites):
    covering_sites = [int(j) for j in site_coverage.get(str(i), [])]
    if covering_sites:
        prob += y[i] <= lpSum([x[j] for j in covering_sites])

# Solve
prob.solve()

# Extract solution
selected_sites = [j for j in range(num_sites) if x[j].varValue == 1]
print(f"Selected sites: {selected_sites}")
```

## Next Steps

1. **Choose optimization approach**:
   - Set Cover (maximize coverage)
   - P-Median (minimize distance)
   - Weighted P-Median (balance coverage and distance)
   - Multi-objective (coverage + equity + accessibility)

2. **Implement solver**:
   - PuLP (Python, open source)
   - Gurobi (commercial, free academic license)
   - OR-Tools (Google, open source)
   - CPLEX (commercial)

3. **Add constraints** (optional):
   - Minimum coverage requirements
   - Maximum distance constraints
   - Regional distribution requirements
   - Budget or resource constraints

4. **Evaluate solution**:
   - Coverage percentage
   - Population served
   - Geographic equity
   - Average distance to nearest facility
   - Maximum distance to nearest facility

## Files Generated

All output files are excluded from git via `.gitignore` and can be regenerated by running the scripts.

To regenerate all coverage data:
```bash
# Generate test data (if needed)
python3 generate_test_data.py

# Create clusters
python3 cluster_children_data.py

# Analyze distances
python3 analyze_coverage_distances.py

# Create coverage matrix
python3 create_coverage_matrix.py
```
