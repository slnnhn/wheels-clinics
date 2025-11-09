# Quick Start: Mobile Clinic Optimization Dashboard

## 🚀 Launch Dashboard in 3 Steps

### Step 1: Ensure Data is Ready

```bash
# Check if clustering and coverage files exist
ls clustered_children_1000.csv coverage_dict.json

# If missing, generate them:
python3 generate_test_data.py
python3 cluster_children_data.py
python3 create_coverage_matrix.py
```

### Step 2: Run Initial Optimization (Optional)

```bash
# Run optimization with default parameters (200 units, $10k each)
python3 optimize_facility_location.py

# This will generate:
# ✓ optimal_facility_locations.csv
# ✓ demand_coverage.csv
# ✓ optimization_solution.json
# ✓ optimization_statistics.txt
```

### Step 3: Launch Dashboard

```bash
python3 visualize_optimization_dashboard.py
```

Then open your browser to: **http://127.0.0.1:8050**

## 🎯 Using the Dashboard

### Controls (Left Panel)

1. **Adjust Number of Units**
   - Drag slider: 10 to 500 units
   - Default: 200 units

2. **Set Cost per Unit**
   - Enter amount in dollars
   - Default: $10,000

3. **Run Optimization**
   - Click "▶️ Run Optimization" button
   - Wait for status message (usually < 1 minute)
   - Map and statistics will auto-update

### Map Features

**Legend:**
- 🟢 **Green circles** = Covered demand points (hover for population)
- 🔴 **Red circles** = Uncovered demand points
- ⭐ **Red stars** = Selected mobile unit locations
- Gray polygons = Malawi administrative boundaries

**Interactions:**
- **Hover** over markers to see details
- **Zoom** with scroll wheel or +/- buttons
- **Pan** by clicking and dragging
- **Toggle layers** by clicking legend items

### Summary Panel (Left Side, Bottom)

Shows real-time statistics:

📊 **Coverage Metrics**
- People served (count and %)
- Demand points covered

💰 **Cost Analysis**
- Total cost
- Cost per unit
- Cost per child served

📍 **Distance Metrics**
- Mean distance to nearest facility
- Coverage radius

⏱️ **Performance**
- Optimization solve time

## 📊 Example Scenarios

### Scenario 1: Limited Budget (100 units)

```bash
1. Set slider to 100 units
2. Keep cost at $10,000
3. Click "Run Optimization"

Expected Results:
- Coverage: ~12-13% of population
- Total cost: $1,000,000
- Solve time: < 1 second
```

### Scenario 2: Maximum Coverage (400 units)

```bash
1. Set slider to 400 units
2. Set cost to $8,000
3. Click "Run Optimization"

Expected Results:
- Coverage: ~40% of population
- Total cost: $3,200,000
- Better geographic distribution
```

### Scenario 3: High Unit Cost

```bash
1. Set units to 200
2. Set cost to $50,000
3. Click "Run Optimization"

Expected Results:
- Same coverage (24.57%)
- Higher total cost: $10,000,000
- Higher cost per child served
```

## 📁 Generated Files

After running optimization, check these files:

```bash
# View selected facility locations
head optimal_facility_locations.csv

# Check which demands are covered
head demand_coverage.csv

# See summary statistics
cat optimization_solution.json

# Read full report
cat optimization_statistics.txt
```

## 🔧 Troubleshooting

### Dashboard won't start

```bash
# Check if port 8050 is in use
sudo lsof -i :8050

# Kill existing process if needed
kill -9 <PID>

# Or change port in code (line 275 of visualize_optimization_dashboard.py)
```

### "No module named 'dash'" error

```bash
pip install dash plotly pulp
```

### Optimization is slow

```bash
# Normal for first run (generates distance matrix)
# Subsequent runs are faster (< 1 minute)

# For very large problems, reduce time limit:
# Edit optimize_facility_location.py line ~123:
# prob.solve(PULP_CBC_CMD(msg=1, timeLimit=60))
```

### Map not showing

```bash
# Check if data files exist:
ls clustered_children_1000.csv malawi_ta_boundaries.geojson

# Regenerate if needed:
python3 cluster_children_data.py
```

## 🎨 Customization

### Change Map Style

Edit `visualize_optimization_dashboard.py` line ~113:

```python
mapbox=dict(
    style='open-street-map',  # Try: 'carto-positron', 'carto-darkmatter'
    ...
)
```

### Adjust Coverage Radius

To change from 5km to 10km:

```bash
# 1. Update coverage matrix generator
sed -i 's/buffer_radius_km=5/buffer_radius_km=10/g' create_coverage_matrix.py

# 2. Regenerate coverage matrix
python3 create_coverage_matrix.py

# 3. Run optimization
python3 optimize_facility_location.py

# 4. View in dashboard
python3 visualize_optimization_dashboard.py
```

### Change Default Parameters

Edit `visualize_optimization_dashboard.py`:

```python
# Line ~190: Change default units
value=300,  # Instead of 200

# Line ~199: Change default cost
value=15000,  # Instead of 10000
```

## 💡 Pro Tips

1. **Start with small numbers** (50-100 units) to test quickly
2. **Compare scenarios** by taking screenshots
3. **Export results** using the generated CSV files
4. **Monitor solve time** - if > 1 minute, consider reducing problem size
5. **Check coverage percentage** - aim for > 50% with adequate units

## 📊 Understanding the Results

### Current Setup (5km radius, no overlap)

- Each facility only covers its own location
- Optimization is equivalent to greedy selection
- 200 units cover exactly 200 demand points (20%)

### Why Coverage is Limited

- **5km radius** < **6.48km minimum spacing** = no overlap
- See `CURRENT_SETUP_SUMMARY.md` for details
- Solution: Increase radius or use fewer clusters

### Improving Coverage

**Option 1: Increase radius to 10km**
- Provides 2-3x coverage overlap
- Each demand has multiple facility options
- Better optimization flexibility
- 200 units could cover 30-40%

**Option 2: Increase radius to 15km**
- Provides 6x coverage overlap
- Rich optimization problem
- 200 units could cover 50-60%
- Longer travel distances

## 📞 Support

For issues or questions:
1. Check `OPTIMIZATION_README.md` for detailed docs
2. Review `OPTIMIZATION_SETUP.md` for problem formulation
3. See `CURRENT_SETUP_SUMMARY.md` for current configuration
4. Check GitHub issues

## 🎓 Next Steps

1. ✅ Run dashboard and explore different scenarios
2. ✅ Try different numbers of units and costs
3. ✅ Export and analyze solution files
4. ✅ Adjust coverage radius for better overlap
5. ✅ Implement additional constraints (budget, equity, etc.)
6. ✅ Add multi-objective optimization

---

**Dashboard URL**: http://127.0.0.1:8050

**Stop server**: Press `Ctrl+C` in terminal

**Restart**: Re-run `python3 visualize_optimization_dashboard.py`
