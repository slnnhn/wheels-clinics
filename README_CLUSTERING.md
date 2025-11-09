# K-means Clustering for Malawi Children Under 5 Population

This directory contains scripts for clustering population data for children under 5 in Malawi using K-means algorithm.

## Overview

The clustering pipeline performs the following:
1. Samples 100,000 random data points from the children under 5 population dataset
2. Clusters them into 1,000 cluster centers using K-means algorithm
3. Each cluster contains coordinates (latitude, longitude) and the number of data points it represents
4. Creates an interactive map visualization with tooltips showing population counts

## Scripts

### 1. `generate_test_data.py`
Generates synthetic test data for demonstration purposes when Git LFS data is unavailable.

**Usage:**
```bash
python3 generate_test_data.py
```

**Output:**
- `mwi_children_under_five_2020_test.csv` - 100,000 synthetic data points within Malawi boundaries

### 2. `cluster_children_data.py`
Main clustering script that samples random points and performs K-means clustering.

**Features:**
- Loads children under 5 population data
- Samples 100,000 random points (or uses all if less than 100,000)
- Clusters into 1,000 centers using MiniBatchKMeans
- Automatically falls back to test data if main CSV is unavailable

**Usage:**
```bash
python3 cluster_children_data.py
```

**Output:**
- `clustered_children_1000.csv` - 1,000 cluster centers with coordinates and population counts
- `clustered_children_1000_stats.txt` - Statistics about the clustering

### 3. `visualize_clusters_interactive.py`
Creates an interactive Folium map with cluster markers and tooltips.

**Features:**
- Interactive map with hover tooltips showing population counts
- Click markers for detailed cluster information
- Multiple map layers (OpenStreetMap, Light, Dark)
- Heatmap overlay (can be toggled)
- Malawi Traditional Authorities boundaries
- Legend with statistics
- Fullscreen mode
- Measure tool
- Mouse position display

**Usage:**
```bash
python3 visualize_clusters_interactive.py
```

**Output:**
- `malawi_clusters_interactive.html` - Interactive map (open in web browser)

## Requirements

Install the required Python packages:
```bash
pip install pandas numpy scikit-learn geopandas folium
```

## Quick Start

Run all scripts in sequence:

```bash
# 1. Generate test data (if needed)
python3 generate_test_data.py

# 2. Perform clustering
python3 cluster_children_data.py

# 3. Create interactive visualization
python3 visualize_clusters_interactive.py

# 4. Open the map in your browser
open malawi_clusters_interactive.html  # macOS
# or
xdg-open malawi_clusters_interactive.html  # Linux
```

## Output Files

Generated files (excluded from git via .gitignore):
- `mwi_children_under_five_2020_test.csv` - Synthetic test data
- `clustered_children_1000.csv` - Cluster centers with population
- `clustered_children_1000_stats.txt` - Clustering statistics
- `malawi_clusters_interactive.html` - Interactive map

## Cluster Data Format

The `clustered_children_1000.csv` file contains:
- `cluster_id` - Unique identifier for each cluster (0-999)
- `latitude` - Latitude coordinate of cluster center
- `longitude` - Longitude coordinate of cluster center
- `population` - Number of data points in this cluster

Example:
```csv
cluster_id,latitude,longitude,population
0,-16.711945,34.977903,119
1,-12.848457,33.565787,94
2,-11.033359,34.229206,94
```

## Map Features

The interactive map includes:
- **Individual Markers View** - Shows all 1,000 clusters as circle markers
  - Size and color vary by population
  - Hover to see population count
  - Click for detailed information
- **Clustered View** - Groups nearby markers for better performance
- **Heatmap** - Shows population density
- **Boundaries** - Malawi Traditional Authorities administrative boundaries
- **Layer Control** - Toggle between different views
- **Legend** - Shows population density categories and statistics

## Technical Details

### Clustering Algorithm
- **Algorithm**: MiniBatchKMeans (from scikit-learn)
- **Sample Size**: 100,000 random points
- **Number of Clusters**: 1,000
- **Batch Size**: 5,000
- **Random Seed**: 42 (for reproducibility)
- **Max Iterations**: 100

### Color Coding
Clusters are color-coded by population density:
- Very Light (`#fee5d9`) - Below 50% of mean
- Light Orange (`#fcae91`) - 50-100% of mean
- Orange (`#fb6a4a`) - 100-150% of median
- Red (`#de2d26`) - 150-200% of mean
- Dark Red (`#a50f15`) - Above 200% of mean

## Notes

- The actual `mwi_children_under_five_2020.csv` file is stored in Git LFS
- If LFS data is unavailable, scripts automatically use test data
- Generated files can be recreated by running the scripts
- The interactive map works offline once generated

## Author

Created for the Wheels Clinics project to analyze population distribution in Malawi.
