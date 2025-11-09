#!/usr/bin/env python3
"""
Interactive dashboard for mobile clinic optimization.
Visualizes facility locations, demand points, and coverage statistics.
Allows users to adjust parameters and re-run optimization.
"""

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
import os
from optimize_facility_location import main as run_optimization


# Initialize the Dash app
app = dash.Dash(__name__)

# Load initial data
def load_data():
    """Load demand points and solution (if exists)."""
    demand_df = pd.read_csv('clustered_children_1000.csv')

    # Try to load existing solution
    if os.path.exists('optimization_solution.json'):
        with open('optimization_solution.json') as f:
            solution = json.load(f)

        facility_df = pd.read_csv('optimal_facility_locations.csv')
        coverage_df = pd.read_csv('demand_coverage.csv')
    else:
        solution = None
        facility_df = None
        coverage_df = None

    # Load boundaries
    if os.path.exists('malawi_ta_boundaries.geojson'):
        import geopandas as gpd
        boundaries_gdf = gpd.read_file('malawi_ta_boundaries.geojson')
    else:
        boundaries_gdf = None

    return demand_df, solution, facility_df, coverage_df, boundaries_gdf


def create_map_figure(demand_df, facility_df=None, coverage_df=None, boundaries_gdf=None):
    """Create the main map visualization."""
    fig = go.Figure()

    # Add boundaries if available
    if boundaries_gdf is not None:
        for idx, row in boundaries_gdf.iterrows():
            geom = row.geometry

            if geom.geom_type == 'Polygon':
                coords = list(geom.exterior.coords)
            elif geom.geom_type == 'MultiPolygon':
                coords = list(geom.geoms[0].exterior.coords)
            else:
                continue

            lons, lats = zip(*coords)

            fig.add_trace(go.Scattermapbox(
                lon=list(lons),
                lat=list(lats),
                mode='lines',
                line=dict(color='gray', width=1),
                fill='toself',
                fillcolor='rgba(200, 200, 200, 0.1)',
                name='Boundaries',
                showlegend=False,
                hoverinfo='skip'
            ))

    # Determine coverage status if available
    if coverage_df is not None:
        covered_mask = coverage_df['covered']
        covered_demands = demand_df[covered_mask]
        uncovered_demands = demand_df[~covered_mask]

        # Plot covered demand points
        fig.add_trace(go.Scattermapbox(
            lon=covered_demands['longitude'],
            lat=covered_demands['latitude'],
            mode='markers',
            marker=dict(
                size=8,
                color=covered_demands['population'],
                colorscale='Greens',
                showscale=True,
                colorbar=dict(title="Population", x=1.15),
                opacity=0.7,
                line=dict(color='darkgreen', width=1)
            ),
            text=[f"Demand Point {i}<br>Population: {p:,}<br>Status: Covered<br>Distance: {d:.2f} km"
                  for i, p, d in zip(covered_demands['cluster_id'],
                                    covered_demands['population'],
                                    coverage_df[covered_mask]['distance_to_facility_km'])],
            hoverinfo='text',
            name='Covered Demand Points'
        ))

        # Plot uncovered demand points
        fig.add_trace(go.Scattermapbox(
            lon=uncovered_demands['longitude'],
            lat=uncovered_demands['latitude'],
            mode='markers',
            marker=dict(
                size=6,
                color='lightcoral',
                opacity=0.5,
                line=dict(color='red', width=1)
            ),
            text=[f"Demand Point {i}<br>Population: {p:,}<br>Status: UNCOVERED"
                  for i, p in zip(uncovered_demands['cluster_id'],
                                 uncovered_demands['population'])],
            hoverinfo='text',
            name='Uncovered Demand Points'
        ))
    else:
        # Just plot all demand points
        fig.add_trace(go.Scattermapbox(
            lon=demand_df['longitude'],
            lat=demand_df['latitude'],
            mode='markers',
            marker=dict(
                size=8,
                color=demand_df['population'],
                colorscale='Blues',
                showscale=True,
                colorbar=dict(title="Population"),
                opacity=0.6
            ),
            text=[f"Demand Point {i}<br>Population: {p:,}"
                  for i, p in zip(demand_df['cluster_id'], demand_df['population'])],
            hoverinfo='text',
            name='Demand Points'
        ))

    # Plot facility locations if available
    if facility_df is not None:
        fig.add_trace(go.Scattermapbox(
            lon=facility_df['longitude'],
            lat=facility_df['latitude'],
            mode='markers',
            marker=dict(
                size=15,
                color='red',
                symbol='star',
                opacity=0.9,
                line=dict(color='darkred', width=2)
            ),
            text=[f"<b>Mobile Unit #{i}</b><br>Location: Site {site}<br>People Served: {p:,}<br>Lat: {lat:.4f}, Lon: {lon:.4f}"
                  for i, site, p, lat, lon in zip(
                      facility_df['facility_id'],
                      facility_df['cluster_id'],
                      facility_df['people_served'],
                      facility_df['latitude'],
                      facility_df['longitude']
                  )],
            hoverinfo='text',
            name='Mobile Units'
        ))

    # Set map layout
    center_lat = demand_df['latitude'].mean()
    center_lon = demand_df['longitude'].mean()

    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=6
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=800,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.8)"
        )
    )

    return fig


def create_summary_panel(solution):
    """Create summary statistics panel."""
    if solution is None:
        return html.Div([
            html.H4("No optimization run yet", className="text-muted"),
            html.P("Click 'Run Optimization' to solve the problem.")
        ])

    return html.Div([
        html.H4("📊 Optimization Results", className="mb-3"),

        html.Div([
            html.Div([
                html.H5(f"{solution['covered_population']:,}", className="text-success mb-0"),
                html.Small("People Served", className="text-muted")
            ], className="mb-3"),

            html.Div([
                html.H5(f"{solution['coverage_percentage']:.2f}%", className="text-info mb-0"),
                html.Small("Coverage Rate", className="text-muted")
            ], className="mb-3"),

            html.Div([
                html.H5(f"{solution['num_covered_demands']:,} / {solution['num_covered_demands'] + solution['num_uncovered_demands']:,}",
                       className="text-primary mb-0"),
                html.Small("Demand Points Covered", className="text-muted")
            ], className="mb-3"),
        ]),

        html.Hr(),

        html.H5("💰 Cost Analysis", className="mt-3 mb-2"),
        html.Div([
            html.P([
                html.Strong("Total Cost: "),
                f"${solution['total_cost']:,}"
            ], className="mb-2"),

            html.P([
                html.Strong("Cost per Unit: "),
                f"${solution['cost_per_unit']:,}"
            ], className="mb-2"),

            html.P([
                html.Strong("Cost per Child Served: "),
                f"${solution['cost_per_child_served']:.2f}"
            ], className="mb-2"),
        ]),

        html.Hr(),

        html.H5("📍 Distance Metrics", className="mt-3 mb-2"),
        html.Div([
            html.P([
                html.Strong("Mean Distance to Facility: "),
                f"{solution['mean_distance_km']:.2f} km"
            ], className="mb-2"),

            html.P([
                html.Strong("Coverage Radius: "),
                "5.00 km"
            ], className="mb-2"),
        ]),

        html.Hr(),

        html.H5("⏱️ Performance", className="mt-3 mb-2"),
        html.P([
            html.Strong("Solve Time: "),
            f"{solution['solve_time_seconds']:.2f} seconds"
        ], className="mb-2"),
    ])


# Define the app layout
app.layout = html.Div([
    html.Div([
        # Left Panel - Controls
        html.Div([
            html.H2("🏥 Mobile Clinic Optimizer", className="mb-4"),

            html.Hr(),

            html.H4("⚙️ Parameters", className="mb-3"),

            # Number of units slider
            html.Label("Number of Mobile Units:", className="form-label"),
            dcc.Slider(
                id='num-units-slider',
                min=10,
                max=500,
                step=10,
                value=200,
                marks={i: str(i) for i in range(0, 501, 50)},
                tooltip={"placement": "bottom", "always_visible": True}
            ),

            html.Br(),

            # Cost per unit input
            html.Label("Cost per Unit ($):", className="form-label mt-3"),
            dcc.Input(
                id='cost-per-unit-input',
                type='number',
                value=10000,
                min=0,
                step=1000,
                className="form-control",
                style={'width': '100%'}
            ),

            html.Br(),
            html.Br(),

            # Run optimization button
            html.Button(
                '▶️ Run Optimization',
                id='optimize-button',
                n_clicks=0,
                className="btn btn-primary btn-lg w-100 mb-3"
            ),

            html.Div(id='optimization-status', className="alert alert-info", style={'display': 'none'}),

            html.Hr(),

            # Summary panel
            html.Div(id='summary-panel', children=create_summary_panel(None))

        ], className="col-md-3 p-4", style={'backgroundColor': '#f8f9fa', 'height': '100vh', 'overflowY': 'auto'}),

        # Right Panel - Map
        html.Div([
            dcc.Graph(id='map-figure', config={'displayModeBar': True})
        ], className="col-md-9 p-0")

    ], className="row g-0")
], className="container-fluid")


# Callback to run optimization
@app.callback(
    [Output('map-figure', 'figure'),
     Output('summary-panel', 'children'),
     Output('optimization-status', 'children'),
     Output('optimization-status', 'style')],
    [Input('optimize-button', 'n_clicks')],
    [State('num-units-slider', 'value'),
     State('cost-per-unit-input', 'value')]
)
def run_optimization_callback(n_clicks, num_units, cost_per_unit):
    """Run optimization when button is clicked."""
    if n_clicks == 0:
        # Initial load
        demand_df, solution, facility_df, coverage_df, boundaries_gdf = load_data()
        fig = create_map_figure(demand_df, facility_df, coverage_df, boundaries_gdf)
        summary = create_summary_panel(solution)
        return fig, summary, "", {'display': 'none'}

    # Show status message
    status_msg = f"⏳ Running optimization with {num_units} units at ${cost_per_unit:,} each..."
    status_style = {'display': 'block'}

    try:
        # Run optimization
        solution = run_optimization(num_facilities=int(num_units), cost_per_unit=float(cost_per_unit))

        # Reload data
        demand_df, solution, facility_df, coverage_df, boundaries_gdf = load_data()

        # Create updated figure
        fig = create_map_figure(demand_df, facility_df, coverage_df, boundaries_gdf)

        # Create summary
        summary = create_summary_panel(solution)

        status_msg = f"✅ Optimization complete! {solution['covered_population']:,} people covered."
        status_style = {'display': 'block', 'backgroundColor': '#d4edda', 'color': '#155724'}

        return fig, summary, status_msg, status_style

    except Exception as e:
        status_msg = f"❌ Error: {str(e)}"
        status_style = {'display': 'block', 'backgroundColor': '#f8d7da', 'color': '#721c24'}

        demand_df, solution, facility_df, coverage_df, boundaries_gdf = load_data()
        fig = create_map_figure(demand_df, facility_df, coverage_df, boundaries_gdf)
        summary = create_summary_panel(solution)

        return fig, summary, status_msg, status_style


if __name__ == '__main__':
    print("="*70)
    print("Mobile Clinic Optimization Dashboard")
    print("="*70)
    print("\nStarting dashboard server...")
    print("Open your browser and navigate to: http://127.0.0.1:8050")
    print("\nPress Ctrl+C to stop the server")
    print("="*70)

    app.run_server(debug=True, host='0.0.0.0', port=8050)
