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


def scatter_tradeoff(df, top_n=100, size_by="co2_avoided_t"):
    # Select top groups
    top_energy = df.nlargest(top_n, "kwh_estimate")
    top_investment = df.nsmallest(top_n, "capex_usd")

    # Mark category
    df = df.copy()  # avoid modifying original
    df["category"] = "Other"
    df.loc[top_energy.index, "category"] = "Top kWh"
    df.loc[top_investment.index, "category"] = "Top Investment"

    # Scatter plot
    fig = px.scatter(
        df,
        x="capex_usd",
        y="simple_payback_years",
        size=size_by,  # "co2_avoided_t" or "kwh_estimate"
        color="category",
        hover_data=["bldg_id", "kwh_estimate", "co2_avoided_t"],
        labels={
            "capex_usd": "Investment (USD)",
            "simple_payback_years": "Payback (years)",
            "kwh_estimate": "Estimated kWh/year",
            "co2_avoided_t": "Avoided CO₂ (t/year)",
            "category": "Ranking Group"
        },
        title=f"Tradeoff: Investment vs. Payback (bubble = {size_by})"
    )

    fig.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color="DarkSlateGrey")))


def scatter_tradeoff_top_bottom(df, top_n=100, size_metric="kwh_estimate"):
    """
    Generates two scatter plots: top N and bottom N buildings by kWh.
    
    Args:
        df: GeoDataFrame or DataFrame with columns: 'bldg_id', 'capex_usd', 'simple_payback_years', 'kwh_estimate', 'co2_avoided_t'
        top_n: number of buildings for top/bottom plots
        size_metric: metric to use for bubble size ('kwh_estimate' or 'co2_avoided_t')
    
    Returns:
        fig_top: Plotly Figure for top N buildings
        fig_bottom: Plotly Figure for bottom N buildings
    """
    # Sort by energy output
    df_sorted = df.sort_values("kwh_estimate", ascending=False)

    # Top N
    df_top = df_sorted.head(top_n).copy()
    df_top["category"] = "Top 100"

    # Bottom N
    df_bottom = df_sorted.tail(top_n).copy()
    df_bottom["category"] = "Bottom 100"

    # Common hover info
    hover_cols = ["bldg_id", "capex_usd", "simple_payback_years", "kwh_estimate", "co2_avoided_t"]

    # Top plot
    fig_top = px.scatter(
        df_top,
        x="capex_usd",
        y="simple_payback_years",
        size=size_metric,
        color="category",
        hover_data=hover_cols,
        labels={
            "capex_usd": "Investment (USD)",
            "simple_payback_years": "Payback (years)",
            "kwh_estimate": "Energy Output (kWh/year)",
            "co2_avoided_t": "Avoided CO₂ (t/year)",
            "category": "Ranking"
        },
        title=f"Top {top_n} Buildings by Energy Output"
    )
    fig_top.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))
    fig_top.update_layout(legend_title_text="Category")

    # Bottom plot
    fig_bottom = px.scatter(
        df_bottom,
        x="capex_usd",
        y="simple_payback_years",
        size=size_metric,
        color="category",
        hover_data=hover_cols,
        labels={
            "capex_usd": "Investment (USD)",
            "simple_payback_years": "Payback (years)",
            "kwh_estimate": "Energy Output (kWh/year)",
            "co2_avoided_t": "Avoided CO₂ (t/year)",
            "category": "Ranking"
        },
        title=f"Bottom {top_n} Buildings by Energy Output"
    )
    fig_bottom.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))
    fig_bottom.update_layout(legend_title_text="Category")

    return fig_top, fig_bottom


def grouped_bars(df, top_n=10, by="kwh_estimate"):
    # Select top N by chosen ranking
    top_df = df.nlargest(top_n, by)

    # Melt for grouped bars
    plot_df = top_df.melt(
        id_vars=["bldg_id"],
        value_vars=["kwh_estimate", "capex_usd", "simple_payback_years"],
        var_name="Metric",
        value_name="Value"
    )

    fig = px.bar(
        plot_df,
        x="bldg_id",
        y="Value",
        color="Metric",
        barmode="group",
        labels={
            "bldg_id": "Building ID",
            "Value": "Value",
            "Metric": "Metric"
        },
        title=f"Top {top_n} Buildings by {by}"
    )

    return fig

