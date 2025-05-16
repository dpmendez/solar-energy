import geopandas as gpd

# Load the full GeoJSON file
full_gdf = gpd.read_file("data/solar_summary.geojson")

# Ensure CRS is in WGS84 for spatial filtering
full_gdf = full_gdf.to_crs("EPSG:4326")

# Define bounding box for the target area
# Semi central Chicago
min_lat = 41.87     
max_lat = 41.92     
min_lon = -87.67    
max_lon = -87.62

# Filter by bounding box using lat/lon columns
central_gdf = full_gdf[
    (full_gdf["lon"] >= min_lon) & (full_gdf["lon"] <= max_lon) &
    (full_gdf["lat"] >= min_lat) & (full_gdf["lat"] <= max_lat)
]

# Simplify geometries to reduce size
central_gdf.loc[:, "geometry"] = central_gdf["geometry"].simplify(tolerance=0.01, preserve_topology=True)

# Drop unneeded columns to reduce memory footprint (keeping only key ones)
columns_to_keep = columns_to_keep = ["ghi_sum", "lon", "lat", "bldg_id", "orientation", "kwh_estimate", "geometry"]
central_gdf = central_gdf[columns_to_keep]

# Save to smaller GeoJSON file
output_path = "data/central_chicago_solar_summary.geojson"
central_gdf.to_file(output_path, driver="GeoJSON")

# Report the new file path and number of features
output_path, len(central_gdf)
