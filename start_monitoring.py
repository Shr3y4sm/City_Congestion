"""
Start Monitoring - Python Helper
=================================
Start traffic monitoring with a simple Python command
"""

import requests
import sys

API_BASE = "http://localhost:8000"

def start_monitoring(origin: str, destination: str):
    """Start monitoring a traffic corridor"""
    print("\n" + "=" * 70)
    print("  CityFlow AI - Start Monitoring")
    print("=" * 70 + "\n")
    
    print(f"Route: {origin} → {destination}\n")
    print("Starting monitoring...")
    
    try:
        response = requests.post(
            f"{API_BASE}/start-monitoring",
            json={"origin": origin, "destination": destination},
            timeout=5
        )
        response.raise_for_status()
        
        data = response.json()
        
        print("\n✓ Monitoring started successfully!")
        print(f"  Origin:      {data['origin']}")
        print(f"  Destination: {data['destination']}")
        print(f"  Interval:    {data['poll_interval_seconds']} seconds")
        
        print("\n" + "=" * 70)
        print("Next Steps:")
        print("  1. Run: python watch_traffic.py")
        print("  2. Or open dashboard: http://localhost:8501")
        print("=" * 70 + "\n")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Failed to connect to API service!")
        print("\nTroubleshooting:")
        print("  1. Start API service: python api/live_stream.py")
        print("  2. Check if port 8000 is available")
        return False
        
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ API error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check service status: curl http://localhost:8000/status")
        print("  2. Restart API service if needed")
        return False
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    # Default route
    origin = "Koramangala, Bangalore"
    destination = "MG Road, Bangalore"
    
    # Accept command line arguments
    if len(sys.argv) >= 3:
        origin = sys.argv[1]
        destination = sys.argv[2]
    elif len(sys.argv) == 2:
        print(f"Usage: python {sys.argv[0]} [origin] [destination]")
        print(f"\nExample:")
        print(f"  python {sys.argv[0]} \"Koramangala, Bangalore\" \"MG Road, Bangalore\"")
        print(f"\nOr just run without arguments to use default route.\n")
        sys.exit(1)
    
    success = start_monitoring(origin, destination)
    sys.exit(0 if success else 1)
