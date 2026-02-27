"""
Test Client for CityFlow AI Live Traffic Monitor
=================================================
Demonstrates how to:
1. Start monitoring via REST API
2. Connect to WebSocket for live updates
3. Handle real-time traffic data
"""

import asyncio
import json
import requests
import websockets
from datetime import datetime


# Configuration
API_BASE = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/live-monitor"


def start_monitoring(origin: str, destination: str):
    """Start traffic monitoring via REST API"""
    url = f"{API_BASE}/start-monitoring"
    payload = {
        "origin": origin,
        "destination": destination
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        print(f"[START] {result['message']}")
        print(f"        Route: {origin} -> {destination}")
        print(f"        Poll interval: {result['poll_interval_seconds']}s")
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to start monitoring: {e}")
        return False


def stop_monitoring():
    """Stop traffic monitoring via REST API"""
    url = f"{API_BASE}/stop-monitoring"
    
    try:
        response = requests.post(url)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n[STOP] {result['message']}")
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to stop monitoring: {e}")
        return False


def get_status():
    """Get current monitoring status"""
    url = f"{API_BASE}/status"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        status = response.json()
        print("\n[STATUS]")
        print(f"  Monitoring: {status['is_monitoring']}")
        print(f"  Origin: {status.get('origin', 'N/A')}")
        print(f"  Destination: {status.get('destination', 'N/A')}")
        print(f"  Connected clients: {status['connected_clients']}")
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to get status: {e}")


async def listen_websocket(duration_seconds: int = 60):
    """Connect to WebSocket and listen for live updates"""
    try:
        async with websockets.connect(WS_URL) as websocket:
            print(f"\n[WS] Connected to live monitor")
            print("[WS] Listening for updates... (press Ctrl+C to stop)\n")
            
            start_time = asyncio.get_event_loop().time()
            
            while True:
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > duration_seconds:
                    print(f"\n[WS] Test duration reached ({duration_seconds}s)")
                    break
                
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=25.0  # Slightly longer than poll interval
                    )
                    
                    data = json.loads(message)
                    
                    # Handle different message types
                    if data.get("type") == "connection":
                        print(f"[WS] {data['message']}")
                        continue
                    
                    # Display traffic update
                    display_update(data)
                
                except asyncio.TimeoutError:
                    print("[WS] No update received (waiting...)")
                    continue
    
    except websockets.exceptions.WebSocketException as e:
        print(f"[WS ERROR] {e}")
    
    except KeyboardInterrupt:
        print("\n[WS] Disconnected by user")


def display_update(data: dict):
    """Format and display traffic update"""
    timestamp = datetime.fromisoformat(data['timestamp']).strftime('%H:%M:%S')
    
    # Color code based on congestion level
    level_colors = {
        'LOW': '🟢',
        'MEDIUM': '🟡',
        'HIGH': '🔴'
    }
    icon = level_colors.get(data['congestion_level'], '⚪')
    
    print(f"[{timestamp}] {icon} {data['congestion_level']}")
    print(f"  Distance: {data['distance_km']} km")
    print(f"  Duration: {data['duration_min']} min")
    print(f"  Congestion Index: {data['congestion_index']}")
    print(f"  Risk Score: {data['risk_score']}/10")
    
    if data['alert']:
        print(f"  ⚠️  ALERT: High congestion detected!")
    
    print()


async def main():
    """Main test flow"""
    print("=" * 60)
    print("CityFlow AI - Live Monitor Test Client")
    print("=" * 60)
    
    # Test configuration
    ORIGIN = "Koramangala, Bangalore"
    DESTINATION = "MG Road, Bangalore"
    LISTEN_DURATION = 60  # Listen for 60 seconds
    
    # 1. Check initial status
    get_status()
    
    # 2. Start monitoring
    print()
    if not start_monitoring(ORIGIN, DESTINATION):
        return
    
    # 3. Listen to WebSocket updates
    try:
        await listen_websocket(duration_seconds=LISTEN_DURATION)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
    
    # 4. Stop monitoring
    stop_monitoring()
    
    # 5. Check final status
    get_status()
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[EXIT] Test client stopped")
