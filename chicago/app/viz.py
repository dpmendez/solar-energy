import plotly.express as px
import json

def plot_top_k_mapbox(top_k_gdf, color_col="kwh_estimate", map_title="Top Buildings by Estimated Energy Output"):
    """
    Returns a Plotly choropleth_mapbox for the top-k buildings, assumed sorted by `color_col`.

    Parameters:
        top_k_gdf (GeoDataFrame): GeoDataFrame of top buildings.
        color_col (str): The column to color by (e.g., 'kwh_estimate').
        map_title (str): Title for the map.

    Returns:
        fig (plotly.graph_objs.Figure): Mapbox choropleth figure.
    """
    # Prepare data
    top_k = top_k_gdf.reset_index(drop=True).copy()
    top_k["uid"] = top_k.index.astype(str)
    top_k = top_k.to_crs(epsg=4326)  # Mapbox requires WGS84
    top_k = top_k.rename(columns={"bldg_id": "ID"})

    # Convert to GeoJSON
    top_k_geojson = json.loads(top_k.to_json())

    # Create figure
    fig = px.choropleth_mapbox(
        top_k,
        geojson=top_k_geojson,
        locations="uid",
        color=color_col,
        hover_data={"ID": True, color_col: True, "lat": True, "lon": True, "uid": False},
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        zoom=10,
        center={"lat": 41.8781, "lon": -87.6298},
        opacity=0.8,
        labels={color_col: "Estimated kWh"},
        featureidkey="properties.uid",
    )

    fig.update_layout(
        title=map_title,
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    return fig
