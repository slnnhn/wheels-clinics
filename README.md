# Wheels Clinics - Malawi Population Clustering

This repository contains scripts for analyzing and visualizing population distribution in Malawi using K-means clustering algorithms. The tools help identify optimal locations for mobile health clinics by clustering population data.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
- [Available Scripts](#available-scripts)
- [Data Files](#data-files)
- [Outputs](#outputs)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This project provides tools to:
- Cluster population data for different demographic groups in Malawi
- Visualize population distribution on interactive maps
- Generate optimized cluster centers for service delivery planning
- Create heat maps and density visualizations
- Display Traditional Authorities (administrative) boundaries

## 🔧 Prerequisites

- Python 3.8 or higher
- Git with Git LFS (Large File Storage) support
- Web browser (for viewing interactive maps)

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/slnnhn/wheels-clinics.git
cd wheels-clinics
```

### 2. Set Up Git LFS

The population data files are stored using Git LFS. Install and set up Git LFS:

```bash
# Install Git LFS (if not already installed)
# On Ubuntu/Debian:
sudo apt-get install git-lfs

# On macOS:
brew install git-lfs

# On Windows:
# Download from https://git-lfs.github.com/

# Initialize Git LFS
git lfs install

# Pull the large data files
git lfs pull
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `scikit-learn` - Machine learning (K-means clustering)
- `geopandas` - Geographic data processing
- `matplotlib` - Static visualizations
- `folium` - Interactive maps
- `pulp` - Optimization solver
- `dash` - Interactive dashboards
- `plotly` - Interactive visualizations

## 🚀 One-Command Pipeline

**NEW**: Run the entire optimization pipeline with a single command!

```bash
# Make script executable (first time only)
chmod +x run_optimization_pipeline.sh

# Run complete pipeline with default parameters (200 units, $10k each)
./run_optimization_pipeline.sh

# Or specify custom parameters
./run_optimization_pipeline.sh 150        # 150 units, $10k each
./run_optimization_pipeline.sh 150 15000  # 150 units, $15k each
```

This automated script will:
1. ✅ Check prerequisites and install missing dependencies
2. ✅ Generate test data (if needed)
3. ✅ Create clusters (100k points → 1k demand centers)
4. ✅ Generate coverage matrix (5km radius buffers)
5. ✅ Run PuLP optimization (select optimal facility locations)
6. ✅ Launch interactive dashboard at http://127.0.0.1:8050

**Total runtime**: ~1-2 minutes for complete pipeline

The script includes:
- Progress indicators and colored output
- Interactive prompts for regenerating existing data
- Error handling and validation
- Results summary before launching dashboard

## 📁 Repository Structure

```
wheels-clinics/
├── README.md                              # This file
├── README_CLUSTERING.md                   # Detailed clustering documentation
├── OPTIMIZATION_README.md                 # Optimization documentation
├── QUICK_START_DASHBOARD.md               # Dashboard quick start guide
├── PROJECT_SUMMARY.md                     # Complete project summary
├── requirements.txt                       # Python dependencies
├── run_optimization_pipeline.sh           # ⭐ ONE-COMMAND PIPELINE SCRIPT
├── .gitignore                            # Git ignore rules
│
├── Data Files (Git LFS)
├── mwi_children_under_five_2020.csv      # Children under 5 population
├── mwi_youth_15_24_2020.csv              # Youth population
├── mwi_women_of_reproductive_age_15_49_2020.csv
├── mwi_women_2020.csv                    # Women population
├── mwi_men_2020.csv                      # Men population
├── mwi_elderly_60_plus_2020.csv          # Elderly population
├── malawi_ta_boundaries.geojson          # Administrative boundaries
├── GAIA MHC Clinic Stops GPS.xlsx        # Existing clinic locations
├── MHFR_Facilities.xlsx                  # Health facility data
│
├── Clustering Scripts
├── cluster_children_data.py              # Cluster children population
├── cluster_population.py                 # Cluster all population data
├── generate_test_data.py                 # Generate synthetic test data
│
├── Optimization Scripts
├── create_coverage_matrix.py             # Generate coverage matrix
├── analyze_coverage_distances.py         # Distance analysis
├── optimize_facility_location.py         # PuLP optimization solver
│
└── Visualization Scripts
    ├── visualize_optimization_dashboard.py # Interactive dashboard (Dash)
    ├── visualize_clusters_interactive.py  # Interactive map (Folium)
    ├── visualize_clustered_population.py  # Static maps (Matplotlib)
    └── visualize_ta_boundaries.py         # Administrative boundaries map
```

## 🚀 Quick Start

### Option 1: Complete Optimization Pipeline ⭐ RECOMMENDED

**Run everything with one command:**

```bash
./run_optimization_pipeline.sh
```

This will automatically:
- Generate/verify data
- Create clusters
- Build coverage matrix
- Run optimization
- Launch interactive dashboard

See [One-Command Pipeline](#-one-command-pipeline) section above for details.

### Option 2: Cluster Children Under 5 Population (Manual Steps)

This workflow clusters 100,000 random children data points into 1,000 optimized locations:

```bash
# Step 1: Generate test data (if Git LFS data unavailable)
python3 generate_test_data.py

# Step 2: Run clustering
python3 cluster_children_data.py

# Step 3: Create interactive map
python3 visualize_clusters_interactive.py

# Step 4: Open the map in your browser
open malawi_clusters_interactive.html        # macOS
xdg-open malawi_clusters_interactive.html    # Linux
start malawi_clusters_interactive.html       # Windows
```

**Output:** Interactive HTML map with 1,000 cluster markers, each showing population count on hover

### Option 3: Cluster All Population Data (Manual)

This clusters all demographic groups with a 100:1 reduction ratio:

```bash
# Run clustering on all population files
python3 cluster_population.py

# Visualize the results
python3 visualize_clustered_population.py

# View generated PNG maps in the current directory
```

**Output:** Static PNG maps showing population distribution

### Option 4: View Administrative Boundaries

```bash
# Generate boundary visualization
python3 visualize_ta_boundaries.py

# View generated files:
# - malawi_ta_boundaries_map.png
# - malawi_ta_boundaries_labeled.png
```

## 📜 Available Scripts

### Clustering Scripts

#### `cluster_children_data.py`
**Purpose:** Cluster children under 5 population data
**Sample Size:** 100,000 random points
**Clusters:** 1,000
**Usage:**
```bash
python3 cluster_children_data.py
```
**Outputs:**
- `clustered_children_1000.csv` - Cluster centers with coordinates and population
- `clustered_children_1000_stats.txt` - Clustering statistics

---

#### `cluster_population.py`
**Purpose:** Cluster all population demographic groups
**Reduction:** 100:1 ratio (100 points → 1 cluster)
**Usage:**
```bash
python3 cluster_population.py
```
**Outputs:**
- `clustered_population.csv` - All cluster centers
- `clustered_population_stats.txt` - Statistics

---

#### `generate_test_data.py`
**Purpose:** Generate synthetic test data when Git LFS is unavailable
**Points:** 100,000 within Malawi boundaries
**Usage:**
```bash
python3 generate_test_data.py
```
**Output:**
- `mwi_children_under_five_2020_test.csv` - Synthetic data

---

### Visualization Scripts

#### `visualize_clusters_interactive.py`
**Purpose:** Create interactive Folium map with tooltips
**Features:**
- Hover tooltips showing population counts
- Click markers for detailed information
- Multiple map layers (street, light, dark)
- Heatmap overlay
- Administrative boundaries
- Legend with statistics
- Fullscreen mode

**Usage:**
```bash
python3 visualize_clusters_interactive.py
```
**Output:**
- `malawi_clusters_interactive.html` - Interactive map

---

#### `visualize_clustered_population.py`
**Purpose:** Create static matplotlib visualizations
**Outputs:** Multiple PNG maps with different visualization styles

**Usage:**
```bash
python3 visualize_clustered_population.py
```
**Outputs:**
- `malawi_population_clusters.png` - Population-weighted visualization
- `malawi_population_density.png` - Density categories
- `malawi_population_simple.png` - Simple cluster overlay

---

#### `visualize_ta_boundaries.py`
**Purpose:** Visualize Malawi's Traditional Authorities boundaries

**Usage:**
```bash
python3 visualize_ta_boundaries.py
```
**Outputs:**
- `malawi_ta_boundaries_map.png` - Boundaries map
- `malawi_ta_boundaries_labeled.png` - Map with labels

---

## 📊 Data Files

### Population Data (Git LFS)

All population CSV files contain geographic coordinates:
- `mwi_children_under_five_2020.csv` - ~2.3M children under 5
- `mwi_youth_15_24_2020.csv` - Youth population
- `mwi_women_of_reproductive_age_15_49_2020.csv` - Women 15-49
- `mwi_women_2020.csv` - All women
- `mwi_men_2020.csv` - All men
- `mwi_elderly_60_plus_2020.csv` - Elderly 60+

**Columns:** `longitude`, `latitude`, `x`, `y`

### Geographic Data

- `malawi_ta_boundaries.geojson` - Traditional Authorities boundaries (245 TAs)
- `GAIA MHC Clinic Stops GPS.xlsx` - Existing clinic GPS locations
- `MHFR_Facilities.xlsx` - Health facility registry data

## 📤 Outputs

### Cluster Data Format

All cluster CSV files contain:
```csv
cluster_id,latitude,longitude,population
0,-16.711945,34.977903,119
1,-12.848457,33.565787,94
...
```

- **cluster_id**: Unique identifier (0 to n-1)
- **latitude**: Cluster center latitude
- **longitude**: Cluster center longitude
- **population**: Number of people in this cluster

### Interactive Map Features

The HTML maps include:
- **Tooltips**: Hover over markers to see population
- **Popups**: Click for detailed cluster information
- **Layer Control**: Toggle different visualizations
- **Heatmap**: Population density overlay
- **Boundaries**: Administrative boundaries
- **Legend**: Statistics and color coding
- **Tools**: Fullscreen, measure, mouse position

## 🔍 Troubleshooting

### Git LFS Issues

**Problem:** CSV files show as small pointer files (134 bytes)

**Solution:**
```bash
# Install and initialize Git LFS
git lfs install

# Pull the actual data
git lfs pull
```

**Alternative:** Use test data generator
```bash
python3 generate_test_data.py
```

### Missing Dependencies

**Problem:** `ModuleNotFoundError: No module named 'X'`

**Solution:**
```bash
pip install -r requirements.txt

# Or install individual packages:
pip install pandas numpy scikit-learn geopandas matplotlib folium
```

### Clustering Takes Too Long

**Problem:** Script runs for a very long time

**Solution:** The scripts use MiniBatchKMeans which is optimized for large datasets. Typical run times:
- 100,000 points → 1,000 clusters: ~30 seconds
- 2,000,000 points → 20,000 clusters: ~5 minutes

You can reduce sample size or cluster count in the scripts.

### Interactive Map Won't Open

**Problem:** HTML file doesn't open in browser

**Solution:**
```bash
# Manually open with browser
# macOS
open malawi_clusters_interactive.html

# Linux
xdg-open malawi_clusters_interactive.html

# Windows
start malawi_clusters_interactive.html

# Or drag and drop the HTML file into your browser
```

## 📖 Additional Documentation

For detailed information about the clustering algorithms and advanced usage, see:
- [README_CLUSTERING.md](README_CLUSTERING.md) - Comprehensive clustering documentation

## 🤝 Contributing

When adding new features:
1. Create a new branch from main
2. Add your scripts and update this README
3. Test with both real and synthetic data
4. Update requirements.txt if new dependencies are added
5. Submit a pull request

## 📝 License

[Add your license information here]

## 👥 Authors

Created for the Wheels Clinics project to optimize mobile health clinic deployment in Malawi.

---

**Questions or Issues?** Please open an issue on GitHub or contact the project maintainers.
