"""
CityFlow AI - Complete Demo
Integrated demo showing TrafficService + CongestionEngine working together.
"""

import sys
from datetime import datetime
from traffic_service import TrafficService
from services.congestion_engine import CongestionEngine


def display_analysis(result: dict):
    """Display congestion analysis results in a formatted way."""
    print("CityFlow AI - Intelligent Route Analysis\n")
    print(f"Origin:      {result['origin']}")
    print(f"Destination: {result['destination']}")
    print(f"Time:        {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}")
    print(f"\n{'='*70}\n")
    
    for idx, route in enumerate(result['routes']):
        is_best = idx == result['best_route_index']
        marker = "[RECOMMENDED]" if is_best else ""
        
        print(f"{marker} Route {idx + 1}")
        print(f"   Distance:           {route['distance_km']} km")
        print(f"   Actual Duration:    {route['duration_min']} min")
        print(f"   Expected Duration:  {route['expected_duration_min']} min")
        print(f"   Congestion Index:   {route['congestion_index']}")
        print(f"   Congestion Level:   {route['congestion_level']}")
        print()
    
    print(f"{'='*70}")
    best = result['routes'][result['best_route_index']]
    print(f"\nRECOMMENDATION: Take Route {result['best_route_index'] + 1}")
    print(f"   - Distance: {best['distance_km']} km")
    print(f"   - Duration: {best['duration_min']} minutes")
    print(f"   - Congestion: {best['congestion_level']}")
    print(f"   - Efficiency: {best['congestion_index']}x expected time")


def main():
    """Run the complete CityFlow AI demo."""
    try:
        # Get user input or use defaults
        if len(sys.argv) >= 3:
            origin = sys.argv[1]
            destination = sys.argv[2]
        else:
            origin = "MG Road, Bangalore"
            destination = "Koramangala, Bangalore"
        
        print("Initializing CityFlow AI...\n")
        
        # Step 1: Fetch routes using TrafficService
        print("Fetching routes from OpenRouteService API...")
        traffic_service = TrafficService()
        route_data = traffic_service.get_routes(origin, destination)
        print(f"Found {len(route_data['routes'])} alternative routes\n")
        
        # Step 2: Analyze congestion using CongestionEngine
        print("Analyzing congestion patterns...")
        engine = CongestionEngine()
        analysis = engine.analyze_routes(route_data)
        print("Congestion analysis complete\n")
        
        print(f"{'='*70}\n")
        
        # Step 3: Display results
        display_analysis(analysis)
        
    except ValueError as e:
        print(f"Input Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("                    CityFlow AI")
    print("           Intelligent Traffic Route Optimization")
    print("="*70 + "\n")
    
    main()
    
    print("\n" + "="*70)
    print("\nUsage: python demo.py \"Origin Address\" \"Destination Address\"")
    print("="*70 + "\n")
