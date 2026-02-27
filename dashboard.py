"""
CityFlow AI - Streamlit Dashboard
AI-Powered Congestion Prediction & Route Optimization.
"""

from datetime import datetime

import folium
import pandas as pd
import polyline
import streamlit as st
from streamlit_folium import st_folium

from services.traffic_service import TrafficService
from services.congestion_engine import CongestionEngine
from services.simulation_engine import SimulationEngine
from ml.predictor import CongestionPredictor


CO2_PER_KM = 0.21
ICON_BASE = "https://unpkg.com/feather-icons/dist/icons"


def _icon_html(name: str, size: int = 16) -> str:
	return (
		f"<img src='{ICON_BASE}/{name}.svg' width='{size}' height='{size}' "
		"style='vertical-align: -3px; margin-right: 6px;'/>"
	)


def _congestion_badge(level: str) -> str:
	if level == "HIGH":
		return f"{_icon_html('alert-octagon')}HIGH"
	if level == "MEDIUM":
		return f"{_icon_html('alert-triangle')}MEDIUM"
	return f"{_icon_html('check-circle')}LOW"


def _calculate_environmental_metrics(routes: list, best_index: int) -> dict:
	best = routes[best_index]
	worst = max(routes, key=lambda r: r["congestion_index"])

	time_saved = max(0.0, round(worst["duration_min"] - best["duration_min"], 2))
	co2_saved = max(0.0, round((worst["distance_km"] - best["distance_km"]) * CO2_PER_KM, 2))
	efficiency = 0.0
	if worst["duration_min"] > 0:
		efficiency = round((time_saved / worst["duration_min"]) * 100, 2)

	return {
		"time_saved": time_saved,
		"co2_saved": co2_saved,
		"efficiency_percentage": efficiency,
	}


def _build_map(origin_coords, dest_coords, routes: list, best_index: int) -> folium.Map:
	base_map = folium.Map(location=origin_coords, zoom_start=13, control_scale=True)

	for idx, route in enumerate(routes):
		if not route.get("geometry"):
			continue
		color = "green" if idx == best_index else "gray"
		weight = 6 if idx == best_index else 3
		points = polyline.decode(route["geometry"])
		folium.PolyLine(points, color=color, weight=weight, opacity=0.8).add_to(base_map)

	folium.Marker(origin_coords, tooltip="Origin", icon=folium.Icon(color="blue")).add_to(base_map)
	folium.Marker(dest_coords, tooltip="Destination", icon=folium.Icon(color="red")).add_to(base_map)

	return base_map


def _simulate_intervention(route_data: dict, scenario: str, hour: int = None) -> dict:
	"""
	Simulate an intervention on route data.
	
	Args:
		route_data: Route data with congestion metrics
		scenario: Intervention scenario
		hour: Current hour for peak hour detection
		
	Returns:
		Simulation result
	"""
	zone_data = {
		"zone_name": "Current Route",
		"distance_km": route_data["distance_km"],
		"actual_duration_min": route_data["duration_min"],
		"expected_duration_min": route_data["expected_duration_min"],
		"congestion_index": route_data["congestion_index"],
		"congestion_level": route_data["congestion_level"],
		"risk_score": 0.0  # Placeholder
	}
	
	engine = SimulationEngine()
	return engine.simulate(zone_data, scenario, hour)


def main() -> None:
    st.set_page_config(page_title="CityFlow AI", layout="wide")

    st.title("CityFlow AI")
    st.subheader("AI-Powered Congestion Prediction & Route Optimization")

    st.divider()

    # Initialize session state
    if "results" not in st.session_state:
        st.session_state.results = None

    st.markdown("### Input Section")
    col1, col2, col3 = st.columns([3, 3, 1])
    with col1:
        origin = st.text_input("Origin", value="MG Road, Bangalore")
    with col2:
        destination = st.text_input("Destination", value="Koramangala, Bangalore")
    with col3:
        analyze_clicked = st.button("Analyze", type="primary")

    if not analyze_clicked and st.session_state.results is None:
        st.stop()

    if not origin.strip() or not destination.strip():
        st.error("Please provide both origin and destination.")
        st.stop()

    # Only run analysis if button clicked
    if analyze_clicked:
        try:
            with st.spinner("Analyzing routes and congestion..."):
                traffic_service = TrafficService()
                congestion_engine = CongestionEngine()
                predictor = CongestionPredictor()

                route_data = traffic_service.get_routes(origin, destination)
                analysis = congestion_engine.analyze_routes(route_data)

                best_index = analysis["best_route_index"]
                routes = analysis["routes"]

                now = datetime.now()
                forecast = predictor.predict(
                    now.hour,
                    now.weekday(),
                    routes[best_index]["congestion_index"],
                    routes[best_index]["distance_km"],
                )

                metrics = _calculate_environmental_metrics(routes, best_index)

                origin_coords = traffic_service.geocode_address(origin)
                dest_coords = traffic_service.geocode_address(destination)

                route_map = _build_map(origin_coords, dest_coords, routes, best_index)

                # Store results in session state
                st.session_state.results = {
                    "best_index": best_index,
                    "routes": routes,
                    "forecast": forecast,
                    "metrics": metrics,
                    "route_map": route_map,
                }

        except Exception as exc:
            st.error(f"Failed to analyze routes: {exc}")
            st.stop()

    # Display results from session state
    if st.session_state.results is None:
        st.stop()

    results = st.session_state.results
    best_index = results["best_index"]
    routes = results["routes"]
    forecast = results["forecast"]
    metrics = results["metrics"]
    route_map = results["route_map"]

    st.divider()

    st.markdown("### Recommended Route")
    best = routes[best_index]
    with st.success("Best route selected based on lowest congestion index"):
        st.write(f"Distance: {best['distance_km']} km")
        st.write(f"Actual Duration: {best['duration_min']} min")
        st.write(f"Expected Duration: {best['expected_duration_min']} min")
        st.write(f"Congestion Index: {best['congestion_index']}")
        st.markdown(
            f"Congestion Level: {_congestion_badge(best['congestion_level'])}",
            unsafe_allow_html=True,
        )
        st.write(f"Efficiency Ratio: {best['congestion_index']}x")

    st.divider()

    st.markdown("### Alternative Routes")
    table_rows = []
    for idx, route in enumerate(routes, start=1):
        table_rows.append({
            "Route": idx,
            "Distance (km)": route["distance_km"],
            "Duration (min)": route["duration_min"],
            "Congestion Level": route["congestion_level"],
            "Congestion Index": route["congestion_index"],
        })
    st.dataframe(pd.DataFrame(table_rows), width="stretch")

    st.divider()

    st.markdown("### 30-Minute Forecast")
    level = forecast["future_congestion_level"]
    with st.container():
        st.markdown(
            f"Future Congestion Level: {_congestion_badge(level)}",
            unsafe_allow_html=True,
        )
        st.write(f"Confidence: {forecast['confidence'] * 100:.0f}%")

    st.divider()

    st.markdown("### Environmental Impact")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Time Saved (min)", metrics["time_saved"])
    col_b.metric("CO2 Saved (kg)", metrics["co2_saved"])
    col_c.metric("Efficiency Improvement (%)", metrics["efficiency_percentage"])

    st.divider()

    st.markdown("### Map Visualization")
    st_folium(route_map, width=1200, height=500, key="route_map", returned_objects=[])

    st.divider()

    st.markdown(
        f"### {_icon_html('bar-chart-2', 18)}Policy Impact Simulator",
        unsafe_allow_html=True,
    )
    st.markdown("Simulate traffic interventions and analyze their impact on congestion metrics.")

    scenario_display_map = {
        "None (Current State)": "none",
        "Widen Road (+15% capacity)": "widen_road",
        "Optimize Signals (+10% efficiency)": "optimize_signals",
        "Road Under Repair (-20% capacity)": "road_under_repair",
        "Heavy Vehicle Restriction (Peak Hours)": "heavy_vehicle_restriction"
    }

    selected_scenario_display = st.selectbox(
        "Select Intervention Scenario",
        list(scenario_display_map.keys()),
        key="scenario_selector"
    )

    selected_scenario_key = scenario_display_map[selected_scenario_display]

    try:
        now = datetime.now()
        simulation_result = _simulate_intervention(
            routes[best_index],
            selected_scenario_key,
            hour=now.hour
        )

        # Display before/after comparison
        col_before, col_after = st.columns(2)

        with col_before:
            st.markdown("**Current State**")
            st.metric("Congestion Index", simulation_result["before"]["ci"])
            st.metric("Congestion Level", simulation_result["before"]["level"])
            st.metric("Risk Score", simulation_result["before"]["risk_score"])

        with col_after:
            st.markdown("**After Intervention**")
            st.metric("Congestion Index", simulation_result["after"]["ci"])
            st.metric("Congestion Level", simulation_result["after"]["level"])
            st.metric("Risk Score", simulation_result["after"]["risk_score"])

        # Show improvement indicator
        st.divider()
        improvement_pct = simulation_result["improvement_percent"]

        if selected_scenario_key != "none":
            if improvement_pct > 0:
                st.success(f"✅ Projected Improvement: **{improvement_pct:.2f}%**")
            elif improvement_pct < 0:
                st.error(f"⚠️  Projected Deterioration: **{abs(improvement_pct):.2f}%**")
            else:
                st.info("➡️  No significant impact projected")

    except Exception as exc:
        st.error(f"Simulation failed: {exc}")

    st.divider()
    st.caption("Built for Smart City Congestion Hackathon | CityFlow AI")


if __name__ == "__main__":
    main()
