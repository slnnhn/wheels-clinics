# Current Optimization Setup Summary

## Updated Parameters (Latest Configuration)

**Problem Configuration:**
- **Number of mobile units**: 200
- **Coverage radius**: 5 km per unit
- **Demand points**: 1,000 (clustered children population centers)
- **Candidate sites**: 1,000 (same as demand points)
- **Total population**: 100,000 children under 5

## Coverage Matrix Results (5km radius)

### Coverage Statistics
- **Total coverage relationships**: 1,000
- **Average coverage overlap**: 1.00x (no overlap)
- Each demand point is covered by exactly **1 candidate site** (itself)
- Each candidate site can serve exactly **1 demand point** (itself)

### Why No Overlap?
The cluster points are more spread out than the 5km radius:
- Minimum nearest neighbor distance: **6.48 km**
- Mean distance between points: **9.44 km**
- Median distance between points: **9.46 km**

With 5km radius, no two clusters overlap since they are at least 6.48km apart.

### Greedy Baseline Coverage
If we simply select the **top 200 sites** by population:
- **Population covered**: 24,571 / 100,000 (24.57%)
- **Demand points covered**: 200 / 1,000 (20%)
- **Uncovered population**: 75,429 children

## Comparison: 5km vs 15km Radius

| Parameter | 5km Radius | 15km Radius |
|-----------|------------|-------------|
| Coverage relationships | 1,000 | 6,360 |
| Avg coverage overlap | 1.00x | 6.36x |
| Candidates per demand | 1 | 6.36 |
| Top 200 coverage | 24.57% | N/A* |
| Top 30 coverage | 4.15% | 25.75% |

*Not tested with 15km and 200 units

## Implications for Optimization

### With 5km Radius (Current)
**Advantages:**
- Simpler problem - no overlap means straightforward selection
- Each site serves a unique location
- No redundancy in coverage

**Disadvantages:**
- **No flexibility** - optimization becomes trivial (just rank by population)
- Cannot balance coverage across regions
- No trade-offs between sites (they don't compete)
- Poor coverage with 200 units (only 24.57%)

**Optimization Strategy:**
Since there's no overlap, the optimal solution is simply:
1. Sort all 1,000 sites by population (descending)
2. Select the top 200 sites
3. Result: 24.57% coverage guaranteed

### With 15km Radius (Previous)
**Advantages:**
- **6.36x coverage overlap** provides optimization flexibility
- Can balance coverage, distance, and equity
- Sites compete for coverage, enabling trade-offs
- Better overall coverage potential

**Disadvantages:**
- More complex optimization problem
- Longer service distances (up to 15km)

## Recommendations

### Option 1: Keep 5km radius + 200 units
If 5km is a hard constraint (e.g., maximum acceptable travel distance):
- Accept that optimization is straightforward (greedy selection)
- Coverage will be limited to ~24.57%
- Consider increasing number of units or accepting lower coverage

### Option 2: Increase to 10km radius + 200 units
Balances coverage and distance:
- Would provide some overlap (1-4 candidates per point)
- Enables meaningful optimization
- Still reasonable travel distances

### Option 3: Use 15km radius + 200 units
Maximizes coverage and optimization potential:
- High coverage overlap (6+ candidates per point)
- Rich optimization problem
- Could achieve 50-60%+ coverage with 200 units
- Longer service distances

## Generated Files (Current: 5km, 200 units)

All files reflect the current 5km radius and 200 mobile units:

1. **coverage_matrix.csv** - 1,000 rows (each point covers itself)
2. **coverage_dict.json** - Each demand point has 1 candidate
3. **reverse_coverage_dict.json** - Each candidate serves 1 demand point
4. **top_200_candidate_sites.csv** - Top 200 sites by population
5. **optimization_input_data.json** - Complete dataset for solver
6. **coverage_statistics.txt** - Summary statistics

## Next Steps

**To regenerate with different parameters:**

```bash
# Edit create_coverage_matrix.py and change:
# Line ~79: buffer_radius_km=5  (change radius)
# Line ~322: 'num_mobile_units': 200  (change number of units)

# Then run:
python3 create_coverage_matrix.py
```

**Recommended for better optimization:**
```bash
# Try 10km radius for balanced coverage
sed -i 's/buffer_radius_km=5/buffer_radius_km=10/g' create_coverage_matrix.py
python3 create_coverage_matrix.py
```

This will provide ~2-3x coverage overlap, enabling meaningful optimization while keeping reasonable service distances.
