#!/usr/bin/env python3
"""
K-means clustering script for Malawi children under five population data.
Samples 100,000 random points and clusters them into 1000 cluster centers.
Each cluster contains coordinates and the number of data points it represents.
"""

import pandas as pd
import numpy as np
from sklearn.cluster import MiniBatchKMeans
import sys
import os


def load_children_data(file_path='mwi_children_under_five_2020.csv'):
    """Load the children under five population CSV file."""
    # Try test data file if main file doesn't exist or is LFS pointer
    test_file = 'mwi_children_under_five_2020_test.csv'

    if not os.path.exists(file_path):
        print(f"Warning: Data file not found: {file_path}")
        if os.path.exists(test_file):
            print(f"Using test data file instead: {test_file}")
            file_path = test_file
        else:
            print("Please ensure the Git LFS file has been pulled or generate test data.")
            sys.exit(1)

    # Check if it's a Git LFS pointer file
    with open(file_path, 'r') as f:
        first_line = f.readline().strip()
        if first_line.startswith('version https://git-lfs'):
            print(f"Warning: {file_path} is a Git LFS pointer file.")
            if os.path.exists(test_file) and file_path != test_file:
                print(f"Using test data file instead: {test_file}")
                file_path = test_file
            else:
                print("Please run 'git lfs pull' to download the actual data.")
                sys.exit(1)

    print(f"Loading data from: {file_path}")
    df = pd.read_csv(file_path)
    print(f"Loaded {len(df):,} total records")
    print(f"Columns: {df.columns.tolist()}")

    return df


def extract_coordinates(df):
    """
    Extract latitude and longitude coordinates from the dataframe.
    Handles various common column naming conventions.
    """
    # Try to find coordinate columns
    lat_cols = [col for col in df.columns if col.lower() in ['lat', 'latitude', 'y']]
    lon_cols = [col for col in df.columns if col.lower() in ['lon', 'long', 'longitude', 'x']]

    if not lat_cols or not lon_cols:
        print("\nAvailable columns:")
        print(df.columns.tolist())
        print("\nAssuming first two columns are longitude and latitude...")
        # If no clear column names, assume first two columns are coordinates
        coords = df.iloc[:, :2].values
        coord_names = df.columns[:2].tolist()
    else:
        lat_col = lat_cols[0]
        lon_col = lon_cols[0]
        print(f"Using coordinate columns: {lon_col}, {lat_col}")
        coords = df[[lon_col, lat_col]].values
        coord_names = [lon_col, lat_col]

    # Remove any rows with NaN values
    initial_count = len(coords)
    coords = coords[~np.isnan(coords).any(axis=1)]
    if len(coords) < initial_count:
        print(f"Removed {initial_count - len(coords):,} rows with NaN values")

    print(f"Valid coordinates: {len(coords):,}")

    return coords, coord_names


def sample_random_points(coordinates, sample_size=100000, random_seed=42):
    """
    Sample random points from the dataset.

    Args:
        coordinates: Array of coordinate pairs
        sample_size: Number of points to sample (default: 100,000)
        random_seed: Random seed for reproducibility

    Returns:
        sampled_coords: Randomly sampled coordinates
    """
    np.random.seed(random_seed)

    n_points = len(coordinates)

    if n_points <= sample_size:
        print(f"\nDataset has {n_points:,} points, which is less than or equal to requested sample size {sample_size:,}")
        print("Using all available points.")
        return coordinates

    print(f"\nSampling {sample_size:,} random points from {n_points:,} total points...")

    # Random sampling without replacement
    sample_indices = np.random.choice(n_points, size=sample_size, replace=False)
    sampled_coords = coordinates[sample_indices]

    print(f"Sampled {len(sampled_coords):,} points")

    return sampled_coords


def cluster_coordinates(coordinates, n_clusters=1000, random_seed=42):
    """
    Cluster coordinates using k-means.

    Args:
        coordinates: Array of [longitude, latitude] pairs
        n_clusters: Number of clusters to create (default: 1000)
        random_seed: Random seed for reproducibility

    Returns:
        cluster_centers: Array of cluster center coordinates
        labels: Cluster labels for each point
        cluster_sizes: Number of points in each cluster
    """
    n_points = len(coordinates)

    print(f"\nClustering {n_points:,} points into {n_clusters:,} clusters")
    print(f"Average cluster size: ~{n_points / n_clusters:.1f} points")

    # Use MiniBatchKMeans for better performance with large datasets
    print("\nRunning k-means clustering...")
    kmeans = MiniBatchKMeans(
        n_clusters=n_clusters,
        batch_size=5000,
        random_state=random_seed,
        verbose=1,
        max_iter=100,
        n_init=3
    )

    labels = kmeans.fit_predict(coordinates)
    cluster_centers = kmeans.cluster_centers_

    print(f"\nClustering complete!")
    print(f"Created {len(cluster_centers):,} cluster centers")

    # Calculate cluster sizes
    unique_labels, counts = np.unique(labels, return_counts=True)
    cluster_sizes = dict(zip(unique_labels, counts))

    return cluster_centers, labels, cluster_sizes


def save_clustered_data(cluster_centers, cluster_sizes, output_file='clustered_children_1000.csv'):
    """
    Save clustered data to CSV file.

    Args:
        cluster_centers: Array of cluster center coordinates
        cluster_sizes: Dictionary mapping cluster IDs to population counts
        output_file: Output filename
    """
    # Create DataFrame with cluster information
    clusters_df = pd.DataFrame(
        cluster_centers,
        columns=['longitude', 'latitude']
    )
    clusters_df['cluster_id'] = range(len(cluster_centers))
    clusters_df['population'] = clusters_df['cluster_id'].map(cluster_sizes).fillna(0).astype(int)

    # Reorder columns for clarity
    clusters_df = clusters_df[['cluster_id', 'latitude', 'longitude', 'population']]

    # Save to CSV
    clusters_df.to_csv(output_file, index=False)

    print(f"\n{'='*70}")
    print(f"Cluster data saved to: {output_file}")
    print(f"{'='*70}")
    print(f"\nDataFrame shape: {clusters_df.shape}")
    print(f"Columns: {clusters_df.columns.tolist()}")
    print(f"\nFirst 10 clusters:")
    print(clusters_df.head(10).to_string(index=False))

    # Print statistics
    print(f"\n{'='*70}")
    print("Cluster Statistics:")
    print(f"{'='*70}")
    print(f"Total clusters: {len(clusters_df):,}")
    print(f"Total population: {clusters_df['population'].sum():,}")
    print(f"\nPopulation distribution:")
    print(f"  Minimum: {clusters_df['population'].min():,}")
    print(f"  Maximum: {clusters_df['population'].max():,}")
    print(f"  Mean: {clusters_df['population'].mean():.2f}")
    print(f"  Median: {clusters_df['population'].median():.0f}")
    print(f"  Std Dev: {clusters_df['population'].std():.2f}")

    # Save statistics to text file
    stats_file = output_file.replace('.csv', '_stats.txt')
    with open(stats_file, 'w') as f:
        f.write("K-means Clustering Statistics\n")
        f.write("="*70 + "\n")
        f.write(f"Data source: mwi_children_under_five_2020.csv\n")
        f.write(f"Sample size: 100,000 random points\n")
        f.write(f"Number of clusters: {len(clusters_df):,}\n")
        f.write(f"Total population: {clusters_df['population'].sum():,}\n\n")
        f.write("Population statistics:\n")
        f.write(f"  Minimum: {clusters_df['population'].min():,}\n")
        f.write(f"  Maximum: {clusters_df['population'].max():,}\n")
        f.write(f"  Mean: {clusters_df['population'].mean():.2f}\n")
        f.write(f"  Median: {clusters_df['population'].median():.0f}\n")
        f.write(f"  Std Dev: {clusters_df['population'].std():.2f}\n")

    print(f"\nStatistics saved to: {stats_file}")

    return clusters_df


def main():
    """Main function to run the clustering pipeline."""
    print("="*70)
    print("Malawi Children Under Five - K-means Clustering")
    print("Sample: 100,000 random points → 1,000 clusters")
    print("="*70)

    # Configuration
    DATA_FILE = 'mwi_children_under_five_2020.csv'
    SAMPLE_SIZE = 100000
    N_CLUSTERS = 1000
    OUTPUT_FILE = 'clustered_children_1000.csv'
    RANDOM_SEED = 42

    # Step 1: Load data
    print("\n1. Loading population data...")
    df = load_children_data(DATA_FILE)

    # Step 2: Extract coordinates
    print("\n2. Extracting coordinates...")
    coordinates, coord_names = extract_coordinates(df)

    # Step 3: Sample random points
    print("\n3. Sampling random points...")
    sampled_coords = sample_random_points(coordinates, sample_size=SAMPLE_SIZE, random_seed=RANDOM_SEED)

    # Step 4: Perform clustering
    print("\n4. Performing k-means clustering...")
    cluster_centers, labels, cluster_sizes = cluster_coordinates(
        sampled_coords,
        n_clusters=N_CLUSTERS,
        random_seed=RANDOM_SEED
    )

    # Step 5: Save results
    print("\n5. Saving results...")
    clusters_df = save_clustered_data(cluster_centers, cluster_sizes, OUTPUT_FILE)

    print("\n" + "="*70)
    print("Clustering complete!")
    print("="*70)
    print(f"\nOutput files:")
    print(f"  - {OUTPUT_FILE}")
    print(f"  - {OUTPUT_FILE.replace('.csv', '_stats.txt')}")
    print(f"\nNext step: Run visualize_clusters_interactive.py to create an interactive map")


if __name__ == '__main__':
    main()
