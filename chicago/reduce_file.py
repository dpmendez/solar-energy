import geopandas as gpd

# Load the full GeoJSON file
full_gdf = gpd.read_file("solar_summary.geojson")

# Ensure CRS is in WGS84 for spatial filtering
full_gdf = full_gdf.to_crs("EPSG:4326")

# Define bounding box for the target area
min_lat = 41.82     # Bridgeport
max_lat = 41.97     # Ravenswood
min_lon = -87.72    # Avondale
max_lon = -87.60    # Lakefront

# Filter by bounding box using lat/lon columns
central_gdf = full_gdf[
    (full_gdf["lon"] >= min_lon) & (full_gdf["lon"] <= max_lon) &
    (full_gdf["lat"] >= min_lat) & (full_gdf["lat"] <= max_lat)
]

# Simplify geometries to reduce size
central_gdf.loc[:, "geometry"] = central_gdf["geometry"].simplify(tolerance=0.0001, preserve_topology=True)
#central_gdf["geometry"] = central_gdf.geometry.simplify(tolerance=0.0005, preserve_topology=True)

# Drop unneeded columns to reduce memory footprint (keeping only key ones)
columns_to_keep = [col for col in central_gdf.columns if col.startswith(("GHI", "DNI", "DHI"))] + ["lon", "lat", "BLDG_ID", "geometry"]
central_gdf = central_gdf[columns_to_keep]

# Save to smaller GeoJSON file
output_path = "central_chicago_solar_summary.geojson"
central_gdf.to_file(output_path, driver="GeoJSON")

# Report the new file path and number of features
output_path, len(central_gdf)
