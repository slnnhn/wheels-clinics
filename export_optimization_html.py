#!/usr/bin/env python3
"""
Export optimization results as standalone HTML file.
"""

import pandas as pd
import plotly.graph_objects as go
import geopandas as gpd
from shapely.geometry import Point
import json

def load_optimization_results():
    """Load all optimization results from CSV files."""
    demand_df = pd.read_csv('clustered_children_1000.csv')
    optimal_df = pd.read_csv('optimal_facility_locations.csv')
    demand_coverage = pd.read_csv('demand_coverage.csv')

    return demand_df, optimal_df, demand_coverage

def create_map_figure(demand_df, optimal_df, demand_coverage):
    """Create the interactive Plotly map figure."""

    # Use demand_coverage which already has the coverage info
    # Split into covered and uncovered
    covered = demand_coverage[demand_coverage['covered'] == True]
    uncovered = demand_coverage[demand_coverage['covered'] == False]

    # Create figure
    fig = go.Figure()

    # Add uncovered demand points (gray)
    if len(uncovered) > 0:
        fig.add_trace(go.Scattermapbox(
            lat=uncovered['latitude'],
            lon=uncovered['longitude'],
            mode='markers',
            marker=dict(size=6, color='lightgray', opacity=0.5),
            text=uncovered.apply(lambda x: f"Uncovered Demand<br>Population: {x['population']}", axis=1),
            name='Uncovered Demand',
            hovertemplate='<b>%{text}</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>'
        ))

    # Add covered demand points (green)
    if len(covered) > 0:
        fig.add_trace(go.Scattermapbox(
            lat=covered['latitude'],
            lon=covered['longitude'],
            mode='markers',
            marker=dict(size=6, color='lightgreen', opacity=0.6),
            text=covered.apply(lambda x: f"Covered Demand<br>Population: {x['population']}", axis=1),
            name='Covered Demand',
            hovertemplate='<b>%{text}</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>'
        ))

    # Add optimal facility locations (red stars)
    fig.add_trace(go.Scattermapbox(
        lat=optimal_df['latitude'],
        lon=optimal_df['longitude'],
        mode='markers',
        marker=dict(size=15, color='red', symbol='star'),
        text=optimal_df.apply(lambda x: f"Mobile Unit #{int(x['facility_id'])}<br>Population Served: {int(x['people_served'])}", axis=1),
        name='Mobile Units',
        hovertemplate='<b>%{text}</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>'
    ))

    # Calculate center of Malawi
    center_lat = demand_df['latitude'].mean()
    center_lon = demand_df['longitude'].mean()

    # Update layout
    fig.update_layout(
        title={
            'text': f'Mobile Clinic Optimization Results<br><sub>200 Units | 5km Coverage Radius</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=6
        ),
        height=800,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.8)"
        ),
        margin=dict(l=0, r=0, t=60, b=0)
    )

    return fig

def calculate_summary_stats(demand_df, optimal_df, demand_coverage):
    """Calculate summary statistics."""
    total_population = demand_coverage['population'].sum()
    covered_population = demand_coverage[demand_coverage['covered'] == True]['population'].sum()
    coverage_pct = (covered_population / total_population) * 100

    num_facilities = len(optimal_df)
    cost_per_unit = 10000  # Default
    total_cost = num_facilities * cost_per_unit
    cost_per_child = total_cost / covered_population if covered_population > 0 else 0

    # Calculate mean distance for covered points
    covered_points = demand_coverage[demand_coverage['covered'] == True]
    if len(covered_points) > 0:
        mean_distance = covered_points['distance_to_facility_km'].mean()
    else:
        mean_distance = 0

    stats = {
        'num_units': num_facilities,
        'total_population': int(total_population),
        'covered_population': int(covered_population),
        'coverage_pct': coverage_pct,
        'total_cost': total_cost,
        'cost_per_child': cost_per_child,
        'mean_distance': mean_distance
    }

    return stats

def create_html_with_summary(fig, stats):
    """Create HTML with embedded figure and summary statistics."""

    summary_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 1400px; margin: 0 auto; padding: 20px;">
        <h1 style="text-align: center; color: #333;">Mobile Clinic Optimization Dashboard</h1>

        <div style="background-color: #f5f5f5; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
            <h2 style="color: #333; margin-top: 0;">Summary Statistics</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                <div style="background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3 style="margin: 0; color: #666; font-size: 14px;">Number of Mobile Units</h3>
                    <p style="margin: 10px 0 0 0; font-size: 32px; font-weight: bold; color: #2196F3;">{stats['num_units']}</p>
                </div>
                <div style="background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3 style="margin: 0; color: #666; font-size: 14px;">Children Covered</h3>
                    <p style="margin: 10px 0 0 0; font-size: 32px; font-weight: bold; color: #4CAF50;">{stats['covered_population']:,} / {stats['total_population']:,}</p>
                    <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">({stats['coverage_pct']:.2f}%)</p>
                </div>
                <div style="background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3 style="margin: 0; color: #666; font-size: 14px;">Total Cost</h3>
                    <p style="margin: 10px 0 0 0; font-size: 32px; font-weight: bold; color: #FF9800;">${stats['total_cost']:,}</p>
                    <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">${stats['cost_per_child']:.2f} per child</p>
                </div>
                <div style="background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3 style="margin: 0; color: #666; font-size: 14px;">Mean Distance to Facility</h3>
                    <p style="margin: 10px 0 0 0; font-size: 32px; font-weight: bold; color: #9C27B0;">{stats['mean_distance']:.2f} km</p>
                    <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">Average coverage radius</p>
                </div>
            </div>
        </div>

        <div style="background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #333; margin-top: 0;">Interactive Map</h2>
            <p style="color: #666; margin-bottom: 20px;">
                <span style="color: red;">★ Red Stars</span>: Mobile clinic locations |
                <span style="color: lightgreen;">● Light Green</span>: Covered demand points |
                <span style="color: lightgray;">● Gray</span>: Uncovered demand points
            </p>
            {fig.to_html(include_plotlyjs='cdn', div_id='map-div')}
        </div>

        <div style="margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
            <h3 style="margin-top: 0; color: #333;">Methodology</h3>
            <ul style="color: #666; line-height: 1.6;">
                <li><b>Clustering:</b> K-means algorithm reduced 100,000 population points to 1,000 demand centers</li>
                <li><b>Coverage:</b> Each mobile unit has a 5km service radius</li>
                <li><b>Optimization:</b> PuLP solver maximizes population coverage with 200 mobile units constraint</li>
                <li><b>Solver:</b> CBC (COIN-OR Branch and Cut) open-source MILP solver</li>
            </ul>
        </div>

        <footer style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #999;">
            <p>Generated by Mobile Clinic Optimization System | Malawi Wheels Clinics Project</p>
        </footer>
    </div>
    """

    return summary_html

def main():
    print("Loading optimization results...")
    demand_df, optimal_df, demand_coverage = load_optimization_results()

    print("Calculating summary statistics...")
    stats = calculate_summary_stats(demand_df, optimal_df, demand_coverage)

    print("Creating map visualization...")
    fig = create_map_figure(demand_df, optimal_df, demand_coverage)

    print("Generating HTML report...")
    html_content = create_html_with_summary(fig, stats)

    # Save to file
    output_file = 'optimization_dashboard.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n{'='*60}")
    print(f"SUCCESS: Dashboard exported to {output_file}")
    print(f"{'='*60}")
    print(f"\nSummary Statistics:")
    print(f"  Mobile Units: {stats['num_units']}")
    print(f"  Population Covered: {stats['covered_population']:,} / {stats['total_population']:,} ({stats['coverage_pct']:.2f}%)")
    print(f"  Total Cost: ${stats['total_cost']:,}")
    print(f"  Cost per Child: ${stats['cost_per_child']:.2f}")
    print(f"  Mean Distance: {stats['mean_distance']:.2f} km")
    print(f"\nOpen {output_file} in your browser to view the interactive dashboard.")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
