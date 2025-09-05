import plotly.express as px
import json


# Define hover data and labels for the map
hover_data={
    "ID": True,
    "kwh_estimate": True,
    "co2_avoided_t": True,
    "capex_usd": True,
    "simple_payback_years": True,
    "lon": False, "lat": False, "uid": False
}

labels = {
    "ID": "Building ID",
    "kwh_estimate": "Estimated kWh/year",
    "co2_avoided_t": "Avoided CO2 t/year",
    "capex_usd": "Investment (USD)",
    "simple_payback_years": "Payback (years)",
    "ghi_sum": "Annual GHI (kWh/m²)"
}

def plot_top_k_mapbox(top_k_gdf, color_col="kwh_estimate", map_title="kWh/year"):
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
        hover_data=hover_data,
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        zoom=10,
        center={"lat": 41.8781, "lon": -87.6298},
        opacity=0.8,
        labels={color_col: map_title},
        featureidkey="properties.uid",
    )

    fig.update_traces(
    hovertemplate=
    "<b>Building ID:</b> %{customdata[0]}<br>" +
    "<b>Estimated kWh/year:</b> %{customdata[1]:,.0f}<br>" +
    "<b>Avoided CO2 t/year:</b> %{customdata[2]:,.1f}<br>" +
    "<b>Investment (USD):</b> $%{customdata[3]:,.0f}<br>" +
    "<b>Payback (years):</b> %{customdata[4]:,.1f}<extra></extra>"
    )

    fig.update_layout(
        title="Top Buildings",
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    return fig
