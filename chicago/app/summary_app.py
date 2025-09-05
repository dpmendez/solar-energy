import geopandas as gpd
import json
import os
import requests
import plotly.express as px
import dash
from dash import dcc, html, dash_table, Input, Output
from viz import plot_top_k_mapbox


### Get the data
gdf_avg = gpd.read_file("../data/central_chicago_solar_summary.geojson")
gdf_avg = gdf_avg.reset_index(drop=True)    # Reset index to ensure it's clean
gdf_avg["uid"] = gdf_avg.index.astype(str)  # Explicitly store it for use in `locations`
gdf_avg = gdf_avg.to_crs(epsg=4326)         # Plotly and Dash require lat lon in (WGS84) format

geojson_data = gdf_avg.set_index("uid").geometry.__geo_interface__

top_k = gpd.read_file("../data/top_100_buildings.geojson")
table_df = top_k.drop(columns="geometry", errors="ignore").copy()

# Define hover data and labels for the map
hover_data={
    "bldg_id": True,
    "kwh_estimate": True,
    "co2_avoided_t": True,
    "capex_usd": True,
    "simple_payback_years": True,
    "lon": False, "lat": False, "uid": False
}

labels = {
    "bldg_id": "Building ID",
    "kwh_estimate": "Estimated kWh/year",
    "co2_avoided_t": "Avoided CO2 t/year",
    "capex_usd": "Investment (USD)",
    "simple_payback_years": "Payback (years)",
    "ghi_sum": "Annual GHI (kWh/m²)"
}


### The app
app = dash.Dash(__name__)
server = app.server  # Needed for Render

# Dropdown variable choices
metric_options = [
    {"label": "Global Horizontal Irradiance", "value": "ghi_sum"},
    {"label": "Estimated Energy Output", "value": "kwh_estimate"},
    {"label": "Estimated Avoided CO2", "value": "co2_avoided_t"}
    ]
pretty_labels={ 
    "ghi_sum": "Annual GHI (kWh/m²)",
    "kwh_estimate": "Energy Output (kWh/year)",
    "co2_avoided_t": "Avoided CO2 (t/year)"
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
            columns=[
                {"name": "ID", "id": "bldg_id"},
                {"name": "Estimated kWh/year", "id": "kwh_estimate", 
                 "type": "numeric", 
                 "format": Format(group=Group.yes, precision=0, scheme=Scheme.fixed)},
                {"name": "Avoided CO2 t/year", "id": "co2_avoided_t", 
                 "type": "numeric", 
                 "format": Format(group=Group.yes, precision=1, scheme=Scheme.fixed)},
                {"name": "Investment (USD)", "id": "capex_usd", 
                 "type": "numeric", 
                 "format": Format(group=Group.yes, precision=0, scheme=Scheme.fixed)},
                {"name": "Payback (years)", "id": "simple_payback_years", 
                 "type": "numeric", 
                 "format": Format(precision=1, scheme=Scheme.fixed)},
                {"name": "Lat", "id": "lat"},
                {"name": "Lon", "id": "lon"},
                {"name": "Orientation", "id": "orientation"},
            ],
            data=table_df.to_dict("records"),
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

    # # Rename column for cleaner hover label
    # filtered_gdf = filtered_gdf.rename(columns={
    #      "bldg_id": "Building ID"})

    fig = px.choropleth_mapbox(
        filtered_gdf,
        geojson=geojson_data,
        locations="uid",
        color=metric,
        hover_data=hover_data,
        # hover_data={
        #     "bldg_id": True,
        #     "kwh_estimate": True,
        #     "co2_avoided_t": True,
        #     "capex_usd": True,
        #     "simple_payback_years": True,
        #     "lon": False, "lat": False, "uid": False
        # },
        color_continuous_scale="YlOrRd",
        mapbox_style="carto-positron",
        zoom=12,
        center={"lat": 41.8781, "lon": -87.6298},
        opacity=0.7,
        labels=labels
    )

    fig.update_traces(
    hovertemplate=
    "<b>Building ID:</b> %{customdata[0]}<br>" +
    "<b>Estimated kWh/year:</b> %{customdata[1]:,.0f}<br>" +
    "<b>Avoided CO2 t/year:</b> %{customdata[2]:,.1f}<br>" +
    "<b>Investment (USD):</b> $%{customdata[3]:,.0f}<br>" +
    "<b>Payback (years):</b> %{customdata[4]:,.1f}<extra></extra>"
    )

    fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
    return fig

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080) # dash uses this port on render