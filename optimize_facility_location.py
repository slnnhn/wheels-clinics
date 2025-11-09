#!/usr/bin/env python3
"""
PuLP optimization solver for mobile clinic facility location problem.
Maximizes population coverage with a fixed number of mobile units.
"""

import pandas as pd
import numpy as np
import json
from pulp import *
import time
from scipy.spatial.distance import cdist
import geopandas as gpd
from shapely.geometry import Point


def load_optimization_data():
    """Load all necessary data for optimization."""
    print("Loading optimization data...")

    # Load demand points with population
    demand_df = pd.read_csv('clustered_children_1000.csv')

    # Load coverage dictionary
    with open('coverage_dict.json') as f:
        coverage_dict = json.load(f)

    # Load reverse coverage dictionary
    with open('reverse_coverage_dict.json') as f:
        reverse_coverage_dict = json.load(f)

    # Load optimization parameters
    with open('optimization_input_data.json') as f:
        opt_params = json.load(f)

    print(f"Loaded {len(demand_df)} demand points")
    print(f"Total population: {demand_df['population'].sum():,}")

    return demand_df, coverage_dict, reverse_coverage_dict, opt_params


def calculate_distance_matrix(demand_df):
    """
    Calculate distance matrix between all points in kilometers.
    Uses projected coordinates for accuracy.
    """
    print("\nCalculating distance matrix...")

    # Create GeoDataFrame
    geometry = [Point(lon, lat) for lon, lat in zip(demand_df['longitude'], demand_df['latitude'])]
    gdf = gpd.GeoDataFrame(demand_df, geometry=geometry, crs='EPSG:4326')

    # Project to UTM for distance calculations in meters
    gdf_projected = gdf.to_crs('EPSG:32736')

    # Get coordinates as array
    coords = np.array([[geom.x, geom.y] for geom in gdf_projected.geometry])

    # Calculate pairwise distances in meters
    distance_matrix = cdist(coords, coords, metric='euclidean')

    # Convert to kilometers
    distance_matrix_km = distance_matrix / 1000

    return distance_matrix_km


def solve_maximal_coverage(demand_df, coverage_dict, reverse_coverage_dict, num_facilities=200):
    """
    Solve maximal coverage location problem using PuLP.

    Objective: Maximize total population covered
    Constraint: Select exactly num_facilities sites

    Args:
        demand_df: DataFrame with demand points and population
        coverage_dict: Dict mapping demand points to candidate sites that cover them
        reverse_coverage_dict: Dict mapping candidate sites to demand points they cover
        num_facilities: Number of facilities to place (default: 200)

    Returns:
        selected_sites: List of selected site IDs
        covered_demands: List of covered demand point IDs
        total_coverage: Total population covered
        solve_time: Time taken to solve (seconds)
    """
    print("\n" + "="*70)
    print("MAXIMAL COVERAGE OPTIMIZATION")
    print("="*70)
    print(f"\nProblem size:")
    print(f"  Demand points: {len(demand_df)}")
    print(f"  Candidate sites: {len(reverse_coverage_dict)}")
    print(f"  Facilities to place: {num_facilities}")
    print(f"  Total population: {demand_df['population'].sum():,}")

    start_time = time.time()

    # Create the optimization problem
    prob = LpProblem("Mobile_Clinic_Maximal_Coverage", LpMaximize)

    # Decision variables
    # x[i] = 1 if we place a facility at candidate site i, 0 otherwise
    candidate_ids = list(range(len(demand_df)))
    x = LpVariable.dicts("site", candidate_ids, cat='Binary')

    # y[j] = 1 if demand point j is covered, 0 otherwise
    demand_ids = list(range(len(demand_df)))
    y = LpVariable.dicts("covered", demand_ids, cat='Binary')

    # Objective: Maximize total covered population
    prob += lpSum([demand_df.iloc[j]['population'] * y[j] for j in demand_ids]), "Total_Coverage"

    # Constraint 1: Select exactly num_facilities sites
    prob += lpSum([x[i] for i in candidate_ids]) == num_facilities, "Facility_Limit"

    # Constraint 2: A demand point is covered only if at least one covering site is selected
    for j in demand_ids:
        # Get candidate sites that can cover demand point j
        covering_sites = [int(site) for site in coverage_dict.get(str(j), [])]

        if covering_sites:
            # Demand j can only be covered if at least one covering site is selected
            prob += y[j] <= lpSum([x[i] for i in covering_sites]), f"Coverage_Demand_{j}"
        else:
            # If no sites can cover this demand, it cannot be covered
            prob += y[j] == 0, f"No_Coverage_Demand_{j}"

    # Solve the problem
    print("\nSolving optimization problem...")
    print("This may take a few minutes...")

    # Use CBC solver (default, open source)
    prob.solve(PULP_CBC_CMD(msg=1, timeLimit=300))  # 5 minute time limit

    solve_time = time.time() - start_time

    # Check solution status
    status = LpStatus[prob.status]
    print(f"\nOptimization Status: {status}")
    print(f"Solve time: {solve_time:.2f} seconds")

    if status != 'Optimal':
        print(f"Warning: Solution is {status}, not Optimal")

    # Extract solution
    selected_sites = [i for i in candidate_ids if x[i].varValue == 1]
    covered_demands = [j for j in demand_ids if y[j].varValue == 1]

    # Calculate coverage statistics
    total_population = demand_df['population'].sum()
    covered_population = sum(demand_df.iloc[j]['population'] for j in covered_demands)
    coverage_percentage = (covered_population / total_population) * 100

    print("\n" + "="*70)
    print("OPTIMIZATION RESULTS")
    print("="*70)
    print(f"\nSites selected: {len(selected_sites)} / {num_facilities}")
    print(f"Demand points covered: {len(covered_demands)} / {len(demand_df)}")
    print(f"Population covered: {covered_population:,} / {total_population:,}")
    print(f"Coverage percentage: {coverage_percentage:.2f}%")
    print(f"Uncovered population: {total_population - covered_population:,}")

    return selected_sites, covered_demands, covered_population, solve_time


def calculate_coverage_statistics(demand_df, selected_sites, covered_demands, distance_matrix_km):
    """
    Calculate detailed statistics about the coverage solution.
    """
    print("\n" + "="*70)
    print("COVERAGE STATISTICS")
    print("="*70)

    # For each demand point, find distance to nearest selected facility
    demand_to_facility_distances = []

    for demand_id in range(len(demand_df)):
        if demand_id in covered_demands:
            # Find nearest selected facility
            distances_to_facilities = [distance_matrix_km[demand_id][site] for site in selected_sites]
            min_distance = min(distances_to_facilities)
            demand_to_facility_distances.append(min_distance)
        else:
            # Uncovered demand point
            demand_to_facility_distances.append(None)

    # Calculate statistics for covered demands
    covered_distances = [d for d in demand_to_facility_distances if d is not None]

    if covered_distances:
        print(f"\nDistance to Nearest Facility (Covered Demands):")
        print(f"  Mean: {np.mean(covered_distances):.2f} km")
        print(f"  Median: {np.median(covered_distances):.2f} km")
        print(f"  Min: {np.min(covered_distances):.2f} km")
        print(f"  Max: {np.max(covered_distances):.2f} km")
        print(f"  Std Dev: {np.std(covered_distances):.2f} km")

    # Population per facility
    facility_populations = []
    for site_id in selected_sites:
        # Find which demand points are served by this facility
        # (demand points within coverage radius of this site)
        served_demands = [j for j in covered_demands if distance_matrix_km[j][site_id] <= 5.0]
        facility_pop = sum(demand_df.iloc[j]['population'] for j in served_demands)
        facility_populations.append(facility_pop)

    print(f"\nPopulation per Facility:")
    print(f"  Mean: {np.mean(facility_populations):.0f}")
    print(f"  Median: {np.median(facility_populations):.0f}")
    print(f"  Min: {np.min(facility_populations):.0f}")
    print(f"  Max: {np.max(facility_populations):.0f}")

    return demand_to_facility_distances, covered_distances


def save_solution(demand_df, selected_sites, covered_demands, covered_population,
                  solve_time, distance_matrix_km, num_facilities=200, cost_per_unit=10000):
    """
    Save the optimization solution to files.
    """
    print("\n" + "="*70)
    print("SAVING SOLUTION")
    print("="*70)

    # Create solution DataFrame for selected sites
    solution_sites = demand_df.iloc[selected_sites].copy()
    solution_sites['selected'] = True
    solution_sites['facility_id'] = range(len(selected_sites))

    # Calculate number of people served by each facility
    facility_coverage = []
    for site_id in selected_sites:
        served_demands = [j for j in covered_demands if distance_matrix_km[j][site_id] <= 5.0]
        people_served = sum(demand_df.iloc[j]['population'] for j in served_demands)
        facility_coverage.append(people_served)

    solution_sites['people_served'] = facility_coverage

    # Save to CSV
    solution_csv = 'optimal_facility_locations.csv'
    solution_sites.to_csv(solution_csv, index=False)
    print(f"\n1. Optimal facility locations saved to: {solution_csv}")

    # Create coverage DataFrame (which demands are covered)
    coverage_df = demand_df.copy()
    coverage_df['covered'] = coverage_df.index.isin(covered_demands)

    # Find nearest facility for each demand point
    nearest_facility = []
    distance_to_facility = []

    for demand_id in range(len(demand_df)):
        if demand_id in covered_demands:
            distances = [(site, distance_matrix_km[demand_id][site]) for site in selected_sites]
            nearest_site, min_dist = min(distances, key=lambda x: x[1])
            nearest_facility.append(nearest_site)
            distance_to_facility.append(min_dist)
        else:
            nearest_facility.append(None)
            distance_to_facility.append(None)

    coverage_df['nearest_facility_id'] = nearest_facility
    coverage_df['distance_to_facility_km'] = distance_to_facility

    coverage_csv = 'demand_coverage.csv'
    coverage_df.to_csv(coverage_csv, index=False)
    print(f"2. Demand point coverage saved to: {coverage_csv}")

    # Calculate mean distance for covered demands
    covered_distances = [d for d in distance_to_facility if d is not None]
    mean_distance = np.mean(covered_distances) if covered_distances else 0

    # Create solution summary
    total_population = demand_df['population'].sum()
    total_cost = num_facilities * cost_per_unit
    cost_per_child = total_cost / covered_population if covered_population > 0 else 0

    solution_summary = {
        'num_facilities': num_facilities,
        'cost_per_unit': cost_per_unit,
        'total_cost': total_cost,
        'total_population': int(total_population),
        'covered_population': int(covered_population),
        'coverage_percentage': float(covered_population / total_population * 100),
        'uncovered_population': int(total_population - covered_population),
        'num_covered_demands': len(covered_demands),
        'num_uncovered_demands': len(demand_df) - len(covered_demands),
        'mean_distance_km': float(mean_distance),
        'cost_per_child_served': float(cost_per_child),
        'solve_time_seconds': solve_time,
        'selected_site_ids': selected_sites
    }

    solution_json = 'optimization_solution.json'
    with open(solution_json, 'w') as f:
        json.dump(solution_summary, f, indent=2)
    print(f"3. Solution summary saved to: {solution_json}")

    # Save statistics
    stats_file = 'optimization_statistics.txt'
    with open(stats_file, 'w') as f:
        f.write("Mobile Clinic Optimization - Solution Summary\n")
        f.write("="*70 + "\n\n")
        f.write(f"Problem Parameters:\n")
        f.write(f"  Number of facilities: {num_facilities}\n")
        f.write(f"  Cost per unit: ${cost_per_unit:,}\n")
        f.write(f"  Coverage radius: 5 km\n")
        f.write(f"  Solve time: {solve_time:.2f} seconds\n\n")

        f.write(f"Coverage Results:\n")
        f.write(f"  Total population: {total_population:,} children\n")
        f.write(f"  Covered population: {covered_population:,} children ({covered_population/total_population*100:.2f}%)\n")
        f.write(f"  Uncovered population: {total_population - covered_population:,} children\n")
        f.write(f"  Demand points covered: {len(covered_demands)} / {len(demand_df)}\n\n")

        f.write(f"Distance Statistics (Covered Demands):\n")
        f.write(f"  Mean distance to facility: {mean_distance:.2f} km\n")
        if covered_distances:
            f.write(f"  Median distance: {np.median(covered_distances):.2f} km\n")
            f.write(f"  Max distance: {np.max(covered_distances):.2f} km\n\n")

        f.write(f"Cost Analysis:\n")
        f.write(f"  Total cost: ${total_cost:,}\n")
        f.write(f"  Cost per child served: ${cost_per_child:.2f}\n")

    print(f"4. Statistics saved to: {stats_file}")

    print("\n" + "="*70)
    print("Solution saved successfully!")
    print("="*70)

    return solution_summary


def main(num_facilities=200, cost_per_unit=10000):
    """
    Main optimization workflow.

    Args:
        num_facilities: Number of mobile units to place
        cost_per_unit: Cost per mobile unit in dollars
    """
    print("="*70)
    print("Mobile Clinic Facility Location Optimization")
    print("="*70)
    print(f"\nParameters:")
    print(f"  Number of facilities: {num_facilities}")
    print(f"  Cost per unit: ${cost_per_unit:,}")
    print(f"  Total budget: ${num_facilities * cost_per_unit:,}")

    # Load data
    demand_df, coverage_dict, reverse_coverage_dict, opt_params = load_optimization_data()

    # Calculate distance matrix
    distance_matrix_km = calculate_distance_matrix(demand_df)

    # Solve optimization
    selected_sites, covered_demands, covered_population, solve_time = solve_maximal_coverage(
        demand_df, coverage_dict, reverse_coverage_dict, num_facilities
    )

    # Calculate statistics
    demand_distances, covered_distances = calculate_coverage_statistics(
        demand_df, selected_sites, covered_demands, distance_matrix_km
    )

    # Save solution
    solution_summary = save_solution(
        demand_df, selected_sites, covered_demands, covered_population,
        solve_time, distance_matrix_km, num_facilities, cost_per_unit
    )

    print("\n" + "="*70)
    print("OPTIMIZATION COMPLETE")
    print("="*70)
    print(f"\nKey Results:")
    print(f"  ✓ {len(selected_sites)} facilities optimally placed")
    print(f"  ✓ {covered_population:,} children covered ({covered_population/demand_df['population'].sum()*100:.2f}%)")
    print(f"  ✓ Mean distance: {np.mean(covered_distances):.2f} km")
    print(f"  ✓ Total cost: ${num_facilities * cost_per_unit:,}")
    print(f"\nOutput files:")
    print(f"  - optimal_facility_locations.csv")
    print(f"  - demand_coverage.csv")
    print(f"  - optimization_solution.json")
    print(f"  - optimization_statistics.txt")
    print(f"\nNext: Run visualize_optimization_dashboard.py to view interactive dashboard")

    return solution_summary


if __name__ == '__main__':
    import sys

    # Allow command line arguments
    num_facilities = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    cost_per_unit = float(sys.argv[2]) if len(sys.argv) > 2 else 10000

    main(num_facilities, cost_per_unit)
