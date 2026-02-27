"""
CityFlow AI - Live Traffic Monitoring Service
==============================================
Production-ready FastAPI service for real-time traffic monitoring.

Features:
- REST endpoint to start monitoring a corridor
- WebSocket broadcasting for live updates
- Background polling every 20 seconds
- Congestion analysis and alerting
- Graceful connection management
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Set, Dict
import traceback
import requests
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from traffic_service import TrafficService
from services.congestion_engine import CongestionEngine


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class MonitoringRequest(BaseModel):
    """Request body for starting traffic monitoring"""
    origin: str
    destination: str


class TrafficUpdate(BaseModel):
    """Real-time traffic update data structure"""
    timestamp: str
    origin: str
    destination: str
    distance_km: float
    duration_min: float
    congestion_index: float
    congestion_level: str
    risk_score: float
    alert: bool


# ============================================================================
# LIFESPAN HANDLER
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    print("[STARTUP] Application starting...")
    yield
    # Shutdown
    print("[SHUTDOWN] Stopping monitoring and closing connections...")
    state.stop_monitoring()
    
    # Close all WebSocket connections
    for connection in list(state.active_connections):
        try:
            await connection.close()
        except:
            pass


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="CityFlow AI - Live Traffic Monitor",
    description="Real-time traffic monitoring and alerting service",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# MAPPLS TRAFFIC SERVICE (for Live Monitoring only)
# ============================================================================

class MappIsTrafficService:
    """Traffic service using Mappls API for real-time Indian traffic data"""
    
    def __init__(self):
        self.api_key = os.getenv("MAPPLS_API_KEY")
        if not self.api_key:
            print("[WARNING] MAPPLS_API_KEY not found in .env. Using fallback mode.")
        
        self.GEOCODE_URL = "https://apis.mappls.com/advancedmaps/v1/{}/geo_code"
        self.ROUTE_URL = "https://apis.mappls.com/advancedmaps/v1/{}/route_adv/driving/{};{}"
        
        # Cache for geocoding results
        self._geocode_cache = {}
    
    def geocode_address(self, address: str) -> tuple:
        """Geocode address using Mappls API"""
        if address in self._geocode_cache:
            return self._geocode_cache[address]
        
        if not self.api_key:
            # Fallback to hardcoded Bangalore coordinates
            fallback_coords = {
                "koramangala": (12.9352, 77.6245),
                "mg road": (12.9716, 77.6412),
                "whitefield": (12.9698, 77.7499),
                "electronic city": (12.8387, 77.6873),
            }
            
            for key, coords in fallback_coords.items():
                if key in address.lower():
                    self._geocode_cache[address] = coords
                    return coords
            
            # Default to central Bangalore
            coords = (12.9716, 77.5946)
            self._geocode_cache[address] = coords
            return coords
        
        try:
            url = self.GEOCODE_URL.format(self.api_key)
            params = {"address": address}
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.ok:
                data = response.json()
                if "copResults" in data and len(data["copResults"]) > 0:
                    result = data["copResults"][0]
                    lat = float(result["latitude"])
                    lon = float(result["longitude"])
                    coords = (lat, lon)
                    self._geocode_cache[address] = coords
                    return coords
        
        except Exception as e:
            print(f"[MAPPLS] Geocoding error: {e}")
        
        # Fallback
        coords = (12.9716, 77.5946)
        self._geocode_cache[address] = coords
        return coords
    
    def get_routes(self, origin: str, destination: str) -> Dict:
        """Fetch routes with real-time traffic from Mappls API"""
        try:
            # Geocode addresses
            origin_lat, origin_lon = self.geocode_address(origin)
            dest_lat, dest_lon = self.geocode_address(destination)
            
            if not self.api_key:
                # Return mock data with realistic Indian traffic
                import random
                base_distance = 8.5  # km
                base_duration = 15   # minutes base
                
                # Add traffic variability
                current_hour = datetime.now().hour
                if 7 <= current_hour < 10 or 17 <= current_hour < 20:
                    traffic_multiplier = random.uniform(1.5, 2.5)  # Peak hours
                else:
                    traffic_multiplier = random.uniform(0.9, 1.3)   # Off-peak
                
                routes = [
                    {
                        "distance_km": base_distance,  # kilometers
                        "duration_min": base_duration * traffic_multiplier,  # minutes
                        "geometry": "mock_geometry"
                    }
                ]
                
                print(f"[MAPPLS FALLBACK] Generated traffic data: {base_duration}min -> {base_duration * traffic_multiplier:.1f}min")
                
                return {
                    "origin": origin,
                    "destination": destination,
                    "routes": routes
                }
            
            # Use Mappls API
            origin_coord = f"{origin_lat},{origin_lon}"
            dest_coord = f"{dest_lat},{dest_lon}"
            
            url = self.ROUTE_URL.format(self.api_key, origin_coord, dest_coord)
            params = {
                "rtype": "0",  # 0 = optimal, 1 = shortest
                "region": "IND"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.ok:
                data = response.json()
                routes = []
                
                if "routes" in data and len(data["routes"]) > 0:
                    for route in data["routes"]:
                        distance_m = int(route.get("distance", 0))
                        duration_s = int(route.get("duration", 0))
                        routes.append({
                            "distance_km": distance_m / 1000.0,  # Convert meters to km
                            "duration_min": duration_s / 60.0,  # Convert seconds to minutes
                            "geometry": route.get("geometry", "")
                        })
                
                print(f"[MAPPLS] Successfully fetched {len(routes)} route(s) with live traffic")
                
                return {
                    "origin": origin,
                    "destination": destination,
                    "routes": routes if routes else self._fallback_routes()
                }
            
            else:
                print(f"[MAPPLS] API error: {response.status_code}")
                return self._fallback_routes()
        
        except Exception as e:
            print(f"[MAPPLS] Error: {e}")
            return self._fallback_routes()
    
    def _fallback_routes(self) -> Dict:
        """Generate fallback route data"""
        import random
        base_distance_km = 8.5  # kilometers
        base_duration_min = 15  # minutes
        
        current_hour = datetime.now().hour
        if 7 <= current_hour < 10 or 17 <= current_hour < 20:
            traffic_multiplier = random.uniform(1.5, 2.5)
        else:
            traffic_multiplier = random.uniform(0.9, 1.3)
        
        return {
            "origin": "Unknown",
            "destination": "Unknown",
            "routes": [{
                "distance_km": base_distance_km,
                "duration_min": base_duration_min * traffic_multiplier,
                "geometry": "fallback"
            }]
        }


# ============================================================================
# GLOBAL STATE
# ============================================================================

class MonitoringState:
    """Manages monitoring state and WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring: bool = False
        self.current_origin: Optional[str] = None
        self.current_destination: Optional[str] = None
        
        # Initialize services
        # Use Mappls API for live monitoring (better Indian traffic data)
        self.traffic_service = MappIsTrafficService()
        self.congestion_engine = CongestionEngine()
        
        print("[INIT] Live monitoring using Mappls API for real-time traffic")
    
    async def connect(self, websocket: WebSocket):
        """Add new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)
    
    async def broadcast(self, data: dict):
        """Send data to all connected clients"""
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                print(f"[ERROR] Failed to send to client: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    def start_monitoring(self, origin: str, destination: str):
        """Start background monitoring task"""
        if self.is_monitoring:
            raise HTTPException(
                status_code=400,
                detail="Monitoring already active. Stop current monitoring first."
            )
        
        self.current_origin = origin
        self.current_destination = destination
        self.is_monitoring = True
        
        # Create background task
        self.monitoring_task = asyncio.create_task(
            self._monitoring_loop()
        )
    
    def stop_monitoring(self):
        """Stop background monitoring task"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            self.monitoring_task = None
        
        self.current_origin = None
        self.current_destination = None
    
    async def _monitoring_loop(self):
        """Background task that polls traffic data every 20 seconds"""
        print(f"[MONITOR] Started monitoring: {self.current_origin} -> {self.current_destination}")
        
        while self.is_monitoring:
            try:
                # Get traffic data
                update = await self._fetch_traffic_update()
                
                # Broadcast to all connected clients
                if update:
                    await self.broadcast(update.model_dump())
                    
                    # Log alerts
                    if update.alert:
                        print(f"[ALERT] High congestion detected! CI={update.congestion_index:.2f}")
                
                # Wait 20 seconds before next poll
                await asyncio.sleep(20)
                
            except asyncio.CancelledError:
                print("[MONITOR] Monitoring stopped")
                break
            except Exception as e:
                print(f"[ERROR] Monitoring loop error: {e}")
                traceback.print_exc()
                await asyncio.sleep(20)  # Continue despite errors
    
    async def _fetch_traffic_update(self) -> Optional[TrafficUpdate]:
        """Fetch current traffic data and compute congestion metrics"""
        try:
            # Get routes from traffic service (runs in thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            routes = await loop.run_in_executor(
                None,
                self.traffic_service.get_routes,
                self.current_origin,
                self.current_destination
            )
            
            if not routes or len(routes) == 0:
                print("[WARNING] No routes returned from API")
                return None
            
            # Analyze congestion for all routes
            analyzed = self.congestion_engine.analyze_routes(routes)
            
            if not analyzed or len(analyzed) == 0:
                print("[WARNING] No routes after congestion analysis")
                return None
            
            # Use the best route from analyzed results
            best_route_idx = analyzed['best_route_index']
            best_route = analyzed['routes'][best_route_idx]
            
            # Extract metrics (already in correct units)
            distance_km = best_route['distance_km']
            duration_min = best_route['duration_min']
            congestion_index = best_route['congestion_index']
            congestion_level = best_route['congestion_level']
            
            # Calculate risk score (CI * 5, clamped to 10)
            risk_score = min(congestion_index * 5, 10.0)
            
            # Trigger alert if congestion is high
            alert = congestion_index > 1.5
            
            # Create update object
            update = TrafficUpdate(
                timestamp=datetime.now().isoformat(),
                origin=self.current_origin,
                destination=self.current_destination,
                distance_km=round(distance_km, 2),
                duration_min=round(duration_min, 2),
                congestion_index=round(congestion_index, 2),
                congestion_level=congestion_level,
                risk_score=round(risk_score, 2),
                alert=alert
            )
            
            return update
            
        except Exception as e:
            print(f"[ERROR] Failed to fetch traffic update: {e}")
            traceback.print_exc()
            return None


# Global state instance
state = MonitoringState()


# ============================================================================
# REST ENDPOINTS
# ============================================================================

@app.post("/start-monitoring")
async def start_monitoring(request: MonitoringRequest):
    """
    Start monitoring a traffic corridor.
    Only one monitoring session allowed at a time.
    """
    try:
        state.start_monitoring(request.origin, request.destination)
        
        return {
            "status": "success",
            "message": "Monitoring started",
            "origin": request.origin,
            "destination": request.destination,
            "poll_interval_seconds": 20
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")


@app.post("/stop-monitoring")
async def stop_monitoring():
    """Stop the active monitoring session"""
    if not state.is_monitoring:
        raise HTTPException(status_code=400, detail="No active monitoring session")
    
    state.stop_monitoring()
    
    return {
        "status": "success",
        "message": "Monitoring stopped"
    }


@app.get("/status")
async def get_status():
    """Get current monitoring status"""
    return {
        "is_monitoring": state.is_monitoring,
        "origin": state.current_origin,
        "destination": state.current_destination,
        "connected_clients": len(state.active_connections)
    }


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "CityFlow AI - Live Traffic Monitor",
        "status": "operational",
        "version": "1.0.0"
    }


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/live-monitor")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for receiving live traffic updates.
    Automatically receives broadcasts when monitoring is active.
    """
    await state.connect(websocket)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to CityFlow AI Live Monitor",
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and listen for client messages
        while True:
            # Wait for any message from client (keeps connection alive)
            data = await websocket.receive_text()
            
            # Echo back or handle commands if needed
            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        print("[WS] Client disconnected")
        state.disconnect(websocket)
    
    except Exception as e:
        print(f"[WS] Error: {e}")
        state.disconnect(websocket)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("CityFlow AI - Live Traffic Monitoring Service")
    print("=" * 60)
    print("\nStarting server...")
    print("API Docs: http://localhost:8000/docs")
    print("WebSocket: ws://localhost:8000/ws/live-monitor")
    print("\nPress CTRL+C to stop")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
