#!/usr/bin/env python3
"""
Analyze distances between cluster points to understand coverage overlap.
Helps determine optimal buffer radius for better coverage overlap.
"""

import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
import geopandas as gpd
from shapely.geometry import Point


def load_cluster_data(file_path='clustered_children_1000.csv'):
    """Load clustered data."""
    df = pd.read_csv(file_path)
    return df


def calculate_distances(df):
    """
    Calculate pairwise distances between all cluster points.
    Uses haversine distance for accuracy.
    """
    print("Calculating distances between all cluster points...")

    # Create GeoDataFrame
    geometry = [Point(lon, lat) for lon, lat in zip(df['longitude'], df['latitude'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

    # Project to UTM for distance calculations in meters
    gdf_projected = gdf.to_crs('EPSG:32736')

    # Get coordinates as array
    coords = np.array([[geom.x, geom.y] for geom in gdf_projected.geometry])

    # Calculate pairwise distances (in meters)
    print("  Computing pairwise distance matrix...")
    distance_matrix = cdist(coords, coords, metric='euclidean')

    # Convert to kilometers
    distance_matrix_km = distance_matrix / 1000

    # Set diagonal to infinity (ignore self-distances)
    np.fill_diagonal(distance_matrix_km, np.inf)

    return distance_matrix_km


def analyze_distances(distance_matrix_km, df):
    """Analyze distance statistics."""
    print("\n" + "="*70)
    print("DISTANCE ANALYSIS")
    print("="*70)

    # Nearest neighbor distances
    min_distances = np.min(distance_matrix_km, axis=1)

    print("\nNearest Neighbor Distances:")
    print(f"  Minimum: {np.min(min_distances):.2f} km")
    print(f"  Maximum: {np.max(min_distances):.2f} km")
    print(f"  Mean: {np.mean(min_distances):.2f} km")
    print(f"  Median: {np.median(min_distances):.2f} km")
    print(f"  Std Dev: {np.std(min_distances):.2f} km")

    # Distance percentiles
    print("\nNearest Neighbor Distance Percentiles:")
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    for p in percentiles:
        value = np.percentile(min_distances, p)
        print(f"  {p}th percentile: {value:.2f} km")

    # Count points within various radii
    print("\nCoverage Analysis for Different Buffer Radii:")
    radii = [5, 10, 15, 20, 25, 30]

    for radius in radii:
        # Count how many points are within radius for each point
        within_radius = (distance_matrix_km <= radius).sum(axis=1)

        avg_coverage = np.mean(within_radius)
        min_coverage = np.min(within_radius)
        max_coverage = np.max(within_radius)

        # Total coverage relationships
        total_relationships = (distance_matrix_km <= radius).sum()

        print(f"\n  {radius}km radius:")
        print(f"    Avg points covered per site: {avg_coverage:.2f}")
        print(f"    Min points covered: {min_coverage}")
        print(f"    Max points covered: {max_coverage}")
        print(f"    Total coverage relationships: {total_relationships:,}")
        print(f"    Avg candidates per demand point: {total_relationships / len(df):.2f}")

        # Estimate population coverage
        total_pop = df['population'].sum()
        # Approximate coverage if we select top sites
        print(f"    Estimated coverage overlap: {(total_relationships / len(df)):.1f}x")

    # Find optimal radius for target coverage
    print("\n" + "="*70)
    print("RECOMMENDED BUFFER RADIUS")
    print("="*70)

    print("\nFor meaningful optimization, each demand point should have multiple")
    print("candidate sites to choose from (coverage overlap).")

    target_coverage = 5  # Target: each point covered by ~5 candidates
    recommended_radius = None

    for radius in range(1, 51):
        within_radius = (distance_matrix_km <= radius).sum(axis=1)
        avg_coverage = np.mean(within_radius)

        if avg_coverage >= target_coverage:
            recommended_radius = radius
            print(f"\nRecommended radius: {recommended_radius} km")
            print(f"  - Average candidates per demand point: {avg_coverage:.2f}")
            print(f"  - Average points each site can cover: {avg_coverage:.2f}")

            total_relationships = (distance_matrix_km <= recommended_radius).sum()
            print(f"  - Total coverage relationships: {total_relationships:,}")

            # Calculate potential coverage with 30 sites
            uncovered_analysis(distance_matrix_km, df, recommended_radius)
            break

    if recommended_radius is None:
        print("\nWarning: Points are very spread out.")
        print("Consider using the maximum available radius or clustering fewer points.")


def uncovered_analysis(distance_matrix_km, df, radius):
    """
    Analyze what happens if we place facilities at top locations.
    """
    print(f"\n  Greedy Coverage Analysis (placing 30 sites):")

    # Greedy algorithm: iteratively select site that covers most uncovered population
    uncovered_demand = set(range(len(df)))
    selected_sites = []
    coverage_dict = {i: set(np.where(distance_matrix_km[i] <= radius)[0])
                     for i in range(len(df))}

    total_pop = df['population'].sum()
    pop_array = df['population'].values

    for iteration in range(30):
        if not uncovered_demand:
            break

        # Find site that covers most uncovered population
        best_site = None
        best_pop = 0

        for site in range(len(df)):
            if site in selected_sites:
                continue

            # Calculate population that would be newly covered
            newly_covered = coverage_dict[site] & uncovered_demand
            newly_covered_pop = sum(pop_array[i] for i in newly_covered)

            if newly_covered_pop > best_pop:
                best_pop = newly_covered_pop
                best_site = site

        if best_site is None:
            break

        selected_sites.append(best_site)
        newly_covered = coverage_dict[best_site] & uncovered_demand
        uncovered_demand -= newly_covered

    # Calculate final coverage
    all_covered = set()
    for site in selected_sites:
        all_covered |= coverage_dict[site]

    covered_pop = sum(pop_array[i] for i in all_covered)
    coverage_pct = (covered_pop / total_pop) * 100

    print(f"    Sites selected: {len(selected_sites)}")
    print(f"    Demand points covered: {len(all_covered):,} / {len(df):,}")
    print(f"    Population covered: {covered_pop:,} / {total_pop:,}")
    print(f"    Coverage percentage: {coverage_pct:.2f}%")
    print(f"    Uncovered demand points: {len(uncovered_demand)}")


def save_distance_statistics(min_distances, df):
    """Save distance statistics to file."""
    stats_df = pd.DataFrame({
        'cluster_id': df['cluster_id'],
        'nearest_neighbor_distance_km': min_distances
    }).sort_values('nearest_neighbor_distance_km')

    output_file = 'nearest_neighbor_distances.csv'
    stats_df.to_csv(output_file, index=False)
    print(f"\nNearest neighbor distances saved to: {output_file}")


def main():
    print("="*70)
    print("Coverage Distance Analysis")
    print("="*70)

    # Load data
    df = load_cluster_data()
    print(f"\nLoaded {len(df):,} cluster points")

    # Calculate distances
    distance_matrix_km = calculate_distances(df)

    # Analyze
    analyze_distances(distance_matrix_km, df)

    # Save statistics
    min_distances = np.min(distance_matrix_km, axis=1)
    save_distance_statistics(min_distances, df)

    print("\n" + "="*70)
    print("Analysis complete!")
    print("="*70)


if __name__ == '__main__':
    main()
