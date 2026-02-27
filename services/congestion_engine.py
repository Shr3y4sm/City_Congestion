"""
CityFlow AI - Congestion Intelligence Engine
Analyzes traffic routes and calculates congestion metrics for optimal route recommendation.
"""

from datetime import datetime
from typing import Dict, List


class CongestionEngine:
    """
    Intelligence engine for analyzing traffic congestion and recommending optimal routes.
    """
    
    # Speed constants (km/h)
    BASE_SPEED = 35
    PEAK_HOUR_SPEED = 25
    WEEKEND_SPEED = 40
    
    # Peak hour ranges
    MORNING_PEAK = (8, 10)
    EVENING_PEAK = (17, 20)
    
    # Congestion thresholds
    LOW_THRESHOLD = 1.2
    MEDIUM_THRESHOLD = 1.5
    
    def calculate_expected_duration(self, distance_km: float) -> float:
        """
        Calculate expected travel duration based on distance and current time conditions.
        
        Args:
            distance_km: Distance in kilometers
            
        Returns:
            Expected duration in minutes (rounded to 2 decimal places)
        """
        now = datetime.now()
        current_hour = now.hour
        is_weekend = now.weekday() >= 5  # Saturday = 5, Sunday = 6
        
        # Determine speed based on time conditions
        if is_weekend:
            speed = self.WEEKEND_SPEED
        elif (self.MORNING_PEAK[0] <= current_hour < self.MORNING_PEAK[1] or 
              self.EVENING_PEAK[0] <= current_hour < self.EVENING_PEAK[1]):
            speed = self.PEAK_HOUR_SPEED
        else:
            speed = self.BASE_SPEED
        
        # Calculate duration: (distance / speed) * 60 to get minutes
        expected_duration = (distance_km / speed) * 60
        
        return round(expected_duration, 2)
    
    def calculate_congestion_index(self, actual_duration: float, 
                                   expected_duration: float) -> float:
        """
        Calculate congestion index as ratio of actual to expected duration.
        
        Args:
            actual_duration: Actual travel time in minutes
            expected_duration: Expected travel time in minutes
            
        Returns:
            Congestion index (rounded to 2 decimal places)
        """
        if expected_duration == 0:
            return 1.0
        
        congestion_index = actual_duration / expected_duration
        return round(congestion_index, 2)
    
    def assign_congestion_level(self, index: float) -> str:
        """
        Assign congestion level based on congestion index.
        
        Args:
            index: Congestion index value
            
        Returns:
            Congestion level: "LOW", "MEDIUM", or "HIGH"
        """
        if index < self.LOW_THRESHOLD:
            return "LOW"
        elif index < self.MEDIUM_THRESHOLD:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def analyze_routes(self, route_data: Dict) -> Dict:
        """
        Analyze all routes and determine the optimal route based on congestion.
        
        Args:
            route_data: Dictionary containing origin, destination, and routes list
            
        Returns:
            Enhanced route data with congestion metrics and best route recommendation
        """
        enhanced_routes = []
        best_route_index = 0
        lowest_congestion_index = float('inf')
        
        for idx, route in enumerate(route_data.get("routes", [])):
            # Extract route details
            distance_km = route["distance_km"]
            actual_duration = route["duration_min"]
            
            # Calculate congestion metrics
            expected_duration = self.calculate_expected_duration(distance_km)
            congestion_index = self.calculate_congestion_index(
                actual_duration, 
                expected_duration
            )
            congestion_level = self.assign_congestion_level(congestion_index)
            
            # Create enhanced route
            enhanced_route = {
                "distance_km": distance_km,
                "duration_min": actual_duration,
                "expected_duration_min": expected_duration,
                "congestion_index": congestion_index,
                "congestion_level": congestion_level,
                "geometry": route.get("geometry", "")
            }
            
            enhanced_routes.append(enhanced_route)
            
            # Track best route (lowest congestion)
            if congestion_index < lowest_congestion_index:
                lowest_congestion_index = congestion_index
                best_route_index = idx
        
        return {
            "origin": route_data.get("origin", ""),
            "destination": route_data.get("destination", ""),
            "best_route_index": best_route_index,
            "routes": enhanced_routes
        }


if __name__ == "__main__":
    """Test the CongestionEngine with mock route data."""
    
    # Mock route data (simulating TrafficService output)
    mock_data = {
        "origin": "MG Road, Bangalore",
        "destination": "Koramangala, Bangalore",
        "routes": [
            {
                "distance_km": 4.88,
                "duration_min": 8.8,
                "geometry": "encoded_polyline_1"
            },
            {
                "distance_km": 4.98,
                "duration_min": 9.78,
                "geometry": "encoded_polyline_2"
            },
            {
                "distance_km": 5.01,
                "duration_min": 12.5,
                "geometry": "encoded_polyline_3"
            }
        ]
    }
    
    # Analyze routes
    engine = CongestionEngine()
    result = engine.analyze_routes(mock_data)
    
    # Display results
    print("🚦 CityFlow AI - Congestion Analysis\n")
    print(f"Origin: {result['origin']}")
    print(f"Destination: {result['destination']}")
    print(f"\nCurrent time: {datetime.now().strftime('%A, %I:%M %p')}")
    print(f"\n{'='*60}\n")
    
    for idx, route in enumerate(result['routes']):
        is_best = idx == result['best_route_index']
        marker = "⭐ RECOMMENDED" if is_best else ""
        
        print(f"Route {idx + 1} {marker}")
        print(f"  Distance:           {route['distance_km']} km")
        print(f"  Actual Duration:    {route['duration_min']} min")
        print(f"  Expected Duration:  {route['expected_duration_min']} min")
        print(f"  Congestion Index:   {route['congestion_index']}")
        print(f"  Congestion Level:   {route['congestion_level']}")
        print()
    
    print(f"{'='*60}")
    print(f"\n✅ Best Route: Route {result['best_route_index'] + 1}")
    best = result['routes'][result['best_route_index']]
    print(f"   ({best['distance_km']} km, {best['duration_min']} min, "
          f"Congestion: {best['congestion_level']})")
