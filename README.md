# 🌞 Rooftop Solar Potential Dashboard

This interactive dashboard visualizes the annual rooftop solar potential of buildings using Global Horizontal Irradiance (GHI) and other solar radiation metrics. Built with Dash and Plotly, it provides a map-based tool to help stakeholders identify high-potential rooftops for solar energy deployment.

👉 Live Demo: https://solar-energy-k3vj.onrender.com/

⚠️ Note: The live app currently displays a limited area of Chicago, but the underlying analysis covers the full city.

## 📌 Project Goals

* Visualize building-level solar irradiance data across urban areas.
* Support local governments and urban planners in making data-driven decisions on where to incentivize solar infrastructure.
* Empower environmental NGOs and solar providers to prioritize rooftops with the highest potential.
* Scale the approach to other cities and regions with minimal configuration changes.

## 🖥️ Features

* Dynamic map of buildings colored by selected solar metric (GHI, DNI, or DHI).
* Hover tooltips showing building-specific information.
* Orientation filter for targeting south-, east-, west-, or flat-facing roofs.
* Clean, responsive web app layout.
* Designed for easy expansion to additional cities.

## 📂 Data

Input data is a GeoDataFrame with:

* Building footprints: [City of Chicago data](https://data.cityofchicago.org)
updated November 13th 2024 
* Annual solar radiation values (GHI, DNI, DHI): [National Solar Radiation Database](https://nsrdb.nrel.gov/data-viewer) for 2023, 2km resolution, 60 minutes interval.
* Additional features like estimated energy output, building ID, and roof orientation.

Note: Data covers the entire city of Chicago, even if the frontend currently displays a subset.

## 🔧 Planned Improvements

- [ ] Add range slider to filter buildings by solar potential (e.g., GHI or kWh).
- [ ] Incorporate daily and hourly solar radiation visualizations.
- [ ] Enable exportable reports of top-performing rooftops for solar targeting.
- [ ] Add clear outlines for recommended buildings.
- [ ] Expand to other cities using the same analysis pipeline.
- [ ] Integrate climate equity, grid proximity, and policy constraints.
- [ ] Provide actionable summaries for government decision-making and urban energy planning.
