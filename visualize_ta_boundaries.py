#!/usr/bin/env python3
"""
Visualize Traditional Authorities (TAs) boundaries of Malawi
"""

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

# Read the GeoJSON file
print("Loading Malawi Traditional Authorities boundaries...")
gdf = gpd.read_file('malawi_ta_boundaries.geojson')

# Display basic information
print(f"\nTotal number of Traditional Authorities: {len(gdf)}")
print(f"\nFirst few TAs:")
print(gdf[['shapeName', 'shapeType']].head(10))

# Get all unique TA names
print(f"\nAll Traditional Authorities ({len(gdf)}):")
for idx, name in enumerate(sorted(gdf['shapeName'].unique()), 1):
    print(f"{idx:3d}. {name}")

# Create the visualization
fig, ax = plt.subplots(1, 1, figsize=(15, 20))

# Plot the boundaries
gdf.boundary.plot(ax=ax, linewidth=0.8, edgecolor='black')
gdf.plot(ax=ax, alpha=0.5, cmap='tab20', legend=False)

# Add title and labels
ax.set_title('Traditional Authorities (TAs) of Malawi',
             fontsize=20, fontweight='bold', pad=20)
ax.set_xlabel('Longitude', fontsize=12)
ax.set_ylabel('Latitude', fontsize=12)

# Add grid
ax.grid(True, alpha=0.3, linestyle='--')

# Add a text box with statistics
textstr = f'Total TAs: {len(gdf)}\nData Source: geoBoundaries'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=props)

# Adjust layout
plt.tight_layout()

# Save the figure
output_file = 'malawi_ta_boundaries_map.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\nMap saved as: {output_file}")

# Create a second visualization with labels for some major TAs
fig2, ax2 = plt.subplots(1, 1, figsize=(15, 20))

# Plot the boundaries
gdf.boundary.plot(ax=ax2, linewidth=0.8, edgecolor='black')
gdf.plot(ax=ax2, alpha=0.5, cmap='tab20', legend=False)

# Add labels for TAs (sample every few to avoid overcrowding)
for idx, row in gdf.iterrows():
    if idx % 8 == 0:  # Label every 8th TA to avoid overcrowding
        centroid = row.geometry.centroid
        ax2.annotate(text=row['shapeName'],
                    xy=(centroid.x, centroid.y),
                    fontsize=6,
                    ha='center',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.6))

ax2.set_title('Traditional Authorities (TAs) of Malawi with Labels',
             fontsize=20, fontweight='bold', pad=20)
ax2.set_xlabel('Longitude', fontsize=12)
ax2.set_ylabel('Latitude', fontsize=12)
ax2.grid(True, alpha=0.3, linestyle='--')

# Add statistics text box
ax2.text(0.02, 0.98, textstr, transform=ax2.transAxes, fontsize=12,
        verticalalignment='top', bbox=props)

plt.tight_layout()

# Save the labeled figure
output_file_labeled = 'malawi_ta_boundaries_labeled.png'
plt.savefig(output_file_labeled, dpi=300, bbox_inches='tight')
print(f"Labeled map saved as: {output_file_labeled}")

# Display summary statistics
print("\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)
print(f"Total Traditional Authorities: {len(gdf)}")
print(f"Coordinate Reference System: {gdf.crs}")
print(f"Bounds (lon, lat): {gdf.total_bounds}")
print("\nDataset columns:")
print(gdf.columns.tolist())
print("\nSample data:")
print(gdf.head())

print("\n✓ Visualization complete! Check the generated PNG files.")
