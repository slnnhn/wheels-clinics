#!/usr/bin/env python3
"""
Create coverage matrix for mobile clinic optimization.

For each candidate site (potential mobile unit location):
- Create a 5km buffer around it
- Determine which demand points fall within this buffer
- Build a coverage matrix showing which sites can serve which demand points

Output: Coverage matrix for optimization problem with 30 mobile units.
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import numpy as np
import json
import sys
import os


def load_cluster_data(file_path='clustered_children_1000.csv'):
    """
    Load the clustered population data.
    These points serve as both demand points and candidate sites.
    """
    if not os.path.exists(file_path):
        print(f"Error: Cluster file not found: {file_path}")
        print("Please run cluster_children_data.py first to generate the clustered data.")
        sys.exit(1)

    print(f"Loading clustered data from: {file_path}")
    df = pd.read_csv(file_path)
    print(f"Loaded {len(df):,} clusters")
    print(f"Columns: {df.columns.tolist()}")

    # Verify required columns
    required_cols = ['cluster_id', 'latitude', 'longitude', 'population']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}")
        sys.exit(1)

    print(f"\nTotal demand points: {len(df):,}")
    print(f"Total population: {df['population'].sum():,} children")
    print(f"Total candidate sites: {len(df):,}")

    return df


def create_geodataframe(df):
    """
    Convert DataFrame to GeoDataFrame with Point geometries.
    Use appropriate CRS for distance calculations.
    """
    print("\nCreating GeoDataFrame...")

    # Create Point geometries from coordinates
    geometry = [Point(lon, lat) for lon, lat in zip(df['longitude'], df['latitude'])]

    # Create GeoDataFrame with WGS84 (EPSG:4326)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=geometry,
        crs='EPSG:4326'  # WGS84
    )

    # Project to UTM zone 36S for Malawi (EPSG:32736) for accurate distance calculations
    # This projection uses meters as units
    print("Projecting to UTM Zone 36S (EPSG:32736) for accurate distance calculations...")
    gdf_projected = gdf.to_crs('EPSG:32736')

    print(f"GeoDataFrame created with {len(gdf_projected)} points")
    print(f"CRS: {gdf_projected.crs}")

    return gdf, gdf_projected


def create_buffers(gdf_projected, buffer_radius_km=15):
    """
    Create buffer zones around each candidate site.

    Args:
        gdf_projected: GeoDataFrame in projected CRS (meters)
        buffer_radius_km: Buffer radius in kilometers (default: 15km)

    Returns:
        GeoDataFrame with buffer geometries
    """
    buffer_radius_m = buffer_radius_km * 1000  # Convert km to meters

    print(f"\nCreating {buffer_radius_km}km buffers around each candidate site...")
    print(f"Buffer radius: {buffer_radius_m:,} meters")

    # Create buffers (in meters since we're using projected CRS)
    buffers = gdf_projected.copy()
    buffers['buffer_geometry'] = gdf_projected.geometry.buffer(buffer_radius_m)
    buffers = buffers.set_geometry('buffer_geometry')

    print(f"Created {len(buffers)} buffers")

    return buffers


def create_coverage_matrix(demand_points_gdf, candidate_buffers_gdf):
    """
    Create coverage matrix showing which candidate sites can serve which demand points.

    Args:
        demand_points_gdf: GeoDataFrame of demand points (projected)
        candidate_buffers_gdf: GeoDataFrame with buffer geometries (projected)

    Returns:
        coverage_dict: Dictionary mapping demand_point_id -> [candidate_site_ids]
        reverse_coverage_dict: Dictionary mapping candidate_site_id -> [demand_point_ids]
        coverage_matrix_df: DataFrame representation of the coverage matrix
    """
    print("\nCreating coverage matrix...")
    print("This may take a few minutes for 1,000 points...")

    # Initialize coverage dictionaries
    coverage_dict = {i: [] for i in demand_points_gdf['cluster_id']}
    reverse_coverage_dict = {i: [] for i in candidate_buffers_gdf['cluster_id']}

    # Create coverage matrix (binary: 1 if covered, 0 if not)
    n_demand = len(demand_points_gdf)
    n_candidates = len(candidate_buffers_gdf)

    print(f"Demand points: {n_demand}")
    print(f"Candidate sites: {n_candidates}")
    print(f"Matrix size: {n_demand} x {n_candidates}")

    # Use spatial index for faster intersection checks
    print("\nBuilding spatial index for faster processing...")
    candidate_sindex = candidate_buffers_gdf.sindex

    # For each demand point, find which candidate buffers contain it
    coverage_count = 0
    total_checks = n_demand

    for idx, demand_point in demand_points_gdf.iterrows():
        if idx % 100 == 0:
            print(f"  Processing demand point {idx}/{total_checks}...")

        demand_id = demand_point['cluster_id']
        demand_geom = demand_point.geometry

        # Use spatial index to find potential candidates
        possible_matches_idx = list(candidate_sindex.intersection(demand_geom.bounds))
        possible_matches = candidate_buffers_gdf.iloc[possible_matches_idx]

        # Check actual intersection with buffer
        for cand_idx, candidate in possible_matches.iterrows():
            candidate_id = candidate['cluster_id']
            buffer_geom = candidate['buffer_geometry']

            if buffer_geom.contains(demand_geom):
                coverage_dict[demand_id].append(candidate_id)
                reverse_coverage_dict[candidate_id].append(demand_id)
                coverage_count += 1

    print(f"\nCoverage matrix created!")
    print(f"Total coverage relationships: {coverage_count:,}")
    print(f"Average candidates covering each demand point: {coverage_count / n_demand:.2f}")
    print(f"Average demand points per candidate site: {coverage_count / n_candidates:.2f}")

    # Create DataFrame representation for easier analysis
    coverage_data = []
    for demand_id, candidate_list in coverage_dict.items():
        for candidate_id in candidate_list:
            coverage_data.append({
                'demand_point_id': demand_id,
                'candidate_site_id': candidate_id
            })

    coverage_matrix_df = pd.DataFrame(coverage_data)

    return coverage_dict, reverse_coverage_dict, coverage_matrix_df


def analyze_coverage(coverage_dict, reverse_coverage_dict, demand_df):
    """
    Analyze the coverage matrix and provide statistics.
    """
    print("\n" + "="*70)
    print("COVERAGE ANALYSIS")
    print("="*70)

    # Demand point coverage statistics
    coverage_counts = [len(candidates) for candidates in coverage_dict.values()]

    print("\nDemand Point Coverage:")
    print(f"  Minimum candidates covering a demand point: {min(coverage_counts)}")
    print(f"  Maximum candidates covering a demand point: {max(coverage_counts)}")
    print(f"  Average candidates per demand point: {np.mean(coverage_counts):.2f}")
    print(f"  Median candidates per demand point: {np.median(coverage_counts):.0f}")

    # Check for uncovered demand points
    uncovered = [demand_id for demand_id, candidates in coverage_dict.items() if len(candidates) == 0]
    if uncovered:
        print(f"\n  WARNING: {len(uncovered)} demand points have NO coverage!")
        print(f"  Uncovered demand point IDs: {uncovered[:10]}{'...' if len(uncovered) > 10 else ''}")
    else:
        print(f"\n  ✓ All demand points have at least one candidate site within 5km")

    # Candidate site coverage statistics
    site_coverage_counts = [len(demands) for demands in reverse_coverage_dict.values()]

    print("\nCandidate Site Coverage:")
    print(f"  Minimum demand points covered by a site: {min(site_coverage_counts)}")
    print(f"  Maximum demand points covered by a site: {max(site_coverage_counts)}")
    print(f"  Average demand points per site: {np.mean(site_coverage_counts):.2f}")
    print(f"  Median demand points per site: {np.median(site_coverage_counts):.0f}")

    # Population coverage analysis
    print("\nPopulation Coverage:")

    # For each candidate site, calculate total population it can serve
    site_population_coverage = {}
    for candidate_id, demand_ids in reverse_coverage_dict.items():
        total_pop = demand_df[demand_df['cluster_id'].isin(demand_ids)]['population'].sum()
        site_population_coverage[candidate_id] = total_pop

    pop_coverage_values = list(site_population_coverage.values())
    print(f"  Minimum population covered by a site: {min(pop_coverage_values):,}")
    print(f"  Maximum population covered by a site: {max(pop_coverage_values):,}")
    print(f"  Average population per site: {np.mean(pop_coverage_values):,.0f}")
    print(f"  Median population per site: {np.median(pop_coverage_values):,.0f}")

    # Top 30 sites by population coverage (for the 30 mobile units)
    print(f"\nTop 30 Candidate Sites by Population Coverage:")
    top_30_sites = sorted(site_population_coverage.items(), key=lambda x: x[1], reverse=True)[:30]
    print(f"  {'Rank':<6} {'Site ID':<10} {'Population Covered':<20}")
    print(f"  {'-'*6} {'-'*10} {'-'*20}")
    for rank, (site_id, pop) in enumerate(top_30_sites, 1):
        print(f"  {rank:<6} {site_id:<10} {pop:>18,}")

    total_top_30_coverage = sum([pop for _, pop in top_30_sites])
    total_population = demand_df['population'].sum()
    coverage_pct = (total_top_30_coverage / total_population) * 100

    print(f"\n  Total population if top 30 sites are selected: {total_top_30_coverage:,}")
    print(f"  Overall population: {total_population:,}")
    print(f"  Coverage percentage: {coverage_pct:.2f}%")

    return site_population_coverage, top_30_sites


def save_coverage_data(coverage_dict, reverse_coverage_dict, coverage_matrix_df,
                       demand_df, site_population_coverage, top_30_sites):
    """
    Save coverage data to various formats for optimization.
    """
    print("\n" + "="*70)
    print("SAVING COVERAGE DATA")
    print("="*70)

    # 1. Save coverage matrix as CSV
    coverage_csv = 'coverage_matrix.csv'
    coverage_matrix_df.to_csv(coverage_csv, index=False)
    print(f"\n1. Coverage matrix saved to: {coverage_csv}")
    print(f"   Format: demand_point_id, candidate_site_id")
    print(f"   Rows: {len(coverage_matrix_df):,}")

    # 2. Save coverage dictionaries as JSON
    coverage_json = 'coverage_dict.json'
    with open(coverage_json, 'w') as f:
        # Convert numpy types to native Python types for JSON serialization
        coverage_dict_serializable = {
            int(k): [int(v) for v in vals]
            for k, vals in coverage_dict.items()
        }
        json.dump(coverage_dict_serializable, f, indent=2)
    print(f"\n2. Demand point coverage dictionary saved to: {coverage_json}")
    print(f"   Format: {{demand_point_id: [candidate_site_ids]}}")

    reverse_coverage_json = 'reverse_coverage_dict.json'
    with open(reverse_coverage_json, 'w') as f:
        reverse_coverage_dict_serializable = {
            int(k): [int(v) for v in vals]
            for k, vals in reverse_coverage_dict.items()
        }
        json.dump(reverse_coverage_dict_serializable, f, indent=2)
    print(f"\n3. Candidate site coverage dictionary saved to: {reverse_coverage_json}")
    print(f"   Format: {{candidate_site_id: [demand_point_ids]}}")

    # 3. Save site population coverage
    site_pop_df = pd.DataFrame([
        {'candidate_site_id': site_id, 'total_population_covered': pop}
        for site_id, pop in site_population_coverage.items()
    ]).sort_values('total_population_covered', ascending=False)

    site_pop_csv = 'candidate_sites_population_coverage.csv'
    site_pop_df.to_csv(site_pop_csv, index=False)
    print(f"\n4. Candidate site population coverage saved to: {site_pop_csv}")
    print(f"   Columns: candidate_site_id, total_population_covered")
    print(f"   Sorted by population coverage (descending)")

    # 4. Save top 30 sites
    top_30_df = pd.DataFrame([
        {'rank': rank, 'candidate_site_id': site_id, 'population_covered': pop}
        for rank, (site_id, pop) in enumerate(top_30_sites, 1)
    ])

    # Add coordinates and demand count for the top 30
    demand_df_indexed = demand_df.set_index('cluster_id')
    top_30_df['latitude'] = top_30_df['candidate_site_id'].map(demand_df_indexed['latitude'])
    top_30_df['longitude'] = top_30_df['candidate_site_id'].map(demand_df_indexed['longitude'])
    top_30_df['num_demand_points_covered'] = top_30_df['candidate_site_id'].map(
        lambda x: len(reverse_coverage_dict.get(x, []))
    )

    top_30_csv = 'top_30_candidate_sites.csv'
    top_30_df.to_csv(top_30_csv, index=False)
    print(f"\n5. Top 30 candidate sites saved to: {top_30_csv}")
    print(f"   Columns: rank, candidate_site_id, population_covered, latitude, longitude, num_demand_points_covered")

    # 5. Save optimization input data
    optimization_data = {
        'num_demand_points': len(demand_df),
        'num_candidate_sites': len(demand_df),
        'num_mobile_units': 30,
        'buffer_radius_km': 15,
        'total_population': int(demand_df['population'].sum()),
        'coverage_relationships': len(coverage_matrix_df),
        'demand_points': demand_df[['cluster_id', 'latitude', 'longitude', 'population']].to_dict('records'),
        'top_30_sites': top_30_df.to_dict('records')
    }

    optimization_json = 'optimization_input_data.json'
    with open(optimization_json, 'w') as f:
        json.dump(optimization_data, f, indent=2)
    print(f"\n6. Optimization input data saved to: {optimization_json}")
    print(f"   Contains: demand points, candidate sites, coverage parameters")

    # 6. Save statistics
    stats_file = 'coverage_statistics.txt'
    with open(stats_file, 'w') as f:
        f.write("Coverage Matrix Statistics\n")
        f.write("="*70 + "\n\n")
        f.write(f"Problem Parameters:\n")
        f.write(f"  Number of demand points: {len(demand_df):,}\n")
        f.write(f"  Number of candidate sites: {len(demand_df):,}\n")
        f.write(f"  Number of mobile units to place: 30\n")
        f.write(f"  Coverage radius: 15 km\n")
        f.write(f"  Total population: {demand_df['population'].sum():,} children\n\n")

        f.write(f"Coverage Matrix:\n")
        f.write(f"  Total coverage relationships: {len(coverage_matrix_df):,}\n")
        f.write(f"  Average candidates per demand point: {len(coverage_matrix_df) / len(demand_df):.2f}\n")
        f.write(f"  Average demand points per candidate: {len(coverage_matrix_df) / len(demand_df):.2f}\n\n")

        f.write(f"Top 30 Sites Coverage:\n")
        f.write(f"  Total population covered: {sum([pop for _, pop in top_30_sites]):,}\n")
        f.write(f"  Coverage percentage: {(sum([pop for _, pop in top_30_sites]) / demand_df['population'].sum()) * 100:.2f}%\n")

    print(f"\n7. Coverage statistics saved to: {stats_file}")

    print("\n" + "="*70)
    print("All coverage data files saved successfully!")
    print("="*70)


def main():
    """
    Main function to create coverage matrix for optimization.
    """
    print("="*70)
    print("Mobile Clinic Coverage Matrix Generator")
    print("="*70)
    print("\nProblem Setup:")
    print("  - Demand points: Clustered population locations with children count")
    print("  - Candidate sites: Same as demand points (1,000 locations)")
    print("  - Mobile units to place: 30")
    print("  - Coverage radius: 15 km")
    print("="*70)

    # Step 1: Load cluster data
    print("\n1. Loading cluster data...")
    demand_df = load_cluster_data('clustered_children_1000.csv')

    # Step 2: Create GeoDataFrame
    print("\n2. Creating geographic data structures...")
    gdf_wgs84, gdf_projected = create_geodataframe(demand_df)

    # Step 3: Create 5km buffers around each candidate site
    print("\n3. Creating 15km buffers around candidate sites...")
    candidate_buffers = create_buffers(gdf_projected, buffer_radius_km=15)

    # Step 4: Create coverage matrix
    print("\n4. Creating coverage matrix...")
    coverage_dict, reverse_coverage_dict, coverage_matrix_df = create_coverage_matrix(
        gdf_projected, candidate_buffers
    )

    # Step 5: Analyze coverage
    print("\n5. Analyzing coverage...")
    site_population_coverage, top_30_sites = analyze_coverage(
        coverage_dict, reverse_coverage_dict, demand_df
    )

    # Step 6: Save all outputs
    print("\n6. Saving coverage data...")
    save_coverage_data(
        coverage_dict, reverse_coverage_dict, coverage_matrix_df,
        demand_df, site_population_coverage, top_30_sites
    )

    print("\n" + "="*70)
    print("Coverage matrix generation complete!")
    print("="*70)
    print("\nOutput files ready for optimization:")
    print("  1. coverage_matrix.csv - Full coverage matrix")
    print("  2. coverage_dict.json - Demand point -> Candidate sites mapping")
    print("  3. reverse_coverage_dict.json - Candidate site -> Demand points mapping")
    print("  4. candidate_sites_population_coverage.csv - Population each site can serve")
    print("  5. top_30_candidate_sites.csv - Best 30 sites by population coverage")
    print("  6. optimization_input_data.json - All data for optimization solver")
    print("  7. coverage_statistics.txt - Summary statistics")
    print("\nNext step: Use these files in your optimization solver to select optimal 30 sites")


if __name__ == '__main__':
    main()
