#!/usr/bin/env python3
"""
Interactive visualization of clustered children population data on Malawi map.
Creates an interactive Folium map with cluster markers and population tooltips.
"""

import pandas as pd
import folium
from folium import plugins
import geopandas as gpd
import sys
import os
import json


def load_clustered_data(cluster_file='clustered_children_1000.csv'):
    """Load the clustered population data."""
    if not os.path.exists(cluster_file):
        print(f"Error: Cluster file not found: {cluster_file}")
        print("Please run cluster_children_data.py first to generate the clustered data.")
        sys.exit(1)

    print(f"Loading clustered data from: {cluster_file}")
    df = pd.read_csv(cluster_file)
    print(f"Loaded {len(df):,} cluster centers")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nTotal population: {df['population'].sum():,}")
    print(f"Population range: {df['population'].min():,} - {df['population'].max():,}")

    return df


def load_malawi_boundaries(boundaries_file='malawi_ta_boundaries.geojson'):
    """Load Malawi Traditional Authorities boundaries."""
    if not os.path.exists(boundaries_file):
        print(f"Warning: Boundaries file not found: {boundaries_file}")
        print("Map will be created without administrative boundaries.")
        return None

    print(f"\nLoading Malawi boundaries from: {boundaries_file}")
    gdf = gpd.read_file(boundaries_file)
    print(f"Loaded {len(gdf)} Traditional Authorities")

    return gdf


def create_interactive_map(cluster_df, boundaries_gdf=None, output_file='malawi_clusters_interactive.html'):
    """
    Create an interactive Folium map with cluster markers and tooltips.

    Args:
        cluster_df: DataFrame with cluster centers and population counts
        boundaries_gdf: GeoDataFrame with Malawi boundaries (optional)
        output_file: Output HTML filename
    """
    print("\nCreating interactive map...")

    # Calculate map center (center of Malawi)
    center_lat = cluster_df['latitude'].mean()
    center_lon = cluster_df['longitude'].mean()

    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles='OpenStreetMap',
        control_scale=True
    )

    # Add alternative tile layers
    folium.TileLayer('CartoDB positron', name='Light Map').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='Dark Map').add_to(m)

    # Add boundaries if available
    if boundaries_gdf is not None:
        print("Adding administrative boundaries...")
        folium.GeoJson(
            boundaries_gdf,
            name='Traditional Authorities',
            style_function=lambda x: {
                'fillColor': 'lightgray',
                'color': 'black',
                'weight': 1.5,
                'fillOpacity': 0.1
            },
            tooltip=folium.GeoJsonTooltip(fields=['TA_NAME'] if 'TA_NAME' in boundaries_gdf.columns else [])
        ).add_to(m)

    # Calculate population statistics for color scaling
    pop_min = cluster_df['population'].min()
    pop_max = cluster_df['population'].max()
    pop_mean = cluster_df['population'].mean()
    pop_median = cluster_df['population'].median()

    print(f"Population stats for color scaling:")
    print(f"  Min: {pop_min:,}, Max: {pop_max:,}")
    print(f"  Mean: {pop_mean:.0f}, Median: {pop_median:.0f}")

    # Create color scale function
    def get_color(population):
        """Get color based on population size using gradient."""
        if population < pop_mean * 0.5:
            return '#fee5d9'  # Very light
        elif population < pop_mean:
            return '#fcae91'  # Light orange
        elif population < pop_median * 1.5:
            return '#fb6a4a'  # Orange
        elif population < pop_mean * 1.5:
            return '#de2d26'  # Red
        else:
            return '#a50f15'  # Dark red

    # Create marker cluster group (optional - can toggle on/off)
    marker_cluster = plugins.MarkerCluster(name='Clustered View').add_to(m)

    # Create regular markers group
    markers_group = folium.FeatureGroup(name='Individual Markers', show=True).add_to(m)

    # Add cluster markers
    print(f"Adding {len(cluster_df)} cluster markers...")

    for idx, row in cluster_df.iterrows():
        lat = row['latitude']
        lon = row['longitude']
        pop = row['population']
        cluster_id = row['cluster_id']

        # Create popup HTML with detailed information
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <h4 style="margin-bottom: 10px; color: #333;">Cluster #{cluster_id}</h4>
            <hr style="margin: 5px 0;">
            <table style="width: 100%; font-size: 12px;">
                <tr>
                    <td style="padding: 3px;"><b>Population:</b></td>
                    <td style="padding: 3px; text-align: right;">{pop:,} children</td>
                </tr>
                <tr>
                    <td style="padding: 3px;"><b>Latitude:</b></td>
                    <td style="padding: 3px; text-align: right;">{lat:.6f}</td>
                </tr>
                <tr>
                    <td style="padding: 3px;"><b>Longitude:</b></td>
                    <td style="padding: 3px; text-align: right;">{lon:.6f}</td>
                </tr>
            </table>
        </div>
        """

        # Tooltip (shows on hover)
        tooltip_text = f"Cluster {cluster_id}: {pop:,} children"

        # Determine marker size based on population
        radius = min(3 + (pop / pop_mean) * 5, 15)  # Scale radius, max 15

        # Add to individual markers group
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=tooltip_text,
            color='black',
            fillColor=get_color(pop),
            fillOpacity=0.7,
            weight=1
        ).add_to(markers_group)

        # Add to marker cluster (simplified for clustering)
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=tooltip_text,
            icon=folium.Icon(color='red', icon='users', prefix='fa')
        ).add_to(marker_cluster)

    # Add heatmap layer
    print("Adding heatmap layer...")
    heat_data = [[row['latitude'], row['longitude'], row['population']]
                 for idx, row in cluster_df.iterrows()]

    plugins.HeatMap(
        heat_data,
        name='Population Heatmap',
        min_opacity=0.3,
        max_zoom=13,
        radius=15,
        blur=20,
        gradient={0.4: 'blue', 0.6: 'lime', 0.8: 'yellow', 1.0: 'red'},
        show=False  # Hidden by default
    ).add_to(m)

    # Add legend
    legend_html = f"""
    <div style="position: fixed;
                bottom: 50px; right: 50px; width: 280px; height: auto;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:14px; padding: 10px; border-radius: 5px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);">
        <h4 style="margin-top: 0;">Malawi Children Under 5</h4>
        <p style="margin: 5px 0;"><b>Clustering Summary:</b></p>
        <table style="width: 100%; font-size: 12px;">
            <tr><td>Total Clusters:</td><td style="text-align: right;"><b>{len(cluster_df):,}</b></td></tr>
            <tr><td>Total Population:</td><td style="text-align: right;"><b>{cluster_df['population'].sum():,}</b></td></tr>
            <tr><td>Avg per Cluster:</td><td style="text-align: right;"><b>{cluster_df['population'].mean():.0f}</b></td></tr>
            <tr><td>Max Cluster:</td><td style="text-align: right;"><b>{pop_max:,}</b></td></tr>
        </table>
        <hr style="margin: 8px 0;">
        <p style="margin: 5px 0;"><b>Population Density:</b></p>
        <div style="margin: 5px 0;">
            <span style="background-color: #fee5d9; padding: 2px 8px; border: 1px solid #ccc;">Very Low</span><br>
            <span style="background-color: #fcae91; padding: 2px 8px; border: 1px solid #ccc;">Low</span><br>
            <span style="background-color: #fb6a4a; padding: 2px 8px; border: 1px solid #ccc;">Medium</span><br>
            <span style="background-color: #de2d26; padding: 2px 8px; border: 1px solid #ccc; color: white;">High</span><br>
            <span style="background-color: #a50f15; padding: 2px 8px; border: 1px solid #ccc; color: white;">Very High</span>
        </div>
        <hr style="margin: 8px 0;">
        <p style="margin: 2px 0; font-size: 11px; color: #666;">
            Click markers for details<br>
            Use layer control (top right) to toggle views
        </p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)

    # Add fullscreen button
    plugins.Fullscreen(
        position='topleft',
        title='Fullscreen',
        title_cancel='Exit fullscreen',
        force_separate_button=True
    ).add_to(m)

    # Add mouse position
    plugins.MousePosition().add_to(m)

    # Add measure control
    plugins.MeasureControl(position='topleft', primary_length_unit='kilometers').add_to(m)

    # Save map
    m.save(output_file)
    print(f"\n{'='*70}")
    print(f"Interactive map saved to: {output_file}")
    print(f"{'='*70}")
    print(f"\nMap features:")
    print(f"  - {len(cluster_df):,} cluster markers with population tooltips")
    print(f"  - Hover over markers to see population count")
    print(f"  - Click markers for detailed information")
    print(f"  - Multiple map layers (street, light, dark)")
    print(f"  - Heatmap overlay (toggle in layer control)")
    print(f"  - Clustered view for better performance")
    print(f"  - Administrative boundaries overlay")
    print(f"  - Legend with statistics")
    print(f"\nOpen {output_file} in a web browser to view the map.")


def main():
    """Main function to create the interactive visualization."""
    print("="*70)
    print("Malawi Children Clusters - Interactive Map Visualization")
    print("="*70)

    # Configuration
    CLUSTER_FILE = 'clustered_children_1000.csv'
    BOUNDARIES_FILE = 'malawi_ta_boundaries.geojson'
    OUTPUT_FILE = 'malawi_clusters_interactive.html'

    # Load data
    print("\n1. Loading cluster data...")
    cluster_df = load_clustered_data(CLUSTER_FILE)

    # Load boundaries (optional)
    print("\n2. Loading boundaries...")
    boundaries_gdf = load_malawi_boundaries(BOUNDARIES_FILE)

    # Create map
    print("\n3. Creating interactive map...")
    create_interactive_map(cluster_df, boundaries_gdf, OUTPUT_FILE)

    print("\n" + "="*70)
    print("Visualization complete!")
    print("="*70)


if __name__ == '__main__':
    main()
