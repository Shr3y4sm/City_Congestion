"""
Quick Test - TomTom Refactored Monitoring
==========================================
Test the refactored monitoring system with detailed output
"""

import requests
import asyncio
import websockets
import json
from datetime import datetime

API_BASE = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/live-monitor"

def test_connection():
    """Test if API is responding"""
    try:
        response = requests.get(f"{API_BASE}/", timeout=3)
        print(f"✓ API Status: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ API Connection Failed: {e}")
        return False

def start_monitoring():
    """Start monitoring session"""
    try:
        response = requests.post(
            f"{API_BASE}/start-monitoring",
            json={"origin": "Koramangala, Bangalore", "destination": "MG Road, Bangalore"},
            timeout=5
        )
        response.raise_for_status()
        print(f"✓ Monitoring Started: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Failed to start monitoring: {e}")
        return False

async def watch_updates():
    """Watch for traffic updates via WebSocket"""
    print("\n" + "="*70)
    print("Watching for traffic updates...")
    print("="*70)
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✓ WebSocket connected")
            
            for i in range(3):  # Wait for 3 updates
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=35)
                    data = json.loads(message)
                    
                    if "congestion_index" in data:
                        print(f"\n━━━ Update #{i+1} ━━━")
                        print(f"Time: {data.get('timestamp')}")
                        print(f"Route: {data.get('origin')} → {data.get('destination')}")
                        print(f"Distance: {data.get('distance_km')} km")
                        print(f"Duration: {data.get('duration_min')} min")
                        print(f"Congestion: {data.get('congestion_level')} (Index: {data.get('congestion_index')})")
                        print(f"Risk: {data.get('risk_score')}/10")
                        if data.get('alert'):
                            print("⚠️  ALERT: HIGH CONGESTION!")
                        print("-"*70)
                    else:
                        print(f"Received message: {data}")
                        
                except asyncio.TimeoutError:
                    print(f"\n⚠  Timeout waiting for update #{i+1}")
                    print("   (Expected delay: ~25 seconds between updates)")
                    break
                    
    except Exception as e:
        print(f"✗ WebSocket error: {e}")

async def main():
    print("\n" + "="*70)
    print("  TomTom Refactored Monitoring - Integration Test")
    print("="*70 + "\n")
    
    # Test connection
    if not test_connection():
        return
    
    # Start monitoring
    if not start_monitoring():
        return
    
    # Watch updates
    await watch_updates()
    
    print("\n" + "="*70)
    print("Test complete!")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted")
