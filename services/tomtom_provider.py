"""
TomTom Traffic API Provider
============================
Live traffic data integration for CityFlow AI - Traffic Command Center

Provides real-time traffic information using TomTom Routing API
with traffic flow data for accurate congestion analysis.
"""

import os
import requests
from typing import Dict, Optional
from dotenv import load_dotenv


class TomTomProvider:
    """
    TomTom Traffic API provider for live corridor traffic data.
    
    Uses TomTom Routing API to fetch real-time traffic conditions
    and compute congestion metrics for traffic corridors.
    """
    
    BASE_URL = "https://api.tomtom.com/routing/1/calculateRoute"
    
    # Congestion thresholds
    LOW_THRESHOLD = 1.2
    MEDIUM_THRESHOLD = 1.5
    
    def __init__(self):
        """
        Initialize TomTom provider with API credentials.
        
        Raises:
            ValueError: If TOMTOM_API_KEY is not found in environment
        """
        load_dotenv()
        self.api_key = os.getenv("TOMTOM_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "TOMTOM_API_KEY not found in environment. "
                "Please add it to your .env file."
            )
    
    def get_live_corridor_data(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float
    ) -> Dict:
        """
        Fetch live traffic data for a corridor between two points.
        
        Args:
            origin_lat: Origin latitude
            origin_lon: Origin longitude
            dest_lat: Destination latitude
            dest_lon: Destination longitude
            
        Returns:
            Dictionary containing:
                - distance_km: Route distance in kilometers
                - duration_min: Travel time with traffic in minutes
                - congestion_index: Traffic congestion ratio
                - congestion_level: LOW, MEDIUM, or HIGH
                - risk_score: Risk score (0-10)
                
        Raises:
            requests.RequestException: If API call fails
            ValueError: If response data is invalid
        """
        try:
            # Format coordinates for TomTom API
            origin = f"{origin_lat},{origin_lon}"
            destination = f"{dest_lat},{dest_lon}"
            
            # Construct API URL
            url = f"{self.BASE_URL}/{origin}:{destination}/json"
            
            # Query parameters
            params = {
                "key": self.api_key,
                "traffic": "true"
            }
            
            # Make API request
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            if "routes" not in data or len(data["routes"]) == 0:
                raise ValueError("No routes returned from TomTom API")
            
            # Extract route summary
            summary = data["routes"][0]["summary"]
            
            # Get key metrics
            travel_time_seconds = summary.get("travelTimeInSeconds", 0)
            no_traffic_time_seconds = summary.get("noTrafficTravelTimeInSeconds", 0)
            length_meters = summary.get("lengthInMeters", 0)
            traffic_delay_seconds = summary.get("trafficDelayInSeconds", 0)
            
            # Calculate metrics
            distance_km = length_meters / 1000.0
            duration_min = travel_time_seconds / 60.0
            
            # Compute congestion index
            # Use noTrafficTravelTime if available, otherwise estimate from distance
            if no_traffic_time_seconds > 0:
                congestion_index = travel_time_seconds / no_traffic_time_seconds
            elif traffic_delay_seconds >= 0:
                # Alternative: use traffic delay to estimate congestion
                no_traffic_estimate = travel_time_seconds - traffic_delay_seconds
                if no_traffic_estimate > 0:
                    congestion_index = travel_time_seconds / no_traffic_estimate
                else:
                    # Fallback: estimate free-flow time from distance (avg 60 km/h)
                    estimated_free_flow = (distance_km / 60.0) * 3600  # seconds
                    congestion_index = travel_time_seconds / max(estimated_free_flow, 1)
            else:
                # Fallback: estimate free-flow time from distance (avg 60 km/h)
                estimated_free_flow = (distance_km / 60.0) * 3600  # seconds
                congestion_index = travel_time_seconds / max(estimated_free_flow, 1)
            
            # Determine congestion level
            if congestion_index < self.LOW_THRESHOLD:
                congestion_level = "LOW"
            elif congestion_index < self.MEDIUM_THRESHOLD:
                congestion_level = "MEDIUM"
            else:
                congestion_level = "HIGH"
            
            # Calculate risk score (CI * 5, clamped to 10)
            risk_score = min(congestion_index * 5, 10.0)
            
            # Return structured data
            return {
                "distance_km": round(distance_km, 2),
                "duration_min": round(duration_min, 2),
                "congestion_index": round(congestion_index, 2),
                "congestion_level": congestion_level,
                "risk_score": round(risk_score, 2)
            }
            
        except requests.RequestException as e:
            raise requests.RequestException(
                f"TomTom API request failed: {str(e)}"
            )
        except (KeyError, ValueError) as e:
            raise ValueError(
                f"Failed to parse TomTom API response: {str(e)}"
            )
    
    def get_route_with_traffic(
        self,
        origin: str,
        destination: str
    ) -> Dict:
        """
        Convenience method to get traffic data using address strings.
        
        Note: This requires geocoding the addresses first.
        Use get_live_corridor_data() if you already have coordinates.
        
        Args:
            origin: Origin address string
            destination: Destination address string
            
        Returns:
            Same structure as get_live_corridor_data()
        """
        # This would require TomTom Geocoding API
        # For now, raise NotImplementedError
        raise NotImplementedError(
            "Address-based routing not yet implemented. "
            "Use get_live_corridor_data() with coordinates."
        )


if __name__ == "__main__":
    """
    Test the TomTom provider with sample Bangalore coordinates.
    
    Example route: Koramangala to MG Road, Bangalore
    """
    try:
        print("=" * 60)
        print("TomTom Traffic Provider - Test")
        print("=" * 60)
        
        # Initialize provider
        provider = TomTomProvider()
        print("✓ TomTom provider initialized")
        
        # Test coordinates (Bangalore)
        # Origin: Koramangala (approx)
        origin_lat, origin_lon = 12.9750, 77.6050
        # Destination: MG Road (approx)
        dest_lat, dest_lon = 12.9352, 77.6245
        
        print(f"\nFetching traffic data...")
        print(f"Origin: {origin_lat}, {origin_lon}")
        print(f"Destination: {dest_lat}, {dest_lon}\n")
        
        # Get live traffic data
        result = provider.get_live_corridor_data(
            origin_lat, origin_lon,
            dest_lat, dest_lon
        )
        
        # Display results
        print("=" * 60)
        print("LIVE TRAFFIC DATA")
        print("=" * 60)
        print(f"Distance:         {result['distance_km']} km")
        print(f"Duration:         {result['duration_min']} min")
        print(f"Congestion Index: {result['congestion_index']}")
        print(f"Congestion Level: {result['congestion_level']}")
        print(f"Risk Score:       {result['risk_score']}/10")
        print("=" * 60)
        
        # Structured output for debugging
        print(f"\nStructured output:")
        print(result)
        
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("\nMake sure TOMTOM_API_KEY is set in your .env file.")
    except requests.RequestException as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")
