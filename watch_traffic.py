"""
CityFlow AI - Terminal Traffic Viewer
======================================
Watch live traffic updates in your terminal (no interaction needed)
"""

import asyncio
import websockets
import json
import requests
import sys
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

API_BASE = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/live-monitor"


def print_banner():
    """Print startup banner"""
    print("\n" + "=" * 70)
    print(f"{Fore.CYAN}  CityFlow AI - Live Traffic Monitor Terminal{Style.RESET_ALL}")
    print("=" * 70 + "\n")


def format_update(data: dict, update_num: int):
    """Format and print traffic update"""
    # Get data fields
    timestamp = data.get("timestamp", "N/A")
    origin = data.get("origin", "Unknown")
    destination = data.get("destination", "Unknown")
    distance = data.get("distance_km", 0)
    duration = data.get("duration_min", 0)
    congestion = data.get("congestion_index", 0)
    level = data.get("congestion_level", "UNKNOWN")
    risk = data.get("risk_score", 0)
    alert = data.get("alert", False)
    
    # Choose color
    if level == "LOW":
        color = Fore.GREEN
    elif level == "MEDIUM":
        color = Fore.YELLOW
    else:
        color = Fore.RED
    
    # Print formatted update
    print(f"\n{Fore.MAGENTA}━━━ Update #{update_num} ━━━{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Time:{Style.RESET_ALL} {timestamp}")
    print(f"{Fore.CYAN}Route:{Style.RESET_ALL} {origin} → {destination}")
    print(f"{Fore.CYAN}Distance:{Style.RESET_ALL} {distance} km  |  {Fore.CYAN}Duration:{Style.RESET_ALL} {duration:.1f} min")
    print(f"{Fore.CYAN}Congestion:{Style.RESET_ALL} {color}{level}{Style.RESET_ALL} (Index: {congestion:.2f})  |  {Fore.CYAN}Risk:{Style.RESET_ALL} {risk:.1f}/10")
    
    if alert:
        print(f"\n{Fore.RED}⚠️  ALERT: HIGH CONGESTION DETECTED!{Style.RESET_ALL}")
    
    print("-" * 70)


async def watch_traffic():
    """Connect to WebSocket and display updates"""
    update_count = 0
    
    print(f"{Fore.GREEN}✓ Connecting to live monitoring service...{Style.RESET_ALL}")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print(f"{Fore.GREEN}✓ Connected! Waiting for traffic updates...{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}(Updates arrive every ~20 seconds. Press Ctrl+C to stop){Style.RESET_ALL}")
            print("=" * 70)
            
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                
                # Only show updates with traffic data
                if "congestion_index" in data:
                    update_count += 1
                    format_update(data, update_count)
                    
    except websockets.exceptions.ConnectionClosed:
        print(f"\n{Fore.YELLOW}✗ Connection closed{Style.RESET_ALL}")
    except KeyboardInterrupt:
        print(f"\n\n{Fore.CYAN}Monitoring stopped by user{Style.RESET_ALL}")


def check_service():
    """Check if API service is running"""
    try:
        response = requests.get(f"{API_BASE}/status", timeout=3)
        if response.status_code == 200:
            status = response.json()
            return status["is_monitoring"], status.get("origin"), status.get("destination")
    except:
        pass
    return False, None, None


def main():
    """Main entry point"""
    print_banner()
    
    # Check service
    print(f"{Fore.CYAN}Checking API service...{Style.RESET_ALL}")
    is_monitoring, origin, dest = check_service()
    
    if not is_monitoring:
        print(f"{Fore.RED}✗ No active monitoring session!{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Please start monitoring first:{Style.RESET_ALL}")
        print(f"  1. Go to the Streamlit dashboard: {Fore.CYAN}http://localhost:8501{Style.RESET_ALL}")
        print(f"  2. Navigate to 'Live Monitoring' tab")
        print(f"  3. Enter a route and click 'Start Monitoring'")
        print(f"\n{Fore.YELLOW}Or use curl:{Style.RESET_ALL}")
        print(f'  curl -X POST http://localhost:8000/start-monitoring -H "Content-Type: application/json" -d \'{{"origin":"Koramangala, Bangalore","destination":"MG Road, Bangalore"}}\'')
        sys.exit(1)
    
    print(f"{Fore.GREEN}✓ API service is running{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✓ Active monitoring session found:{Style.RESET_ALL}")
    print(f"    {origin} → {dest}\n")
    
    # Start watching
    try:
        asyncio.run(watch_traffic())
    except KeyboardInterrupt:
        pass
    
    print(f"\n{Fore.WHITE}Thank you for using CityFlow AI!{Style.RESET_ALL}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted{Style.RESET_ALL}\n")
        sys.exit(0)
