SYSTEM_EFFICIENCY = 0.18 # 18% panel + system efficiency
DERATING_FACTOR = 0.77   # Account for system losses (inverters, wiring, etc.)
USABLE_AREA = 0.75       # Assume 75% of rooftop is usable

from shapely.geometry import LineString
import numpy as np


def get_orientation(geom): 
    """Compute orientation (azimuth) from geometry
    1 Extract the longest edge of the polygon (assuming it's aligned with the roof ridge).
    2. Compute the angle of that line."""

    if geom.geom_type != "Polygon":
        return np.nan

    coords = list(geom.exterior.coords) # get list of the polygon vertices
    max_len = 0
    angle = np.nan

    for i in range(len(coords) - 1): 
        p1, p2 = coords[i], coords[i + 1]
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        length = np.hypot(dx, dy)

        if length > max_len:
            max_len = length
            angle = (np.degrees(np.arctan2(dy, dx)) + 360) % 360 # ensure angle is always positive

    return angle


def azimuth_to_orientation(angle):
    """Convert azimuth angle (0–360°) into a cardinal/intercardinal orientation label."""
    
    # Define boundaries for compass sectors
    directions = [
        ("North",        337.5, 360.0),
        ("North",          0.0, 22.5),
        ("Northeast",     22.5, 67.5),
        ("East",          67.5, 112.5),
        ("Southeast",    112.5, 157.5),
        ("South",        157.5, 202.5),
        ("Southwest",    202.5, 247.5),
        ("West",         247.5, 292.5),
        ("Northwest",    292.5, 337.5)
    ]
    
    for label, start, end in directions:
        if start <= angle < end or (start > end and (angle >= start or angle < end)):
            return label
    return "Unknown"


def get_kwh(ghi, area):
    """
    Estimate annual energy output (kWh) from solar irradiance and roof area.
    
    Parameters:
        ghi (float): Global Horizontal Irradiance in Wh/m²/year
        area (float): Roof area in m²
    
    Returns:
        float: Estimated energy output in kWh/year
    """
    if ghi is None or area is None or ghi <= 0 or area <= 0:
        return 0
    return ghi * (area * USABLE_AREA) * SYSTEM_EFFICIENCY * DERATING_FACTOR / 1000
