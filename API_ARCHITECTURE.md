# API Architecture Overview

## Service Separation: Mappls vs OpenRouteService

```
┌─────────────────────────────────────────────────────────────┐
│                    CityFlow AI System                        │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
         ┌──────▼──────┐         ┌─────▼──────┐
         │  Mappls API │         │ OpenRoute  │
         │  (Indian)   │         │  Service   │
         └──────┬──────┘         └─────┬──────┘
                │                      │
                │                      │
    ┌───────────▼────────┐  ┌─────────▼──────────┐
    │  Live Monitoring   │  │  Dashboard & Demo  │
    │  api/live_stream   │  │  dashboard.py      │
    │                    │  │  demo.py           │
    │  ✓ Real-time       │  │                    │
    │  ✓ WebSocket       │  │  ✓ Route Analysis  │
    │  ✓ 20s updates     │  │  ✓ ML Prediction   │
    │  ✓ Indian traffic  │  │  ✓ Policy Simulator│
    └────────────────────┘  └────────────────────┘
```

---

## File-by-File Breakdown

### Using **Mappls API** 🇮🇳

#### ✅ api/live_stream.py
- **Purpose**: Real-time traffic monitoring
- **Why Mappls**: Live Indian traffic data
- **Frequency**: Every 20 seconds
- **Data**: Real-time duration with traffic

```python
# Uses MappIsTrafficService
class MonitoringState:
    def __init__(self):
        self.traffic_service = MappIsTrafficService()  # ← Mappls
```

---

### Using **OpenRouteService** 🌍

#### ✅ traffic_service.py
- **Purpose**: General traffic data provider
- **Used by**: dashboard.py, demo.py
- **Why ORS**: Global coverage, stable API
- **Data**: Distance, duration (no real-time traffic)

```python
# Original TrafficService class
class TrafficService:
    DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
```

#### ✅ dashboard.py
- **Purpose**: User-facing route optimizer
- **API**: OpenRouteService (via TrafficService)
- **Features**: 
  - Route comparison
  - 30-min ML forecast
  - Environmental metrics
  - Policy simulator

```python
from traffic_service import TrafficService  # ← OpenRouteService
```

#### ✅ demo.py
- **Purpose**: CLI demonstration
- **API**: OpenRouteService (via TrafficService)
- **Features**:
  - Console route analysis
  - Formatted output

```python
from traffic_service import TrafficService  # ← OpenRouteService
```

#### ✅ authority_dashboard.py
- **Purpose**: Authority command center
- **API**: 
  - **Live Monitoring Tab**: Mappls (via api/live_stream.py)
  - **Other Tabs**: Mock data + OpenRouteService
- **Features**:
  - Live WebSocket updates
  - City-wide analytics
  - Policy impact analysis

```python
# Live tab connects to api/live_stream.py (Mappls)
# Other features use mock data or ORS
```

---

## API Configuration

### .env File Structure

```env
# OpenRouteService (for dashboard, demo)
OPENROUTESERVICE_API_KEY=your_ors_key_here

# Mappls API (for live monitoring only)
MAPPLS_API_KEY=your_mappls_key_here
```

---

## Data Flow Comparison

### 🔴 Live Monitoring (Mappls)

```
User clicks "Start Monitoring"
         ↓
Authority Dashboard (Streamlit)
         ↓
POST /start-monitoring → api/live_stream.py
         ↓
Background async loop (every 20s)
         ↓
MappIsTrafficService.get_routes()
         ↓
Mappls API Request
https://apis.mappls.com/advancedmaps/v1/{key}/route_adv/...
         ↓
Real-time traffic data
{distance: 8500m, duration: 1410s (23.5 min with traffic)}
         ↓
CongestionEngine.analyze_routes()
         ↓
WebSocket broadcast
         ↓
Dashboard displays metrics
```

### 🔵 Dashboard/Demo (OpenRouteService)

```
User enters origin/destination
         ↓
Dashboard/Demo (Streamlit/CLI)
         ↓
TrafficService.get_routes()
         ↓
OpenRouteService API Request
https://api.openrouteservice.org/v2/directions/driving-car
         ↓
Basic route data (no real-time traffic)
{distance: 8500m, duration: 900s (15 min baseline)}
         ↓
CongestionEngine.analyze_routes()
         ↓
Display results
```

---

## Why This Split?

### Mappls for Live Monitoring ✅

**Advantages**:
- ✅ Real-time Indian traffic conditions
- ✅ Better accuracy for Bangalore/Indian cities
- ✅ Traffic-aware routing
- ✅ Higher API limits (10k/day)

**Use Case**:
- Authority dashboard needs live updates
- Real-time alerts for congestion
- Monitoring specific corridors continuously

### OpenRouteService for Everything Else ✅

**Advantages**:
- ✅ Already implemented and stable
- ✅ Global coverage
- ✅ Consistent with existing codebase
- ✅ No need to change working features

**Use Case**:
- Route analysis and comparison
- ML predictions
- Environmental calculations
- One-time queries

---

## Testing Both APIs

### Test Mappls API (Live Monitoring)

```bash
# Terminal 1: Start API service
python api/live_stream.py
# Should see: [INIT] Live monitoring using Mappls API for real-time traffic

# Terminal 2: Start Authority Dashboard
streamlit run authority_dashboard.py

# In browser:
# 1. Go to "Live Monitoring" tab
# 2. Enter: Koramangala → MG Road
# 3. Click "Start Monitoring"
# 4. Wait 20 seconds for Mappls data
```

Console output:
```
[MAPPLS] Successfully fetched 1 route(s) with live traffic
Duration: 23.5 min (with real-time traffic)
CI: 1.67 (HIGH)
```

### Test OpenRouteService (Dashboard)

```bash
# Start user dashboard
streamlit run dashboard.py

# In browser:
# 1. Enter: Koramangala → MG Road  
# 2. Click "Analyze Routes"
# 3. See 3 routes with basic data
```

Console output:
```
Fetching routes from OpenRouteService...
Duration: 15 min (baseline, no traffic)
CI: 1.25 (MEDIUM)
```

---

## API Usage Summary

| Component | API | Key in .env | Updates | Traffic Data |
|-----------|-----|-------------|---------|--------------|
| **api/live_stream.py** | Mappls | MAPPLS_API_KEY | Every 20s | ✅ Real-time |
| **dashboard.py** | OpenRouteService | OPENROUTESERVICE_API_KEY | On-demand | ❌ Baseline |
| **demo.py** | OpenRouteService | OPENROUTESERVICE_API_KEY | On-demand | ❌ Baseline |
| **authority_dashboard.py** (Live tab) | Mappls (via API) | MAPPLS_API_KEY | Every 20s | ✅ Real-time |
| **authority_dashboard.py** (Other tabs) | Mock data | N/A | Static | 📊 Simulated |

---

## Migration Notes

### ✅ What Changed
- `api/live_stream.py` now uses `MappIsTrafficService` instead of `TrafficService`
- Added `MAPPLS_API_KEY` to `.env`
- Live monitoring gets real Indian traffic data

### ✅ What Stayed the Same
- `dashboard.py` still uses OpenRouteService
- `demo.py` still uses OpenRouteService
- `traffic_service.py` unchanged
- All other modules work as before

### ✅ Backward Compatibility
- If `MAPPLS_API_KEY` is missing, system falls back to simulated data
- No breaking changes to existing features
- OpenRouteService features continue working

---

## Quick Start

### 1. Get Both API Keys

**OpenRouteService** (existing):
- Already have: Check `.env`
- If not: https://openrouteservice.org/dev/#/signup

**Mappls** (new):
- Sign up: https://apis.mappls.com/console/
- Get REST API key
- Free tier: 10,000 requests/day

### 2. Update .env

```env
OPENROUTESERVICE_API_KEY=your_existing_ors_key
MAPPLS_API_KEY=your_new_mappls_key
```

### 3. Test

```bash
# Test live monitoring (Mappls)
python api/live_stream.py

# Test dashboard (OpenRouteService)
streamlit run dashboard.py
```

---

## Cost Analysis

### Free Tier Limits

| API | Requests/Day | Sufficient For |
|-----|--------------|----------------|
| **Mappls** | 10,000 | ✅ Live monitoring (4,320/day at 20s intervals) |
| **OpenRouteService** | 2,000 | ✅ Dashboard queries (typically <100/day) |

### Usage Breakdown

**Live Monitoring** (20-second updates):
- 3 updates/minute
- 180 updates/hour
- 4,320 updates/day (if running 24/7)
- **Mappls Free Tier**: ✅ Supports this

**Dashboard** (on-demand):
- ~10-50 queries per demo session
- Multiple sessions possible
- **ORS Free Tier**: ✅ Plenty of headroom

---

## Best Practices

### ✅ DO:
- Use Mappls for live, continuous monitoring
- Use OpenRouteService for one-time route analysis
- Monitor API usage in respective consoles
- Cache geocoding results (already implemented)

### ❌ DON'T:
- Use OpenRouteService for real-time traffic (doesn't provide it)
- Exceed free tier limits during demos
- Commit API keys to Git (use .env)
- Mix APIs within same service (keep separate)

---

## Future Enhancements

### Potential Improvements:
- [ ] Add Google Maps API as third option
- [ ] Implement automatic API failover
- [ ] Add API usage monitoring dashboard
- [ ] Cache traffic patterns for ML training
- [ ] Support multiple live corridors (Mappls)

---

**You now have the best of both worlds: Real-time Indian traffic (Mappls) + Global coverage (OpenRouteService)!** 🎉
