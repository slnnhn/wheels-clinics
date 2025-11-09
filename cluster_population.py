#!/usr/bin/env python3
"""
K-means clustering script for Malawi population data.
Clusters population coordinates, reducing 100 points into 1 cluster center.
"""

import pandas as pd
import numpy as np
from sklearn.cluster import MiniBatchKMeans
import glob
import os
import sys


def load_population_data(file_pattern='mwi_*.csv'):
    """Load all population CSV files matching the pattern."""
    files = glob.glob(file_pattern)

    if not files:
        print(f"No files found matching pattern: {file_pattern}")
        sys.exit(1)

    print(f"Found {len(files)} population files:")
    for f in files:
        print(f"  - {f}")

    # Read all files and combine them
    all_data = []
    for file in files:
        try:
            df = pd.read_csv(file)
            all_data.append(df)
            print(f"Loaded {len(df):,} records from {file}")
        except Exception as e:
            print(f"Error loading {file}: {e}")
            continue

    if not all_data:
        print("No data loaded successfully")
        sys.exit(1)

    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"\nTotal records loaded: {len(combined_df):,}")

    return combined_df


def extract_coordinates(df):
    """
    Extract latitude and longitude coordinates from the dataframe.
    Assumes columns are named with common variations: lat/latitude/y and lon/longitude/x
    """
    # Try to find coordinate columns
    lat_cols = [col for col in df.columns if col.lower() in ['lat', 'latitude', 'y']]
    lon_cols = [col for col in df.columns if col.lower() in ['lon', 'long', 'longitude', 'x']]

    if not lat_cols or not lon_cols:
        print("\nColumn names in the dataset:")
        print(df.columns.tolist())
        print("\nAssuming first two columns are longitude and latitude...")
        # If no clear column names, assume first two columns are coordinates
        coords = df.iloc[:, :2].values
    else:
        lat_col = lat_cols[0]
        lon_col = lon_cols[0]
        print(f"Using columns: {lon_col}, {lat_col}")
        coords = df[[lon_col, lat_col]].values

    # Remove any rows with NaN values
    coords = coords[~np.isnan(coords).any(axis=1)]
    print(f"Valid coordinates after removing NaN: {len(coords):,}")

    return coords


def cluster_coordinates(coordinates, reduction_factor=100):
    """
    Cluster coordinates using k-means.

    Args:
        coordinates: Array of [longitude, latitude] pairs
        reduction_factor: How many points to reduce into one cluster (default: 100)

    Returns:
        cluster_centers: Array of cluster center coordinates
        labels: Cluster labels for each original point
        n_clusters: Number of clusters created
    """
    n_points = len(coordinates)
    n_clusters = max(1, n_points // reduction_factor)

    print(f"\nClustering {n_points:,} points into {n_clusters:,} clusters")
    print(f"Reduction factor: {reduction_factor}:1")
    print(f"Average cluster size: ~{reduction_factor} points")

    # Use MiniBatchKMeans for better performance with large datasets
    print("\nRunning k-means clustering (this may take a few minutes)...")
    kmeans = MiniBatchKMeans(
        n_clusters=n_clusters,
        batch_size=10000,
        random_state=42,
        verbose=1,
        max_iter=100
    )

    labels = kmeans.fit_predict(coordinates)
    cluster_centers = kmeans.cluster_centers_

    print(f"\nClustering complete!")
    print(f"Created {len(cluster_centers):,} cluster centers")

    return cluster_centers, labels, n_clusters


def save_clustered_data(cluster_centers, labels, original_coords, output_file='clustered_population.csv'):
    """
    Save clustered data to CSV files.

    Args:
        cluster_centers: Array of cluster center coordinates
        labels: Cluster labels for each original point
        original_coords: Original coordinate array
        output_file: Output filename for cluster centers
    """
    # Save cluster centers
    centers_df = pd.DataFrame(
        cluster_centers,
        columns=['longitude', 'latitude']
    )
    centers_df['cluster_id'] = range(len(cluster_centers))

    # Calculate cluster sizes
    unique_labels, counts = np.unique(labels, return_counts=True)
    cluster_sizes = dict(zip(unique_labels, counts))
    centers_df['population_count'] = centers_df['cluster_id'].map(cluster_sizes)

    centers_df.to_csv(output_file, index=False)
    print(f"\nCluster centers saved to: {output_file}")
    print(f"Columns: {centers_df.columns.tolist()}")
    print(f"\nFirst few cluster centers:")
    print(centers_df.head(10))

    # Save statistics
    stats_file = output_file.replace('.csv', '_stats.txt')
    with open(stats_file, 'w') as f:
        f.write("K-means Clustering Statistics\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Original points: {len(original_coords):,}\n")
        f.write(f"Cluster centers: {len(cluster_centers):,}\n")
        f.write(f"Reduction ratio: {len(original_coords) / len(cluster_centers):.2f}:1\n\n")
        f.write(f"Cluster size statistics:\n")
        f.write(f"  Minimum: {centers_df['population_count'].min()}\n")
        f.write(f"  Maximum: {centers_df['population_count'].max()}\n")
        f.write(f"  Mean: {centers_df['population_count'].mean():.2f}\n")
        f.write(f"  Median: {centers_df['population_count'].median():.2f}\n")

    print(f"Statistics saved to: {stats_file}")


def main():
    """Main function to run the clustering pipeline."""
    print("=" * 70)
    print("Malawi Population K-means Clustering")
    print("=" * 70)

    # Load population data
    print("\n1. Loading population data...")
    df = load_population_data('mwi_*.csv')

    # Extract coordinates
    print("\n2. Extracting coordinates...")
    coordinates = extract_coordinates(df)

    # Perform clustering (100:1 reduction)
    print("\n3. Performing k-means clustering...")
    cluster_centers, labels, n_clusters = cluster_coordinates(coordinates, reduction_factor=100)

    # Save results
    print("\n4. Saving results...")
    save_clustered_data(cluster_centers, labels, coordinates, 'clustered_population.csv')

    print("\n" + "=" * 70)
    print("Clustering complete!")
    print("=" * 70)
    print("\nOutput files:")
    print("  - clustered_population.csv (cluster centers with population counts)")
    print("  - clustered_population_stats.txt (clustering statistics)")


if __name__ == '__main__':
    main()
