#!/usr/bin/env python3
"""
Generate synthetic test data for Malawi children population.
Creates realistic-looking population data points within Malawi's geographic boundaries.
This is for testing/demonstration purposes when the actual LFS data is not available.
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import sys
import os
from shapely.geometry import Point


def generate_synthetic_data(n_points=100000, output_file='mwi_children_under_five_2020_test.csv'):
    """
    Generate synthetic population data for Malawi.

    Args:
        n_points: Number of data points to generate
        output_file: Output CSV filename
    """
    print(f"Generating {n_points:,} synthetic data points for Malawi...")

    # Malawi approximate boundaries
    # Latitude: -17.1 to -9.4
    # Longitude: 32.7 to 35.9
    lat_min, lat_max = -17.1, -9.4
    lon_min, lon_max = 32.7, 35.9

    # Check if boundaries file exists to create more realistic data
    boundaries_file = 'malawi_ta_boundaries.geojson'
    if os.path.exists(boundaries_file):
        print(f"Loading boundaries from {boundaries_file} for realistic placement...")
        gdf = gpd.read_file(boundaries_file)

        # Generate points within actual boundaries
        points = []
        attempts = 0
        max_attempts = n_points * 10  # Limit attempts to avoid infinite loop

        print("Generating points within Malawi boundaries (this may take a moment)...")

        # Get the union of all geometries
        malawi_boundary = gdf.unary_union

        while len(points) < n_points and attempts < max_attempts:
            attempts += 1

            # Generate random point
            lat = np.random.uniform(lat_min, lat_max)
            lon = np.random.uniform(lon_min, lon_max)
            point = Point(lon, lat)

            # Check if point is within Malawi
            if malawi_boundary.contains(point):
                points.append([lon, lat])

            # Progress indicator
            if len(points) % 10000 == 0 and len(points) > 0:
                print(f"  Generated {len(points):,} / {n_points:,} points...")

        if len(points) < n_points:
            print(f"Warning: Only generated {len(points):,} points within boundaries")
            print(f"Filling remaining {n_points - len(points):,} with random points...")

            # Fill remaining with simple random points
            remaining = n_points - len(points)
            for _ in range(remaining):
                lat = np.random.uniform(lat_min, lat_max)
                lon = np.random.uniform(lon_min, lon_max)
                points.append([lon, lat])

        coordinates = np.array(points)

    else:
        print("Boundaries file not found. Generating uniform random distribution...")

        # Create population centers (cities/towns) for more realistic distribution
        n_centers = 20
        centers = []

        for i in range(n_centers):
            center_lat = np.random.uniform(lat_min, lat_max)
            center_lon = np.random.uniform(lon_min, lon_max)
            center_weight = np.random.uniform(0.3, 1.0)  # Popularity weight
            centers.append([center_lon, center_lat, center_weight])

        centers = np.array(centers)
        print(f"Created {n_centers} population centers")

        # Generate points clustered around centers
        coordinates = []

        for _ in range(n_points):
            # Select a random center (weighted by popularity)
            weights = centers[:, 2] / centers[:, 2].sum()
            center_idx = np.random.choice(len(centers), p=weights)
            center = centers[center_idx]

            # Add random offset with normal distribution
            lat_offset = np.random.normal(0, 0.15)  # ~16km standard deviation
            lon_offset = np.random.normal(0, 0.15)

            lat = np.clip(center[1] + lat_offset, lat_min, lat_max)
            lon = np.clip(center[0] + lon_offset, lon_min, lon_max)

            coordinates.append([lon, lat])

        coordinates = np.array(coordinates)

    # Create DataFrame
    df = pd.DataFrame(coordinates, columns=['longitude', 'latitude'])

    # Add some additional realistic columns
    df['x'] = df['longitude']
    df['y'] = df['latitude']

    # Save to CSV
    df.to_csv(output_file, index=False)

    print(f"\n{'='*70}")
    print(f"Synthetic data saved to: {output_file}")
    print(f"{'='*70}")
    print(f"\nDataFrame info:")
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {df.columns.tolist()}")
    print(f"\nCoordinate ranges:")
    print(f"  Latitude: {df['latitude'].min():.4f} to {df['latitude'].max():.4f}")
    print(f"  Longitude: {df['longitude'].min():.4f} to {df['longitude'].max():.4f}")
    print(f"\nFirst few rows:")
    print(df.head(10))

    print(f"\nNote: This is synthetic test data for demonstration purposes.")
    print(f"For production use, please use the actual mwi_children_under_five_2020.csv from Git LFS.")

    return df


def main():
    """Main function to generate synthetic test data."""
    print("="*70)
    print("Generate Synthetic Test Data for Malawi Children Population")
    print("="*70)

    # Configuration
    N_POINTS = 100000
    OUTPUT_FILE = 'mwi_children_under_five_2020_test.csv'

    # Generate data
    df = generate_synthetic_data(N_POINTS, OUTPUT_FILE)

    print("\n" + "="*70)
    print("Test data generation complete!")
    print("="*70)
    print(f"\nYou can now run:")
    print(f"  1. python cluster_children_data.py (update to use {OUTPUT_FILE})")
    print(f"  2. python visualize_clusters_interactive.py")


if __name__ == '__main__':
    main()
