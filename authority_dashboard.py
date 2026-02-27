"""
CityFlow AI - Authority Mode Dashboard
Traffic Intelligence & Command Control Center
"""

import asyncio
import json
import threading
from queue import Queue
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
import streamlit as st
from streamlit_folium import st_folium
import websockets
import requests

from services.congestion_engine import CongestionEngine
from services.simulation_engine import SimulationEngine
from ml.predictor import CongestionPredictor

ICON_BASE = "https://unpkg.com/feather-icons/dist/icons"

# Live Monitoring Configuration
API_BASE = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/live-monitor"


def _icon_html(name: str, size: int = 18) -> str:
    return (
        f"<img src='{ICON_BASE}/{name}.svg' width='{size}' height='{size}' "
        "style='vertical-align: -3px; margin-right: 6px;'/>"
    )


def _generate_mock_zones_data() -> list:
    """Generate mock zone data for demonstration."""
    zones = [
        {
            "zone_name": "MG Road",
            "distance_km": 5.0,
            "actual_duration_min": 12.0,
            "expected_duration_min": 8.5,
            "congestion_index": 1.41,
            "congestion_level": "MEDIUM",
            "risk_score": 6.2,
            "latitude": 12.9352,
            "longitude": 77.6245,
            "forecast_level": "MEDIUM"
        },
        {
            "zone_name": "Whitefield",
            "distance_km": 12.0,
            "actual_duration_min": 18.0,
            "expected_duration_min": 20.0,
            "congestion_index": 0.90,
            "congestion_level": "LOW",
            "risk_score": 2.6,
            "latitude": 12.9698,
            "longitude": 77.7499,
            "forecast_level": "LOW"
        },
        {
            "zone_name": "Koramangala",
            "distance_km": 3.5,
            "actual_duration_min": 14.0,
            "expected_duration_min": 6.0,
            "congestion_index": 2.33,
            "congestion_level": "HIGH",
            "risk_score": 11.3,
            "latitude": 12.9352,
            "longitude": 77.6245,
            "forecast_level": "HIGH"
        },
        {
            "zone_name": "Indiranagar",
            "distance_km": 4.0,
            "actual_duration_min": 9.0,
            "expected_duration_min": 8.0,
            "congestion_index": 1.12,
            "congestion_level": "LOW",
            "risk_score": 3.5,
            "latitude": 12.9716,
            "longitude": 77.6412,
            "forecast_level": "LOW"
        },
        {
            "zone_name": "Electronic City",
            "distance_km": 15.0,
            "actual_duration_min": 22.0,
            "expected_duration_min": 26.0,
            "congestion_index": 0.85,
            "congestion_level": "LOW",
            "risk_score": 2.4,
            "latitude": 12.8387,
            "longitude": 77.6873,
            "forecast_level": "LOW"
        },
        {
            "zone_name": "Silk Board",
            "distance_km": 8.0,
            "actual_duration_min": 20.0,
            "expected_duration_min": 13.7,
            "congestion_index": 1.46,
            "congestion_level": "MEDIUM",
            "risk_score": 6.8,
            "latitude": 12.9352,
            "longitude": 77.6245,
            "forecast_level": "MEDIUM"
        }
    ]
    return zones


def _create_city_gauge(city_ci: float) -> go.Figure:
    """Create city congestion index gauge chart."""
    fig = go.Figure(data=[go.Indicator(
        mode="gauge+number+delta",
        value=city_ci,
        title={"text": "City Congestion Index (CI)"},
        delta={"reference": 1.2},
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "axis": {"range": [0, 2]},
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [0, 1.2], "color": "rgba(0, 200, 0, 0.3)"},
                {"range": [1.2, 1.5], "color": "rgba(255, 165, 0, 0.3)"},
                {"range": [1.5, 2], "color": "rgba(255, 0, 0, 0.3)"}
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": 1.5
            }
        }
    )])
    
    fig.update_layout(height=400, font={"size": 14})
    return fig


def _create_zone_risk_bar(zones_data: list) -> go.Figure:
    """Create zone risk score bar chart."""
    df = pd.DataFrame([
        {"Zone": z["zone_name"], "Risk Score": z["risk_score"]}
        for z in zones_data
    ])
    
    def get_color(score):
        if score < 4:
            return "green"
        elif score < 7:
            return "orange"
        else:
            return "red"
    
    df["Color"] = df["Risk Score"].apply(get_color)
    
    fig = px.bar(df, x="Zone", y="Risk Score", 
                 color="Risk Score",
                 color_continuous_scale=["green", "orange", "red"],
                 range_color=[0, 10],
                 title="Zone Risk Assessment",
                 labels={"Risk Score": "Risk Score (0-10)"})
    
    fig.update_layout(showlegend=False, height=400)
    return fig


def _create_severity_pie(zones_data: list) -> go.Figure:
    """Create alert severity distribution pie chart."""
    severity_counts = {}
    for zone in zones_data:
        level = zone["congestion_level"]
        severity_counts[level] = severity_counts.get(level, 0) + 1
    
    colors = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}
    
    fig = px.pie(
        values=list(severity_counts.values()),
        names=list(severity_counts.keys()),
        title="City Alert Severity Distribution",
        color_discrete_map=colors
    )
    
    fig.update_layout(height=400)
    return fig


def _create_6hour_projection() -> go.Figure:
    """Create 6-hour congestion projection."""
    predictor = CongestionPredictor()
    now = datetime.now()
    
    hours = []
    levels = []
    level_names = []
    
    for i in range(7):
        current_hour = (now.hour + i) % 24
        hours.append(f"{current_hour:02d}:00")
        
        # Predict with mock data
        result = predictor.predict(
            current_hour, 
            now.weekday(), 
            1.2 + (i * 0.1),  # Mock increasing congestion
            5.0
        )
        
        level_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        level_numeric = level_map[result["future_congestion_level"]]
        levels.append(level_numeric)
        level_names.append(result["future_congestion_level"])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours, y=levels,
        mode='lines+markers',
        name='Congestion Level',
        line=dict(color='blue', width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        title="6-Hour Congestion Projection",
        xaxis_title="Time",
        yaxis_title="Level (1=Low, 2=Medium, 3=High)",
        yaxis=dict(range=[0.5, 3.5]),
        height=400,
        hovermode='x unified'
    )
    
    return fig


def _create_policy_impact_chart(before_ci: float, after_ci: float, 
                               before_risk: float, after_risk: float) -> go.Figure:
    """Create policy impact comparison chart."""
    fig = go.Figure(data=[
        go.Bar(name='Before', x=['Congestion Index', 'Risk Score'], 
               y=[before_ci, before_risk], marker_color='lightblue'),
        go.Bar(name='After', x=['Congestion Index', 'Risk Score'],
               y=[after_ci, after_risk], marker_color='lightgreen')
    ])
    
    fig.update_layout(
        title="Policy Intervention Impact Analysis",
        barmode='group',
        height=400,
        xaxis_title="Metric",
        yaxis_title="Value"
    )
    
    return fig


def _create_heatmap(zones_data: list) -> folium.Map:
    """Create advanced congestion heatmap with circle markers."""
    center_lat = np.mean([z["latitude"] for z in zones_data])
    center_lon = np.mean([z["longitude"] for z in zones_data])
    
    base_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        control_scale=True
    )
    
    color_map = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}
    
    for zone in zones_data:
        color = color_map.get(zone["congestion_level"], "blue")
        radius = zone["risk_score"] * 3
        
        popup_text = f"""
        <b>{zone['zone_name']}</b><br>
        CI: {zone['congestion_index']:.2f}<br>
        Risk Score: {zone['risk_score']:.1f}<br>
        Level: {zone['congestion_level']}<br>
        Forecast: {zone['forecast_level']}
        """
        
        folium.CircleMarker(
            location=[zone["latitude"], zone["longitude"]],
            radius=radius,
            popup=folium.Popup(popup_text, max_width=200),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=2
        ).add_to(base_map)
    
    return base_map


def _start_monitoring(origin: str, destination: str) -> bool:
    """Start monitoring via REST API."""
    try:
        # First check if monitoring is already active
        status_response = requests.get(f"{API_BASE}/status", timeout=5)
        status_response.raise_for_status()
        status = status_response.json()
        
        # If monitoring is already active, stop it first
        if status.get("is_monitoring", False):
            stop_response = requests.post(f"{API_BASE}/stop-monitoring", timeout=5)
            stop_response.raise_for_status()
            print("[INFO] Stopped existing monitoring session")
        
        # Now start new monitoring
        response = requests.post(
            f"{API_BASE}/start-monitoring",
            json={"origin": origin, "destination": destination},
            timeout=5
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to start monitoring: {e}")
        return False


def _stop_monitoring() -> bool:
    """Stop monitoring via REST API."""
    try:
        response = requests.post(f"{API_BASE}/stop-monitoring", timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to stop monitoring: {e}")
        return False


async def _ws_listener(data_queue: Queue):
    """WebSocket listener that runs in background thread."""
    try:
        async with websockets.connect(WS_URL) as websocket:
            data_queue.put({"type": "connected"})
            
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    # Put data in queue for main thread
                    data_queue.put(data)
                    
                except websockets.exceptions.ConnectionClosed:
                    data_queue.put({"type": "disconnected"})
                    break
                except Exception as e:
                    data_queue.put({"type": "error", "message": str(e)})
                    break
    
    except Exception as e:
        data_queue.put({"type": "error", "message": f"Connection failed: {e}"})


def _run_ws_listener(data_queue: Queue):
    """Run WebSocket listener in asyncio event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_ws_listener(data_queue))
    loop.close()


def _generate_ai_recommendations(zones_data: list, live_data: dict = None) -> dict:
    """Generate AI-powered traffic management recommendations based on current conditions."""
    recommendations = {
        "immediate": [],
        "short_term": [],
        "long_term": [],
        "insights": []
    }
    
    # Analyze zone data
    high_zones = [z for z in zones_data if z["congestion_level"] == "HIGH"]
    medium_zones = [z for z in zones_data if z["congestion_level"] == "MEDIUM"]
    avg_ci = np.mean([z["congestion_index"] for z in zones_data])
    
    # IMMEDIATE ACTIONS (Critical - within 1 hour)
    if high_zones:
        for zone in high_zones:
            recommendations["immediate"].append({
                "icon": "🚨",
                "priority": "CRITICAL",
                "title": f"Deploy Traffic Control at {zone['zone_name']}",
                "description": f"CI: {zone['congestion_index']:.2f} | Risk: {zone['risk_score']:.1f}/10",
                "action": "Deploy traffic police to manually control signal timing and manage flow",
                "impact": "High - Expected 15-25% reduction in congestion within 30 minutes"
            })
        
        recommendations["immediate"].append({
            "icon": "📢",
            "priority": "HIGH",
            "title": "Issue Public Advisory",
            "description": f"{len(high_zones)} zone(s) experiencing severe congestion",
            "action": "Broadcast traffic alerts via radio, social media, and mobile apps to divert traffic",
            "impact": "Medium - Reduce incoming traffic by 10-15%"
        })
    
    # Analyze live monitoring data if available
    if live_data and live_data.get("congestion_index", 0) >= 1.5:
        recommendations["immediate"].append({
            "icon": "🚦",
            "priority": "HIGH",
            "title": f"Optimize Signal Timing: {live_data.get('origin', '')} → {live_data.get('destination', '')}",
            "description": f"Live CI: {live_data.get('congestion_index', 0):.2f} | Duration: {live_data.get('duration_min', 0):.1f} min",
            "action": "Extend green signal duration on main corridor by 30% and reduce cross-traffic timing",
            "impact": "High - Estimated 20% improvement in flow rate"
        })
    
    # SHORT-TERM STRATEGIES (1-7 days)
    if medium_zones:
        recommendations["short_term"].append({
            "icon": "🔧",
            "title": "Signal Re-programming Initiative",
            "description": f"{len(medium_zones)} zones showing moderate congestion patterns",
            "action": "Deploy AI-based adaptive signal control system to dynamically adjust timing",
            "timeline": "2-3 days implementation",
            "cost": "Low (Software update)",
            "impact": "25-35% improvement in throughput"
        })
    
    if avg_ci > 1.3:
        recommendations["short_term"].append({
            "icon": "🚌",
            "title": "Enhanced Public Transit",
            "description": f"City-wide average CI: {avg_ci:.2f} (above normal)",
            "action": "Increase bus frequency by 40% on congested routes, add express shuttle services",
            "timeline": "1-2 days to implement",
            "cost": "Medium ($5,000-$10,000/day)",
            "impact": "Reduce private vehicle traffic by 12-18%"
        })
    
    recommendations["short_term"].append({
        "icon": "📊",
        "title": "Peak Hour Pricing Analysis",
        "description": "Evaluate congestion pricing feasibility",
        "action": "Conduct 7-day pilot study for variable toll pricing during rush hours",
        "timeline": "7 days data collection",
        "cost": "Low (Study only)",
        "impact": "Potential 15-20% reduction if implemented"
    })
    
    # LONG-TERM PLANNING (1-6 months)
    recommendations["long_term"].append({
        "icon": "🏗️",
        "title": "Infrastructure Capacity Expansion",
        "description": "Permanent solutions for recurring congestion",
        "action": "Widen critical corridors, add dedicated bus lanes, improve intersection design",
        "timeline": "3-6 months planning + construction",
        "cost": "High ($500K - $2M)",
        "impact": "40-60% long-term capacity increase"
    })
    
    recommendations["long_term"].append({
        "icon": "🤖",
        "title": "Smart City Integration",
        "description": "Deploy IoT sensors and predictive analytics",
        "action": "Install 500+ traffic sensors, implement ML-based prediction models",
        "timeline": "4-6 months deployment",
        "cost": "High ($1M - $3M)",
        "impact": "30-50% improvement in incident response time"
    })
    
    recommendations["long_term"].append({
        "icon": "🚴",
        "title": "Alternative Mobility Program",
        "description": "Reduce car dependency through bike-sharing and pedestrian zones",
        "action": "Launch e-bike fleet, create car-free zones in city center",
        "timeline": "2-4 months rollout",
        "cost": "Medium ($200K - $500K)",
        "impact": "10-15% reduction in short-distance car trips"
    })
    
    # AI INSIGHTS
    recommendations["insights"].append({
        "icon": "🧠",
        "title": "Peak Congestion Pattern",
        "insight": f"Analysis shows {len(high_zones)} critical zones. Focus intervention on highest CI zones first for maximum impact."
    })
    
    if avg_ci < 1.2:
        recommendations["insights"].append({
            "icon": "✅",
            "title": "System Performance",
            "insight": f"Overall city traffic flow is HEALTHY (Avg CI: {avg_ci:.2f}). Current measures are effective."
        })
    elif avg_ci >= 1.5:
        recommendations["insights"].append({
            "icon": "⚠️",
            "title": "System Stress Alert",
            "insight": f"City-wide CI at {avg_ci:.2f} indicates systemic issues. Immediate multi-zone intervention required."
        })
    else:
        recommendations["insights"].append({
            "icon": "📈",
            "title": "Moderate Stress Level",
            "insight": f"City-wide CI at {avg_ci:.2f}. Proactive measures recommended to prevent escalation."
        })
    
    recommendations["insights"].append({
        "icon": "💡",
        "title": "AI Prediction",
        "insight": "Based on historical patterns, congestion is likely to peak in the next 2-3 hours. Pre-emptive action recommended."
    })
    
    return recommendations


def main() -> None:
    st.set_page_config(page_title="🚦 CityFlow AI - Authority Mode", layout="wide", page_icon="🚦")
    
    st.markdown(
        f"# 🚦 {_icon_html('activity', 26)}CityFlow AI - Authority Command Center",
        unsafe_allow_html=True,
    )
    st.subheader("🎯 Traffic Intelligence & Real-Time Control System")
    
    # Initialize session state for live monitoring
    if "live_monitoring_active" not in st.session_state:
        st.session_state.live_monitoring_active = False
    if "live_data" not in st.session_state:
        st.session_state.live_data = None
    if "ws_thread" not in st.session_state:
        st.session_state.ws_thread = None
    if "data_queue" not in st.session_state:
        st.session_state.data_queue = None
    if "ws_connected" not in st.session_state:
        st.session_state.ws_connected = False
    if "update_logs" not in st.session_state:
        st.session_state.update_logs = []  # Store all updates for log display
    if "update_counter" not in st.session_state:
        st.session_state.update_counter = 0  # Count updates
    
    # Generate mock data
    zones_data = _generate_mock_zones_data()
    city_ci = round(np.mean([z["congestion_index"] for z in zones_data]), 2)
    
    # Create tabs
    tab_overview, tab_analytics, tab_live, tab_ai = st.tabs(
        ["🎛️ Command Center Overview", "📊 Analytics & Intelligence", "📡 Live Monitoring", "🤖 AI Recommendations"]
    )
    
    # ============ TAB 1: OVERVIEW ============
    with tab_overview:
        st.markdown("### 🌆 Real-Time Traffic Status")
        
        col1, col2, col3, col4 = st.columns(4)
        
        high_count = sum(1 for z in zones_data if z["congestion_level"] == "HIGH")
        medium_count = sum(1 for z in zones_data if z["congestion_level"] == "MEDIUM")
        low_count = sum(1 for z in zones_data if z["congestion_level"] == "LOW")
        avg_risk = round(np.mean([z["risk_score"] for z in zones_data]), 2)
        
        col1.metric("🔴 High Alert Zones", high_count)
        col2.metric("🟡 Medium Alert Zones", medium_count)
        col3.metric("🟢 Low Alert Zones", low_count)
        col4.metric("⚠️ Avg Risk Score", avg_risk)
        
        st.divider()
        
        st.markdown("### Zone Status Overview")
        overview_df = pd.DataFrame([
            {
                "Zone": z["zone_name"],
                "CI": z["congestion_index"],
                "Level": z["congestion_level"],
                "Risk": z["risk_score"],
                "Forecast": z["forecast_level"]
            }
            for z in zones_data
        ])
        st.dataframe(overview_df, use_container_width=True)
        
        st.divider()
        
        st.markdown("### City Congestion Heatmap")
        overview_map = _create_heatmap(zones_data)
        st_folium(overview_map, width=1200, height=500, key="overview_map", returned_objects=[])
    
    # ============ TAB 2: ANALYTICS ============
    with tab_analytics:
        st.markdown("### City KPI Dashboard")
        
        try:
            gauge_fig = _create_city_gauge(city_ci)
            st.plotly_chart(gauge_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to create gauge: {e}")
        
        st.markdown("---")
        
        st.markdown("### Zone Risk Assessment")
        try:
            risk_fig = _create_zone_risk_bar(zones_data)
            st.plotly_chart(risk_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to create risk chart: {e}")
        
        st.markdown("---")
        
        st.markdown("### Alert Severity Distribution")
        try:
            pie_fig = _create_severity_pie(zones_data)
            st.plotly_chart(pie_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to create severity chart: {e}")
        
        st.markdown("---")
        
        st.markdown("### 6-Hour Congestion Projection")
        try:
            projection_fig = _create_6hour_projection()
            st.plotly_chart(projection_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to create projection: {e}")
        
        st.markdown("---")
        
        st.markdown("### Policy Intervention Simulator")
        selected_zone = st.selectbox("Select Zone for Simulation", 
                                     [z["zone_name"] for z in zones_data])
        zone_data = next(z for z in zones_data if z["zone_name"] == selected_zone)
        
        scenario_map = {
            "None (Current)": "none",
            "Widen Road": "widen_road",
            "Optimize Signals": "optimize_signals",
            "Road Repair": "road_under_repair",
            "Heavy Vehicle Restriction": "heavy_vehicle_restriction"
        }
        
        selected_scenario = st.selectbox("Select Intervention", list(scenario_map.keys()))
        scenario_key = scenario_map[selected_scenario]
        
        try:
            engine = SimulationEngine()
            sim_result = engine.simulate(zone_data, scenario_key, hour=datetime.now().hour)
            
            if scenario_key != "none":
                impact_fig = _create_policy_impact_chart(
                    sim_result["before"]["ci"],
                    sim_result["after"]["ci"],
                    sim_result["before"]["risk_score"],
                    sim_result["after"]["risk_score"]
                )
                st.plotly_chart(impact_fig, use_container_width=True)
                
                improvement = sim_result["improvement_percent"]
                if improvement > 0:
                    st.success(f"✅ Projected Improvement: {improvement:.2f}%")
                elif improvement < 0:
                    st.error(f"⚠️  Projected Deterioration: {abs(improvement):.2f}%")
                else:
                    st.info("➡️  No significant impact")
        except Exception as e:
            st.error(f"Simulation failed: {e}")
        
        st.markdown("---")
        
        st.markdown("### Advanced Congestion Heatmap")
        try:
            analytics_map = _create_heatmap(zones_data)
            st_folium(analytics_map, width=1200, height=500, key="analytics_map", returned_objects=[])
        except Exception as e:
            st.error(f"Failed to create heatmap: {e}")
    
    # ============ TAB 3: LIVE MONITORING ============
    with tab_live:
        st.markdown("### 📡 Real-Time Traffic Corridor Monitoring")
        st.info("🔄 Monitor specific corridors with live updates every ~25 seconds")
        
        col1, col2 = st.columns(2)
        
        with col1:
            origin = st.text_input(
                "📍 Origin",
                value="Koramangala, Bangalore",
                disabled=st.session_state.live_monitoring_active
            )
        
        with col2:
            destination = st.text_input(
                "🎯 Destination",
                value="MG Road, Bangalore",
                disabled=st.session_state.live_monitoring_active
            )
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
        
        with col_btn1:
            if st.button(
                "▶️ Start Monitoring",
                disabled=st.session_state.live_monitoring_active,
                type="primary",
                use_container_width=True
            ):
                if origin and destination:
                    # Start monitoring via REST API
                    if _start_monitoring(origin, destination):
                        st.session_state.live_monitoring_active = True
                        st.session_state.live_data = None
                        st.session_state.update_logs = []  # Clear logs on new session
                        st.session_state.update_counter = 0
                        
                        # Create queue for WebSocket data
                        st.session_state.data_queue = Queue()
                        
                        # Start WebSocket listener in background thread
                        st.session_state.ws_thread = threading.Thread(
                            target=_run_ws_listener,
                            args=(st.session_state.data_queue,),
                            daemon=True
                        )
                        st.session_state.ws_thread.start()
                        
                        st.success("✅ Monitoring started! Waiting for first update...")
                        st.rerun()
                else:
                    st.error("❌ Please enter both origin and destination")
        
        with col_btn2:
            if st.button(
                "⏹️ Stop Monitoring",
                disabled=not st.session_state.live_monitoring_active,
                type="secondary",
                use_container_width=True
            ):
                _stop_monitoring()
                st.session_state.live_monitoring_active = False
                st.session_state.ws_connected = False
                st.session_state.live_data = None
                st.session_state.update_logs = []
                st.session_state.update_counter = 0
                st.success("⏹️ Monitoring stopped")
                st.rerun()
        
        st.divider()
        
        # Check for new data from WebSocket
        if st.session_state.live_monitoring_active and st.session_state.data_queue:
            try:
                # Non-blocking check for new messages
                while not st.session_state.data_queue.empty():
                    data = st.session_state.data_queue.get_nowait()
                    
                    # Handle connection status
                    if data.get("type") == "connected":
                        st.session_state.ws_connected = True
                    elif data.get("type") == "disconnected":
                        st.session_state.ws_connected = False
                        st.session_state.live_monitoring_active = False
                    elif data.get("type") == "error":
                        st.error(f"WebSocket error: {data.get('message')}")
                        st.session_state.ws_connected = False
                        st.session_state.live_monitoring_active = False
                    # Only store if it's a valid traffic update with all required fields
                    elif all(key in data for key in ['origin', 'destination', 'congestion_index', 'timestamp']):
                        st.session_state.live_data = data
                        # Add to update logs with counter
                        st.session_state.update_counter += 1
                        log_entry = {
                            "update_number": st.session_state.update_counter,
                            "data": data.copy()
                        }
                        st.session_state.update_logs.append(log_entry)
                        # Keep only last 20 updates to prevent memory issues
                        if len(st.session_state.update_logs) > 20:
                            st.session_state.update_logs = st.session_state.update_logs[-20:]
            except Exception as e:
                pass  # Queue empty or other non-critical error
        
        # Display live data
        if st.session_state.live_monitoring_active:
            # Connection status
            if st.session_state.ws_connected:
                st.success(f"{_icon_html('wifi', 16)} Connected to Live Monitor", icon="✅")
            else:
                st.warning(f"{_icon_html('wifi-off', 16)} Connecting...", icon="⏳")
            
            # Create two columns: current data and update log
            col_current, col_log = st.columns([1, 1])
            
            with col_current:
                st.markdown("### 🚗 Live Traffic Data")
                
                if st.session_state.live_data:
                    data = st.session_state.live_data
                    
                    # Validate that we have all required fields
                    required_fields = ['origin', 'destination', 'distance_km', 'duration_min', 
                                      'congestion_index', 'congestion_level', 'risk_score', 
                                      'alert', 'timestamp']
                    
                    if all(field in data for field in required_fields):
                        # Alert banner
                        if data.get("alert"):
                            st.error(
                                f"🚨 {_icon_html('alert-triangle', 20)} **CONGESTION ALERT** – Immediate Action Required",
                                icon="🚨"
                            )
                        else:
                            st.success(
                                f"✅ {_icon_html('check-circle', 20)} Traffic Flow Stable",
                                icon="✅"
                            )
                        
                        st.markdown("---")
                        
                        # Route info
                        st.markdown(f"**🛣️ Route:** {data['origin']} → {data['destination']}")
                        timestamp = datetime.fromisoformat(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                        st.caption(f"🕐 Last Update: {timestamp}")
                    
                        st.markdown("---")
                        
                        # Key metrics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                label="📊 Congestion Index",
                                value=f"{data['congestion_index']}",
                                delta=f"{data['congestion_level']}"
                            )
                        
                        with col2:
                            # Color code delta based on risk
                            risk_color = "inverse" if data['risk_score'] > 7 else "normal"
                            st.metric(
                                label="⚠️ Risk Score",
                                value=f"{data['risk_score']}/10",
                                delta=None
                            )
                        
                        with col3:
                            st.metric(
                                label="📏 Distance",
                                value=f"{data['distance_km']} km",
                                delta=None
                            )
                        
                        with col4:
                            st.metric(
                                label="⏱️ Duration",
                                value=f"{data['duration_min']} min",
                                delta=None
                            )
                        
                        st.markdown("---")
                        
                        # Congestion level badge
                        level = data['congestion_level']
                        if level == "HIGH":
                            badge_color = "#fee2e2"
                            text_color = "#991b1b"
                            icon = "alert-circle"
                        elif level == "MEDIUM":
                            badge_color = "#fef3c7"
                            text_color = "#92400e"
                            icon = "alert-triangle"
                        else:
                            badge_color = "#d1fae5"
                            text_color = "#065f46"
                            icon = "check-circle"
                        
                        st.markdown(
                            f"""<div style='padding: 20px; background: {badge_color}; border-radius: 10px; text-align: center;'>
                                <h2 style='color: {text_color}; margin: 0;'>
                                    {_icon_html(icon, 30)} {level} CONGESTION
                                </h2>
                            </div>""",
                            unsafe_allow_html=True
                        )
                    else:
                        # Invalid data structure received
                        st.warning("⚠️ Received incomplete data. Waiting for valid traffic update...")
                else:
                    st.info("⏳ Waiting for traffic data... First update will arrive within 25 seconds.")
            
            # Display update logs in the right column
            with col_log:
                st.markdown("### 📋 Live Update Log")
                st.caption(f"🔄 Updates arrive every ~25 seconds")
                
                if st.session_state.update_logs:
                    # Create a scrollable container for logs
                    log_container = st.container()
                    
                    with log_container:
                        # Display updates in reverse order (newest first)
                        for log_entry in reversed(st.session_state.update_logs):
                            update_num = log_entry["update_number"]
                            log_data = log_entry["data"]
                            
                            # Parse timestamp
                            timestamp = datetime.fromisoformat(log_data['timestamp']).strftime('%H:%M:%S')
                            
                            # Determine colors based on congestion level
                            level = log_data['congestion_level']
                            if level == "HIGH":
                                border_color = "#ef4444"
                                bg_color = "#fee2e2"
                                emoji = "🔴"
                            elif level == "MEDIUM":
                                border_color = "#f59e0b"
                                bg_color = "#fef3c7"
                                emoji = "🟡"
                            else:
                                border_color = "#10b981"
                                bg_color = "#d1fae5"
                                emoji = "🟢"
                            
                            # Build log entry HTML
                            alert_html = ""
                            if log_data.get("alert"):
                                alert_html = '<div style="background: #dc2626; color: white; padding: 5px 10px; border-radius: 5px; margin-top: 8px; font-weight: bold;">⚠️ ALERT: HIGH CONGESTION DETECTED!</div>'
                            
                            log_html = f"""
                            <div style="border-left: 4px solid {border_color}; background: {bg_color}; padding: 12px; margin-bottom: 12px; border-radius: 5px;">
                                <div style="font-weight: bold; font-size: 14px; margin-bottom: 5px;">
                                    {emoji} Update #{update_num} — {timestamp}
                                </div>
                                <div style="font-size: 12px; color: #374151; line-height: 1.6;">
                                    <strong>Route:</strong> {log_data['origin']} → {log_data['destination']}<br>
                                    <strong>Distance:</strong> {log_data['distance_km']} km | <strong>Duration:</strong> {log_data['duration_min']} min<br>
                                    <strong>Congestion:</strong> {level} (Index: {log_data['congestion_index']}) | <strong>Risk:</strong> {log_data['risk_score']}/10
                                </div>
                                {alert_html}
                            </div>
                            """
                            
                            st.markdown(log_html, unsafe_allow_html=True)
                else:
                    st.info("⏳ No updates yet. Waiting for first traffic data...")
            
            # Auto-refresh every 2 seconds to check for new data
            import time
            time.sleep(2)
            st.rerun()
        
        else:
            st.info("👆 Click 'Start Monitoring' to begin receiving live traffic updates")
    
    # ============ TAB 4: AI RECOMMENDATIONS ============
    with tab_ai:
        st.markdown("### 🤖 AI-Powered Traffic Management Recommendations")
        st.info("💡 Real-time intelligent suggestions based on current traffic conditions and predictive analytics")
        
        # Generate recommendations
        recommendations = _generate_ai_recommendations(zones_data, st.session_state.live_data)
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🚨 Immediate Actions", len(recommendations["immediate"]))
        col2.metric("📅 Short-term Strategies", len(recommendations["short_term"]))
        col3.metric("🎯 Long-term Plans", len(recommendations["long_term"]))
        col4.metric("🧠 AI Insights", len(recommendations["insights"]))
        
        st.markdown("---")
        
        # IMMEDIATE ACTIONS
        st.markdown("### 🚨 Immediate Actions (Next 1 Hour)")
        if recommendations["immediate"]:
            for rec in recommendations["immediate"]:
                priority_color = "#fee2e2" if rec.get("priority") == "CRITICAL" else "#fef3c7"
                priority_text = "#991b1b" if rec.get("priority") == "CRITICAL" else "#92400e"
                
                st.markdown(
                    f"""<div style='background: {priority_color}; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid {priority_text};'>
                        <h4 style='margin: 0 0 10px 0; color: {priority_text};'>{rec['icon']} {rec['title']}</h4>
                        <p style='margin: 5px 0; color: #374151;'><strong>📋 Details:</strong> {rec['description']}</p>
                        <p style='margin: 5px 0; color: #374151;'><strong>🎯 Action:</strong> {rec['action']}</p>
                        <p style='margin: 5px 0; color: #374151;'><strong>📊 Expected Impact:</strong> {rec['impact']}</p>
                    </div>""",
                    unsafe_allow_html=True
                )
        else:
            st.success("✅ No immediate actions required. Traffic flow is stable.")
        
        st.markdown("---")
        
        # SHORT-TERM STRATEGIES
        st.markdown("### 📅 Short-term Strategies (1-7 Days)")
        for rec in recommendations["short_term"]:
            with st.expander(f"{rec['icon']} {rec['title']}", expanded=False):
                st.markdown(f"**📋 Description:** {rec['description']}")
                st.markdown(f"**🎯 Recommended Action:** {rec['action']}")
                st.markdown(f"**⏱️ Timeline:** {rec['timeline']}")
                st.markdown(f"**💰 Cost Estimate:** {rec['cost']}")
                st.markdown(f"**📊 Expected Impact:** {rec['impact']}")
        
        st.markdown("---")
        
        # LONG-TERM PLANNING
        st.markdown("### 🎯 Long-term Planning (1-6 Months)")
        for rec in recommendations["long_term"]:
            with st.expander(f"{rec['icon']} {rec['title']}", expanded=False):
                st.markdown(f"**📋 Description:** {rec['description']}")
                st.markdown(f"**🎯 Recommended Action:** {rec['action']}")
                st.markdown(f"**⏱️ Timeline:** {rec['timeline']}")
                st.markdown(f"**💰 Cost Estimate:** {rec['cost']}")
                st.markdown(f"**📊 Expected Impact:** {rec['impact']}")
        
        st.markdown("---")
        
        # AI INSIGHTS
        st.markdown("### 🧠 AI-Generated Insights")
        for insight in recommendations["insights"]:
            st.info(f"{insight['icon']} **{insight['title']}:** {insight['insight']}")
        
        st.markdown("---")
        
        # Action Tracker
        st.markdown("### 📝 Implementation Tracker")
        st.markdown("Track the status of recommended actions:")
        
        # Create a simple tracking table
        tracking_data = {
            "Action": ["Deploy Traffic Control", "Issue Public Advisory", "Signal Re-programming", "Enhanced Public Transit"],
            "Priority": ["🔴 Critical", "🟡 High", "🟢 Medium", "🟢 Medium"],
            "Status": ["⏳ Pending", "⏳ Pending", "⏳ Pending", "⏳ Pending"],
            "Assigned To": ["Traffic Division", "Communications", "Tech Team", "Transit Authority"]
        }
        
        tracking_df = pd.DataFrame(tracking_data)
        st.dataframe(tracking_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        st.markdown("### 📞 Emergency Contacts")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🚓 Traffic Police Command**  
            Emergency: 100  
            Control Room: +91-80-2222-2222
            """)
        
        with col2:
            st.markdown("""
            **🚌 Transit Operations**  
            Dispatch: +91-80-3333-3333  
            Control: +91-80-3333-3334
            """)
        
        with col3:
            st.markdown("""
            **🔧 Infrastructure Team**  
            Emergency: +91-80-4444-4444  
            Signals: +91-80-4444-4445
            """)
    
    st.divider()
    st.caption("🚦 CityFlow AI - Smart City Traffic Intelligence | Authority Mode")


if __name__ == "__main__":
    main()
