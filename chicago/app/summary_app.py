import geopandas as gpd
import json
import os
import requests
import plotly.express as px
import dash
from dash import dcc, html, dash_table, Input, Output
from app.viz import plot_top_k_mapbox


### Get the data
gdf_avg = gpd.read_file("data/central_chicago_solar_summary.geojson")
gdf_avg = gdf_avg.reset_index(drop=True)    # Reset index to ensure it's clean
gdf_avg["uid"] = gdf_avg.index.astype(str)  # Explicitly store it for use in `locations`
gdf_avg = gdf_avg.to_crs(epsg=4326)         # Plotly and Dash require lat lon in (WGS84) format

geojson_data = gdf_avg.set_index("uid").geometry.__geo_interface__

top_k = gpd.read_file("data/top_100_buildings.geojson")

# Define table elements
table_df = top_k.copy()
table_df.rename(columns={
    "bldg_id": "ID",
    "lat" : "Lat",
    "lon" : "Lon",
    "kwh_estimate": "Estimated kWh",
    "orientation": "Orientation"
}, inplace=True)

table_df = table_df[["ID", "Lat", "Lon", "Estimated kWh", "Orientation"]]

dash_table.DataTable(
    id='top-k-table',
    columns=[{"name": i, "id": i} for i in table_df.columns],
    data=table_df.to_dict('records'),
    style_table={'overflowX': 'auto', 'height': '400px'},
    style_cell={'textAlign': 'left', 'padding': '5px'},
    style_header={'fontWeight': 'bold', 'backgroundColor': '#f0f0f0'},
)


### The app
app = dash.Dash(__name__)
server = app.server  # Needed for Render

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

    html.Div([
    html.H2("Top 100 Buildings by Estimated Energy Output"),
    
    html.Div([
        dcc.Graph(
            id="top-k-map",
            figure=plot_top_k_mapbox(top_k)
        )
    ], style={'width': '65%', 'display': 'inline-block', 'verticalAlign': 'top'}),

    html.Div([
        dash_table.DataTable(
            id='top-k-table',
            columns=[{"name": i, "id": i} for i in table_df.columns],
            data=table_df.to_dict('records'),
            style_table={'overflowY': 'auto', 'height': '600px'},
            style_cell={'textAlign': 'left', 'padding': '5px'},
            style_header={'fontWeight': 'bold', 'backgroundColor': '#f0f0f0'},
        )
    ], style={'width': '34%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '1%'}),
])

])

@app.callback(
    Output("solar-map", "figure"),
    Input("metric", "value"),
    Input("roof-orientation", "value")
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

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080) # dash uses this port on render