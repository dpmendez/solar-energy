from shapely.geometry import LineString
import numpy as np

# Assumptions for energy estimation (physics)
system_efficiency  = 0.18 # 18% panel + system efficiency
derating_factor    = 0.77 # Account for system losses (inverters, wiring, etc.)
usable_roof_area   = 0.75 # Assume 75% of rooftop is usable
grid_ef_kg_per_kwh = 0.40  # kg CO2 per kWh (US grid average; use 0.90 for coal, 0.40 gas, ~0.05 nuclear)

# Assumptions for financial estimation (market)
pv_power_density_kw_per_m2 = 0.18  # kW per m²
installed_cost_per_kw      = 1800  # $/kW base capex per kW
scale_discount             = 0.08  # bigger systems get up to ~8% discount (tunable)
om_rate                    = 0.01  # annual O&M fraction of CapEx
tariff_usd_per_kwh         = 0.15  # $/kWh

rng = np.random.default_rng(42)  # for reproducible noise

# orientation multiplier
orientation_factor = {
    "South": 1.00,
    "Southeast": 0.98,
    "Southwest": 0.98,
    "East": 0.92,
    "West": 0.92,
    "Flat": 0.90,
    "Northeast": 0.85,
    "Northwest": 0.85,
    "North": 0.80
}


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


def get_kwh(df):

    if df["ghi_sum"] is None or df["surface_area"] is None or df["ghi_sum"] <= 0 or df["surface_area"] <= 0:
        df["raw_kwh_estimate"] = 0
        df["kwh_estimate"] = 0
    else:
        df["raw_kwh_estimate"] = df["ghi_sum"] * (df["surface_area"] * usable_roof_area) * system_efficiency * derating_factor / 1000
        df["orientation_cat"] = df["orientation"].fillna("Flat")
        df["orientation_factor"] = df["orientation_cat"].map(orientation_factor).fillna(0.95)
        df["kwh_estimate"] = df[raw_kwh_col] * df["orientation_factor"]

    return df


def get_co2_avoided(annual_kwh, grid_ef_kg_per_kwh=grid_ef_kg_per_kwh):
    """
    Estimate avoided CO2 emissions from annual solar energy generation.

    Parameters
    ----------
    annual_kwh : float
        Annual solar energy generation in kWh.
    grid_ef_kg_per_kwh : float, optional
        Grid emission factor in kgCO2 per kWh.

    Returns
    -------
    float
        Annual CO2 avoided in metric tons (tCO2/year).
    """
    if annual_kwh is None or annual_kwh <= 0:
        return 0
    return annual_kwh * grid_ef_kg_per_kwh / 1000  # convert kg → metric tons


def get_finance_computations(df, annual_kwh_col = "kwh_estimate", roof_area_col = "surface_area"):
    """
    Adds finance and climate metrics to a GeoDataFrame.
    
    Metrics added:
        - system_kw: PV system size in kW
        - capex_usd: capital expenditure
        - annual_savings_usd: savings per year
        - annual_om_usd: operations and maintenance (O&M) cost per year
        - simple_payback_years: years
        - simple_roi: annual return relative to the upfront cost (%/year)
    
    df: GeoDataFrame with at least 'annual_kw_col' and 'roof_area_col' columns.
    """

    df = df.copy()

    df["annual_kwh"] = df[annual_kwh_col]
    df["system_kw"] = df[roof_area_col] * usable_roof_area * pv_power_density_kw_per_m2
    
    # Financial metrics

    # size-dependent capex per kW (decreasing with size)
    # a simple smooth curve: cost = base * (1 - discount * log(1 + system_kw))
    df["capex_per_kw_adj"] = installed_cost_per_kw * (1 - scale_discount * np.log1p(df["system_kw"]))
    df["capex_per_kw_adj"] = df["capex_per_kw_adj"].clip(lower=800)  # floor
    # apply a small random installation complexity premium/discount (±5%)
    df["capex_per_kw_adj"] *= (1 + rng.normal(0, 0.05, size=len(df)))
    # compute capex_usd
    df["capex_usd"] = df["system_kw"] * df["capex_per_kw_adj"]

    df["annual_savings_usd"] = df["annual_kwh"] * tariff_usd_per_kwh
    df["annual_om_usd"] = df["capex_usd"] * om_rate
    
    df["simple_payback_years"] = df["capex_usd"] / (df["annual_savings_usd"] - df["annual_om_usd"])
    df["simple_roi"] = (df["annual_savings_usd"] - df["annual_om_usd"]) / df["capex_usd"]

    return df