"""
CityFlow AI - Terminal Live Monitor
====================================
Display real-time traffic updates in the terminal
"""

import asyncio
import websockets
import json
import requests
from datetime import datetime
from colorama import init, Fore, Style, Back

# Initialize colorama for Windows
init(autoreset=True)

API_BASE = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/live-monitor"


def clear_screen():
    """Clear terminal screen"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print header banner"""
    print(f"\n{Back.BLUE}{Fore.WHITE}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Back.BLUE}{Fore.WHITE}  CityFlow AI - Live Traffic Monitor  {Style.RESET_ALL}")
    print(f"{Back.BLUE}{Fore.WHITE}{'=' * 80}{Style.RESET_ALL}\n")


def get_congestion_color(level: str) -> str:
    """Get color based on congestion level"""
    colors = {
        "LOW": Fore.GREEN,
        "MEDIUM": Fore.YELLOW,
        "HIGH": Fore.RED
    }
    return colors.get(level, Fore.WHITE)


def format_traffic_update(data: dict) -> str:
    """Format traffic update for terminal display"""
    timestamp = data.get("timestamp", "")
    origin = data.get("origin", "Unknown")
    destination = data.get("destination", "Unknown")
    distance_km = data.get("distance_km", 0)
    duration_min = data.get("duration_min", 0)
    congestion_index = data.get("congestion_index", 0)
    congestion_level = data.get("congestion_level", "UNKNOWN")
    risk_score = data.get("risk_score", 0)
    alert = data.get("alert", False)
    
    # Get color for congestion level
    color = get_congestion_color(congestion_level)
    
    # Format output
    output = []
    output.append(f"{Fore.CYAN}[{timestamp}]{Style.RESET_ALL}")
    output.append(f"\n{Fore.WHITE}Route:{Style.RESET_ALL} {origin} → {destination}")
    output.append(f"{Fore.WHITE}Distance:{Style.RESET_ALL} {distance_km} km")
    output.append(f"{Fore.WHITE}Duration:{Style.RESET_ALL} {duration_min:.1f} min")
    output.append(f"{Fore.WHITE}Congestion:{Style.RESET_ALL} {color}{congestion_level}{Style.RESET_ALL} (Index: {congestion_index:.2f})")
    output.append(f"{Fore.WHITE}Risk Score:{Style.RESET_ALL} {risk_score:.1f}/10")
    
    if alert:
        output.append(f"\n{Back.RED}{Fore.WHITE} ⚠ ALERT: HIGH CONGESTION DETECTED! {Style.RESET_ALL}")
    
    output.append("\n" + "-" * 80)
    
    return "\n".join(output)


def start_monitoring(origin: str, destination: str) -> bool:
    """Start monitoring via REST API"""
    try:
        response = requests.post(
            f"{API_BASE}/start-monitoring",
            json={"origin": origin, "destination": destination},
            timeout=5
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"{Fore.RED}Error starting monitoring: {e}{Style.RESET_ALL}")
        return False


def stop_monitoring() -> bool:
    """Stop monitoring via REST API"""
    try:
        response = requests.post(f"{API_BASE}/stop-monitoring", timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"{Fore.RED}Error stopping monitoring: {e}{Style.RESET_ALL}")
        return False


async def monitor_traffic():
    """Connect to WebSocket and display live traffic updates"""
    update_count = 0
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print(f"{Fore.GREEN}✓ Connected to live monitoring service{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Waiting for traffic updates... (Updates every ~20 seconds){Style.RESET_ALL}\n")
            print("-" * 80)
            
            while True:
                try:
                    # Receive message
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    # Only display if it has traffic data (not just connection messages)
                    if "congestion_index" in data:
                        update_count += 1
                        print(f"\n{Fore.MAGENTA}Update #{update_count}{Style.RESET_ALL}")
                        print(format_traffic_update(data))
                    
                except websockets.exceptions.ConnectionClosed:
                    print(f"\n{Fore.YELLOW}Connection closed by server{Style.RESET_ALL}")
                    break
                except json.JSONDecodeError:
                    print(f"{Fore.YELLOW}Received non-JSON message{Style.RESET_ALL}")
                    continue
                except KeyboardInterrupt:
                    print(f"\n\n{Fore.YELLOW}Stopping monitor...{Style.RESET_ALL}")
                    break
                    
    except websockets.exceptions.WebSocketException as e:
        print(f"{Fore.RED}WebSocket error: {e}{Style.RESET_ALL}")
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Monitoring interrupted by user{Style.RESET_ALL}")


def check_service() -> bool:
    """Check if the API service is running"""
    try:
        response = requests.get(f"{API_BASE}/", timeout=3)
        if response.status_code == 200:
            return True
    except:
        pass
    return False


async def main():
    """Main function"""
    clear_screen()
    print_header()
    
    # Check if service is running
    print(f"{Fore.CYAN}Checking API service...{Style.RESET_ALL}")
    if not check_service():
        print(f"{Fore.RED}✗ API service is not running!{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Please start the service first:{Style.RESET_ALL}")
        print(f"  python api/live_stream.py")
        return
    
    print(f"{Fore.GREEN}✓ API service is running{Style.RESET_ALL}\n")
    
    # Get route from user
    print(f"{Fore.CYAN}Enter route to monitor:{Style.RESET_ALL}")
    origin = input(f"  Origin: ").strip() or "Koramangala, Bangalore"
    destination = input(f"  Destination: ").strip() or "MG Road, Bangalore"
    
    print(f"\n{Fore.CYAN}Starting monitoring for:{Style.RESET_ALL}")
    print(f"  {origin} → {destination}\n")
    
    # Start monitoring
    if not start_monitoring(origin, destination):
        print(f"{Fore.RED}Failed to start monitoring{Style.RESET_ALL}")
        return
    
    print(f"{Fore.GREEN}✓ Monitoring started{Style.RESET_ALL}\n")
    
    try:
        # Connect to WebSocket and display updates
        await monitor_traffic()
    finally:
        # Stop monitoring
        print(f"\n{Fore.CYAN}Stopping monitoring...{Style.RESET_ALL}")
        stop_monitoring()
        print(f"{Fore.GREEN}✓ Monitoring stopped{Style.RESET_ALL}")
        print(f"\n{Fore.WHITE}Thank you for using CityFlow AI!{Style.RESET_ALL}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Program terminated by user{Style.RESET_ALL}")
