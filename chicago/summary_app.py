import geopandas as gpd
import json

gdf_avg = gpd.read_file("data/central_chicago_solar_summary.geojson")

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

# Dropdown variable choices
metric_options = [
    {"label": "Global Horizontal Irradiance (GHI)", "value": "ghi_sum"},
    {"label": "Estimated Energy Output (kWh)", "value": "kwh_estimate"},
]
pretty_labels={ 
    "ghi_sum": "Annual GHI (kWh/m²)",
    "kwh_estimate": "Estimated Annual Energy (kWh)"
}

app.layout = html.Div([
    html.H2("Solar Radiation Map by Building"),
    
    html.Div([
        html.Label("Solar Metric"),
        dcc.Dropdown(
            id="metric",
            options=metric_options,
            value="ghi_sum"
        ),
    ], style={"width": "48%", "display": "inline-block"}),

    html.Div([
        html.Label("Orientation"),
        dcc.Dropdown(
            id="roof-orientation",
            options=[{"label": "All", "value": "all"}] + [
                {"label": o.title(), "value": o} for o in sorted(gdf_avg["orientation"].dropna().unique())
            ],
            value="all"
        ),
    ], style={"width": "48%", "display": "inline-block"}),

    dcc.Graph(id="solar-map"),
])

@app.callback(
    Output("solar-map", "figure"),
    Input("metric", "value"),
    Input("roof-orientation", "value"),
    Input("value-range", "value")
)
def update_map(metric, orientation):
    # Filter data by orientation
    if orientation == "all":
        filtered_gdf = gdf_avg.copy()
    else:
        filtered_gdf = gdf_avg[gdf_avg["orientation"] == orientation]

    # Rename column for cleaner hover label
    filtered_gdf = filtered_gdf.rename(columns={"bldg_id": "Building ID"})

    fig = px.choropleth_mapbox(
        filtered_gdf,
        geojson=geojson_data,
        locations="uid",
        color=metric,
        hover_data={"Building ID": True, "lon":True, "lat": True, "uid": False},
        color_continuous_scale="YlOrRd",
        mapbox_style="carto-positron",
        zoom=12,
        center={"lat": 41.8781, "lon": -87.6298},
        opacity=0.7,
        labels={metric: pretty_labels.get(metric, metric)}
    )
    fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
    return fig

app.run(debug=True,port=8050)