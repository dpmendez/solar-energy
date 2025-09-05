import geopandas as gpd
import json
import plotly.express as px
import dash
from dash import dcc, html, dash_table, Input, Output
from dash.dash_table.Format import Format, Group, Scheme
from app.viz import plot_top_k_mapbox

### Get the data
#gdf_avg = gpd.read_file("data/solar_summary.geojson")
gdf_avg = gpd.read_file("data/central_chicago_solar_summary.geojson")
gdf_avg = gdf_avg.reset_index(drop=True)    # Reset index to ensure it's clean
gdf_avg["uid"] = gdf_avg.index.astype(str)  # Explicitly store it for use in `locations`
gdf_avg = gdf_avg.to_crs(epsg=4326)         # Plotly and Dash require lat lon in (WGS84) format

geojson_data = gdf_avg.set_index("uid").geometry.__geo_interface__

# Default top 100 (highest energy output)
top_k_init = gdf_avg.nlargest(100, "kwh_estimate").copy()

# Thresholds
min_area = 20  # m2
min_kwh = 8000 # kWh/year

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

    # ----- Header section -----
    html.Div([
        html.H2("Chicago Rooftop Solar Potential"),
        html.P(
            "This interactive dashboard maps and quantifies rooftop solar potential across city buildings. "
            "You can explore solar radiation, estimated energy output, avoided CO₂ emissions, and financial metrics "
            "such as investment cost and payback period."
        ),
    ], style={
        "maxWidth": "900px",
        "margin": "20px auto",
        "padding": "15px",
        "backgroundColor": "#f9f9f9",
        "border": "1px solid #ddd",
        "borderRadius": "8px",
        "lineHeight": "1.6",
        "fontSize": "16px"
    }),

    # ----- Controls + Map -----
    html.H2("Solar Radiation Map"),
    
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

    # ----- Top 100 section -----
    html.Div([
        html.H2("Top 100 Buildings"),
        
        html.Div([
            html.Label("Ranking criterion"),
            dcc.Dropdown(
                id="ranking-criterion",
                options=[
                    {"label": "Highest Energy Output", "value": "energy"},
                    {"label": "Lowest Investment", "value": "investment"},
                    {"label": "Fastest Payback", "value": "payback"},
                ],
                value="energy"  # default
            )
        ], style={"width": "48%", "marginBottom": "20px"}),
       
        html.Div([
            dcc.Graph(
                id="top-k-map",
                figure=plot_top_k_mapbox(top_k_init)
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
                    {"name": "Investment (USD)", "id": "capex_usd", 
                     "type": "numeric", 
                     "format": Format(group=Group.yes, precision=0, scheme=Scheme.fixed)},
                    {"name": "Payback (years)", "id": "simple_payback_years", 
                     "type": "numeric", 
                     "format": Format(precision=1, scheme=Scheme.fixed)},
                    {"name": "Avoided CO2 t/year", "id": "co2_avoided_t", 
                     "type": "numeric", 
                     "format": Format(group=Group.yes, precision=1, scheme=Scheme.fixed)},
                    {"name": "Orientation", "id": "orientation"},
                    {"name": "Lat", "id": "lat"},
                    {"name": "Lon", "id": "lon"},
                ],
                data=[], # will be filled in callback
                style_table={'overflowY': 'auto', 'height': '600px'},
                style_cell={'textAlign': 'left', 'padding': '5px'},
                style_header={'fontWeight': 'bold', 'backgroundColor': '#f0f0f0', 'position': 'sticky', 'top': 0, 'zIndex': 1},
            )
        ], style={'width': '34%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '1%'}),
    ]),

    # ----- Footnote -----
    html.Div([
        html.P(
            "Note: Results exclude rooftops below a minimum area and very low annual solar output. "
            "This ensures rankings focus on buildings with meaningful potential."
        )
    ], style={
        "maxWidth": "900px",
        "margin": "30px auto 10px auto",
        "padding": "10px",
        "fontSize": "14px",
        "color": "#555",
        "fontStyle": "italic",
        "textAlign": "center"
    })
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

    fig = px.choropleth_mapbox(
        filtered_gdf,
        geojson=geojson_data,
        locations="uid",
        color=metric,
        hover_data=hover_data,
        color_continuous_scale="YlOrRd",
        mapbox_style="carto-positron",
        zoom=12,
        center={"lat": 41.895, "lon": -87.645},
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

@app.callback(
    [Output("top-k-map", "figure"),
     Output("top-k-table", "data")],
    Input("ranking-criterion", "value")
)
def update_top_k(ranking):

    # Defensive filtering (skip NaNs, ensure numeric)
    df = gdf_avg.copy()
    df = df.dropna(subset=["surface_area", "kwh_estimate"])
    df = df[
        (df["surface_area"].astype(float) >= min_area) &
        (df["kwh_estimate"].astype(float) >= min_kwh)
    ]

    # Pick ranking
    if ranking == "energy":
        df_top = df.nlargest(100, "kwh_estimate")
        color_top = "kwh_estimate"
        title = "Energy (kWh/year)"
        ascending = False
    elif ranking == "investment":
        df_top = df.nsmallest(100, "capex_usd")
        color_top = "capex_usd"
        title = "Investment (USD)"
        ascending = True
    elif ranking == "payback":
        df_top = df.nsmallest(100, "simple_payback_years")
        color_top = "simple_payback_years"
        title = "Payback (years)"
        ascending = True

    # Prepare GeoDataFrame for the map (keep geometry, ensure CRS is WGS84)
    df_map = df_top.copy()
    if df_map.crs is None or df_map.crs.to_epsg() != 4326:
        try:
            df_map = df_map.to_crs(epsg=4326)
        except Exception:
            print("Warning: failed to convert df_map to EPSG:4326 — check CRS")

    # Table
    table_cols = ["bldg_id", "kwh_estimate", "capex_usd", "simple_payback_years", "co2_avoided_t",  "orientation", "lat", "lon"]
    present_cols = [c for c in table_cols if c in df_map.columns]
    df_table = df_map.drop(columns="geometry", errors="ignore").copy()
    df_table = df_table[present_cols].reset_index(drop=True)

    # Map
    fig = plot_top_k_mapbox(df_map, color_top, title)

    return fig, df_table.to_dict("records")


app.run(debug=True,port=8062)