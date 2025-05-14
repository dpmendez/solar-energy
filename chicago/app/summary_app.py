import geopandas as gpd
import json
import os
import requests

# change dl=0 with dl=1 for direct download
DROPBOX_URL = "https://www.dropbox.com/scl/fi/nrohv5gfcckeiy8phool4/solar_summary.geojson?rlkey=5w6d7mnoz61a8ssvemea9rx32&st=dyn9zsan&dl=1"
LOCAL_PATH = "../data/solar_summary.geojson"

# Ensure directory exists
os.makedirs("../data", exist_ok=True)

# Download only if it doesn't exist
if not os.path.exists(LOCAL_PATH):
    print("Downloading GeoJSON from Dropbox...")
    r = requests.get(DROPBOX_URL)
    with open(LOCAL_PATH, "wb") as f:
        f.write(r.content)
    print("Download complete.")


gdf_avg = gpd.read_file("../data/solar_summary.geojson")

gdf_avg = gdf_avg.reset_index(drop=True)         # Reset index to ensure it's clean
gdf_avg.index = gdf_avg.index.astype(str)        # Convert index to string
gdf_avg["uid"] = gdf_avg.index                   # Explicitly store it for use in `locations`

# Plotly and Dash require latitude/longitude in (WGS84) format — that's EPSG:4326
# Convert only if needed
gdf_avg = gdf_avg.to_crs("EPSG:4326")

geojson_data = gdf_avg.set_index("uid").geometry.__geo_interface__


# --------------------------
# --------------------------
# --------------------------

import plotly.express as px
import dash
from dash import dcc, html, Input, Output

app = dash.Dash(__name__)
server = app.server  # Needed for Render

# Dropdown variable choices
solar_options = [
    {"label": "Global Horizontal Irradiance (GHI)", "value": "GHI"},
    {"label": "Direct Normal Irradiance (DNI)", "value": "DNI"},
    {"label": "Diffuse Horizontal Irradiance (DHI)", "value": "DHI"}
]

app.layout = html.Div([
    html.H2("Solar Radiation Map by Building"),
    
    html.Div([
        html.Label("Solar Metric"),
        dcc.Dropdown(
            id="solar-variable",
            options=solar_options,
            value="GHI"
        ),
    ], style={"width": "48%", "display": "inline-block"}),

    html.Div([
        html.Label("Aggregation"),
        dcc.Dropdown(
            id="agg-type",
            options=[{"label": "Average", "value": "mean"}, {"label": "Sum", "value": "sum"}],
            value="mean"
        ),
    ], style={"width": "48%", "display": "inline-block"}),

    dcc.Graph(id="solar-map")
])

@app.callback(
    Output("solar-map", "figure"),
    Input("solar-variable", "value"),
    Input("agg-type", "value")
)
def update_map(var, agg):
    column_name = f"{var}_{agg}"  # e.g. GHI_mean or GHI_sum
    print(f"Rendering: {column_name}")
    
    fig = px.choropleth_mapbox(
        gdf_avg,
        geojson=geojson_data,
        locations="uid",
        color=column_name,
        hover_data={"BLDG_ID": True, column_name: True, "lon":True, "lat": True, "uid": False},
        color_continuous_scale="YlOrRd",
        mapbox_style="carto-positron",
        zoom=12,
        center={"lat": 41.8781, "lon": -87.6298},  # Chicago
        opacity=0.7,
        labels={column_name: f"{var.upper()} ({agg})"}
    )
    fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
    return fig

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080) # dash uses this port on render