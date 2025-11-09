#!/usr/bin/env python3
"""
Visualize clustered population data on the map of Malawi.
Overlays k-means cluster centers on Malawi Traditional Authorities boundaries.
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import numpy as np
import sys
import os


def load_clustered_data(cluster_file='clustered_population.csv'):
    """Load the clustered population data."""
    if not os.path.exists(cluster_file):
        print(f"Error: Cluster file not found: {cluster_file}")
        print("Please run cluster_population.py first to generate the clustered data.")
        sys.exit(1)

    print(f"Loading clustered data from: {cluster_file}")
    df = pd.read_csv(cluster_file)
    print(f"Loaded {len(df):,} cluster centers")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nTotal population represented: {df['population_count'].sum():,}")
    print(f"Average cluster size: {df['population_count'].mean():.2f}")
    print(f"Min cluster size: {df['population_count'].min()}")
    print(f"Max cluster size: {df['population_count'].max()}")

    return df


def load_malawi_boundaries(boundaries_file='malawi_ta_boundaries.geojson'):
    """Load Malawi Traditional Authorities boundaries."""
    if not os.path.exists(boundaries_file):
        print(f"Error: Boundaries file not found: {boundaries_file}")
        sys.exit(1)

    print(f"\nLoading Malawi boundaries from: {boundaries_file}")
    gdf = gpd.read_file(boundaries_file)
    print(f"Loaded {len(gdf)} Traditional Authorities")

    return gdf


def create_population_map(cluster_df, boundaries_gdf, output_file='malawi_population_clusters.png'):
    """
    Create a visualization of clustered population on Malawi map.

    Args:
        cluster_df: DataFrame with cluster centers and population counts
        boundaries_gdf: GeoDataFrame with Malawi boundaries
        output_file: Output filename for the visualization
    """
    print("\nCreating population cluster visualization...")

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(15, 20))

    # Plot the Traditional Authorities boundaries
    boundaries_gdf.boundary.plot(ax=ax, linewidth=0.5, edgecolor='black', alpha=0.7)
    boundaries_gdf.plot(ax=ax, alpha=0.15, color='lightgray')

    # Normalize population counts for color mapping
    pop_counts = cluster_df['population_count'].values
    norm = mcolors.LogNorm(vmin=max(1, pop_counts.min()), vmax=pop_counts.max())

    # Plot cluster centers with size and color based on population
    scatter = ax.scatter(
        cluster_df['longitude'],
        cluster_df['latitude'],
        c=cluster_df['population_count'],
        s=np.sqrt(cluster_df['population_count']) * 2,  # Size proportional to sqrt of population
        cmap='YlOrRd',
        norm=norm,
        alpha=0.6,
        edgecolors='black',
        linewidths=0.5,
        zorder=5
    )

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, pad=0.02, fraction=0.046)
    cbar.set_label('Population Count per Cluster', fontsize=12, fontweight='bold')

    # Add title and labels
    ax.set_title('Malawi Population Distribution\n(K-means Clustered)',
                 fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)

    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    # Add statistics text box
    total_pop = cluster_df['population_count'].sum()
    num_clusters = len(cluster_df)
    textstr = (f'Total Population: {total_pop:,}\n'
               f'Clusters: {num_clusters:,}\n'
               f'Avg Cluster Size: {cluster_df["population_count"].mean():.0f}\n'
               f'Max Cluster Size: {cluster_df["population_count"].max():,}')

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.9)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props, family='monospace')

    # Adjust layout
    plt.tight_layout()

    # Save the figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Map saved as: {output_file}")


def create_density_map(cluster_df, boundaries_gdf, output_file='malawi_population_density.png'):
    """
    Create a density-focused visualization showing population concentration.

    Args:
        cluster_df: DataFrame with cluster centers and population counts
        boundaries_gdf: GeoDataFrame with Malawi boundaries
        output_file: Output filename for the visualization
    """
    print("\nCreating population density visualization...")

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(15, 20))

    # Plot the Traditional Authorities boundaries
    boundaries_gdf.boundary.plot(ax=ax, linewidth=0.5, edgecolor='black', alpha=0.7)
    boundaries_gdf.plot(ax=ax, alpha=0.1, color='lightgray')

    # Create density categories
    pop_counts = cluster_df['population_count'].values
    percentiles = [0, 25, 50, 75, 90, 100]
    thresholds = np.percentile(pop_counts, percentiles)

    # Define colors for different density levels
    colors = ['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15']
    labels = ['Low', 'Medium-Low', 'Medium', 'Medium-High', 'High']

    # Plot each density category
    for i in range(len(colors)):
        if i == len(colors) - 1:
            mask = (pop_counts >= thresholds[i]) & (pop_counts <= thresholds[i+1])
        else:
            mask = (pop_counts >= thresholds[i]) & (pop_counts < thresholds[i+1])

        if mask.any():
            ax.scatter(
                cluster_df.loc[mask, 'longitude'],
                cluster_df.loc[mask, 'latitude'],
                c=colors[i],
                s=50,
                alpha=0.7,
                edgecolors='black',
                linewidths=0.3,
                label=f'{labels[i]} ({thresholds[i]:.0f}-{thresholds[i+1]:.0f})',
                zorder=5
            )

    # Add title and labels
    ax.set_title('Malawi Population Density Distribution\n(K-means Clustered)',
                 fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)

    # Add legend
    ax.legend(loc='lower right', title='Population Density', fontsize=10,
              framealpha=0.9, edgecolor='black')

    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    # Add statistics text box
    total_pop = cluster_df['population_count'].sum()
    num_clusters = len(cluster_df)
    textstr = (f'Total Population: {total_pop:,}\n'
               f'Clusters: {num_clusters:,}\n'
               f'Density Categories: {len(colors)}')

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.9)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props, family='monospace')

    # Adjust layout
    plt.tight_layout()

    # Save the figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Density map saved as: {output_file}")


def create_simple_overlay(cluster_df, boundaries_gdf, output_file='malawi_population_simple.png'):
    """
    Create a simple visualization with uniform point sizes for clarity.

    Args:
        cluster_df: DataFrame with cluster centers and population counts
        boundaries_gdf: GeoDataFrame with Malawi boundaries
        output_file: Output filename for the visualization
    """
    print("\nCreating simple population overlay...")

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(15, 20))

    # Plot the Traditional Authorities boundaries
    boundaries_gdf.boundary.plot(ax=ax, linewidth=0.8, edgecolor='black', alpha=0.8)
    boundaries_gdf.plot(ax=ax, alpha=0.2, cmap='Pastel1', legend=False)

    # Plot all cluster centers with uniform size
    ax.scatter(
        cluster_df['longitude'],
        cluster_df['latitude'],
        c='red',
        s=20,
        alpha=0.5,
        edgecolors='darkred',
        linewidths=0.3,
        label=f'{len(cluster_df):,} Cluster Centers',
        zorder=5
    )

    # Add title and labels
    ax.set_title('Malawi Population Cluster Centers',
                 fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)

    # Add legend
    ax.legend(loc='lower right', fontsize=12, framealpha=0.9, edgecolor='black')

    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    # Add statistics text box
    total_pop = cluster_df['population_count'].sum()
    num_clusters = len(cluster_df)
    textstr = (f'Total Population: {total_pop:,}\n'
               f'Cluster Centers: {num_clusters:,}\n'
               f'Reduction: ~100:1')

    props = dict(boxstyle='round', facecolor='lightblue', alpha=0.9)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props, family='monospace')

    # Adjust layout
    plt.tight_layout()

    # Save the figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Simple overlay saved as: {output_file}")


def main():
    """Main function to create all visualizations."""
    print("=" * 70)
    print("Malawi Population Cluster Visualization")
    print("=" * 70)

    # Load data
    print("\n1. Loading data...")
    cluster_df = load_clustered_data('clustered_population.csv')
    boundaries_gdf = load_malawi_boundaries('malawi_ta_boundaries.geojson')

    # Create visualizations
    print("\n2. Creating visualizations...")

    # Map 1: Population-weighted clusters
    create_population_map(cluster_df, boundaries_gdf, 'malawi_population_clusters.png')

    # Map 2: Density categories
    create_density_map(cluster_df, boundaries_gdf, 'malawi_population_density.png')

    # Map 3: Simple overlay
    create_simple_overlay(cluster_df, boundaries_gdf, 'malawi_population_simple.png')

    # Summary
    print("\n" + "=" * 70)
    print("Visualization complete!")
    print("=" * 70)
    print("\nGenerated maps:")
    print("  1. malawi_population_clusters.png - Population-weighted visualization")
    print("  2. malawi_population_density.png - Density categories")
    print("  3. malawi_population_simple.png - Simple cluster overlay")
    print("\nAll maps show cluster centers overlaid on Malawi Traditional Authorities.")


if __name__ == '__main__':
    main()
