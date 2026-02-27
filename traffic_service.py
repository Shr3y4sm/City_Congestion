"""
CityFlow AI - Traffic Service
A clean, production-ready service for fetching traffic routes using OpenRouteService API.
"""

import os
import requests
from typing import Tuple, Dict, List
from dotenv import load_dotenv


class TrafficService:
    """
    Service for geocoding addresses and fetching route information using OpenRouteService API.
    """
    
    GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
    DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
    
    def __init__(self):
        """Initialize the TrafficService and load API credentials."""
        load_dotenv()
        self.api_key = os.getenv("OPENROUTESERVICE_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENROUTESERVICE_API_KEY not found in environment variables")
        
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Cache to conserve API quota
        self._geocode_cache = {}
        self._route_cache = {}
    
    def geocode_address(self, address: str) -> Tuple[float, float]:
        """
        Convert an address string to geographic coordinates.
        
        Args:
            address: The address string to geocode
            
        Returns:
            Tuple of (latitude, longitude)
            
        Raises:
            ValueError: If the address cannot be geocoded
            requests.RequestException: If the API request fails
        """
        # Check cache first
        if address in self._geocode_cache:
            return self._geocode_cache[address]
        
        try:
            params = {
                "api_key": self.api_key,
                "text": address
            }
            
            response = requests.get(self.GEOCODE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("features"):
                raise ValueError(f"Address not found: {address}")
            
            # Extract coordinates from the first result
            coordinates = data["features"][0]["geometry"]["coordinates"]
            longitude, latitude = coordinates[0], coordinates[1]
            
            # Cache result
            self._geocode_cache[address] = (latitude, longitude)
            
            return latitude, longitude
            
        except requests.RequestException as e:
            raise Exception(f"Geocoding API error: {str(e)}")
    
    def get_routes(self, origin: str, destination: str) -> Dict:
        """
        Fetch route information between two addresses including up to 3 alternative routes.
        
        Args:
            origin: Starting address
            destination: Destination address
            
        Returns:
            Dictionary containing origin, destination, and list of routes with:
                - distance_km: Distance in kilometers
                - duration_min: Duration in minutes
                - geometry: Encoded polyline geometry
                
        Raises:
            ValueError: If addresses cannot be geocoded
            requests.RequestException: If the API request fails
        """
        # Check cache
        cache_key = f"{origin}|{destination}"
        if cache_key in self._route_cache:
            return self._route_cache[cache_key]
        
        try:
            # Geocode both addresses
            origin_lat, origin_lon = self.geocode_address(origin)
            dest_lat, dest_lon = self.geocode_address(destination)
            
            # Prepare directions request
            request_body = {
                "coordinates": [
                    [origin_lon, origin_lat],
                    [dest_lon, dest_lat]
                ],
                "alternative_routes": {
                    "target_count": 3
                }
            }
            
            # Make directions API request
            response = requests.post(
                self.DIRECTIONS_URL,
                json=request_body,
                headers=self.headers,
                timeout=10
            )
            
            # Provide detailed error info if request fails
            if not response.ok:
                error_detail = response.text
                raise Exception(f"Directions API error ({response.status_code}): {error_detail}")
            
            data = response.json()
            
            # Extract route information
            routes = self._extract_routes(data)
            
            result = {
                "origin": origin,
                "destination": destination,
                "routes": routes
            }
            
            # Cache result
            self._route_cache[cache_key] = result
            
            return result
            
        except requests.RequestException as e:
            raise Exception(f"Directions API error: {str(e)}")
    
    def _extract_routes(self, data: Dict) -> List[Dict]:
        """
        Extract and format route information from API response.
        
        Args:
            data: Raw API response data
            
        Returns:
            List of formatted route dictionaries
        """
        routes = []
        
        for route in data.get("routes", []):
            summary = route.get("summary", {})
            
            # Convert meters to kilometers
            distance_km = round(summary.get("distance", 0) / 1000, 2)
            
            # Convert seconds to minutes
            duration_min = round(summary.get("duration", 0) / 60, 2)
            
            # Get encoded polyline geometry
            geometry = route.get("geometry", "")
            
            routes.append({
                "distance_km": distance_km,
                "duration_min": duration_min,
                "geometry": geometry
            })
        
        return routes


if __name__ == "__main__":
    """Test the TrafficService with a sample query."""
    try:
        service = TrafficService()
        print("CityFlow AI - Traffic Service Demo\n")
        print("Fetching routes in Bangalore...\n")
        
        result = service.get_routes(
            "MG Road, Bangalore",
            "Koramangala, Bangalore"
        )
        
        print(f"Origin: {result['origin']}")
        print(f"Destination: {result['destination']}")
        print(f"\nFound {len(result['routes'])} route(s):\n")
        
        for idx, route in enumerate(result['routes'], 1):
            print(f"Route {idx}:")
            print(f"  Distance: {route['distance_km']} km")
            print(f"  Duration: {route['duration_min']} minutes")
            print(f"  Geometry: {route['geometry'][:50]}...\n")
            
    except Exception as e:
        print(f"Error: {str(e)}")
