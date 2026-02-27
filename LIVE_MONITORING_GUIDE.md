# Live Monitoring Feature - Quick Start Guide

## Overview

The **Live Monitoring** tab in Authority Dashboard provides real-time traffic updates for specific corridors using WebSocket connectivity.

---

## How It Works

### Architecture

```
Authority Dashboard (Streamlit)
        ↓
    REST API (FastAPI)
        ↓
    START monitoring
        ↓
    WebSocket Connection
        ↓
    Background Thread (asyncio)
        ↓
    Queue → session_state
        ↓
    Auto-refresh UI
```

### Components

1. **REST API Calls** - Start/stop monitoring via `requests`
2. **WebSocket Listener** - Background thread with asyncio event loop
3. **Queue Communication** - Thread-safe data passing
4. **Session State** - Persistent data storage across reruns
5. **Auto-refresh** - UI updates every 2-3 seconds to check for new data

---

## Usage Instructions

### Step 1: Start the Live Traffic Service

First, ensure the FastAPI service is running:

```bash
# Terminal 1
python api/live_stream.py
```

Wait for: `Uvicorn running on http://0.0.0.0:8000`

### Step 2: Launch Authority Dashboard

```bash
# Terminal 2
streamlit run authority_dashboard.py
```

### Step 3: Navigate to Live Monitoring Tab

Click on the **"Live Monitoring"** tab (third tab)

### Step 4: Configure Route

- **Origin**: Enter starting location (e.g., "Koramangala, Bangalore")
- **Destination**: Enter destination (e.g., "MG Road, Bangalore")

### Step 5: Start Monitoring

Click **"Start Monitoring"** button

The system will:
1. Call REST API to start monitoring
2. Connect WebSocket in background thread
3. Begin receiving updates every 20 seconds
4. Auto-refresh display

### Step 6: View Live Data

The dashboard displays:

- **Alert Banner**: Red alert if congestion > 1.5, green for stable
- **Route Info**: Origin → Destination with timestamp
- **Metrics**: 
  - Congestion Index
  - Risk Score (0-10)
  - Distance (km)
  - Duration (min)
- **Congestion Level Badge**: Color-coded (HIGH/MEDIUM/LOW)

### Step 7: Stop Monitoring

Click **"Stop Monitoring"** to end the session

---

## Features

### 1. Alert System

```python
if alert == True:
    🚨 CONGESTION ALERT – Immediate Action Required
else:
    ✅ Traffic Flow Stable
```

### 2. Real-Time Metrics

- **Congestion Index**: Actual/Expected duration ratio
- **Risk Score**: CI × 5 (clamped to 10)
- **Distance**: Route distance in km
- **Duration**: Current travel time

### 3. Color-Coded Levels

| Level | Color | Criteria |
|-------|-------|----------|
| **LOW** | Green | CI < 1.2 |
| **MEDIUM** | Yellow | 1.2 ≤ CI < 1.5 |
| **HIGH** | Red | CI ≥ 1.5 |

### 4. Auto-Refresh

- UI refreshes every 2-3 seconds
- Checks queue for new WebSocket data
- Non-blocking updates

### 5. Connection Status

- ✅ Connected to Live Monitor (green)
- ⏳ Connecting... (yellow)
- Disconnected (when stopped)

---

## Technical Implementation

### WebSocket Handler

```python
async def _ws_listener(data_queue: Queue):
    """Runs in background thread with asyncio event loop"""
    async with websockets.connect(WS_URL) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            data_queue.put(data)  # Thread-safe queue
```

### Threading Integration

```python
# Start background thread
ws_thread = threading.Thread(
    target=_run_ws_listener,
    args=(data_queue,),
    daemon=True
)
ws_thread.start()
```

### Session State Management

```python
# Initialize
st.session_state.live_monitoring_active = False
st.session_state.live_data = None
st.session_state.data_queue = None
st.session_state.ws_connected = False

# Update
while not data_queue.empty():
    data = data_queue.get_nowait()
    st.session_state.live_data = data
```

### Auto-Refresh Logic

```python
if live_monitoring_active:
    # Display data
    if live_data:
        # Show metrics
        pass
    
    # Trigger rerun after delay
    time.sleep(2)
    st.rerun()
```

---

## Troubleshooting

### Issue: "Failed to start monitoring"

**Cause**: FastAPI service not running

**Solution**:
```bash
python api/live_stream.py
```

### Issue: WebSocket won't connect

**Cause**: Service running on different port or firewall

**Solution**:
- Check service is at `http://localhost:8000`
- Verify firewall allows connections
- Check terminal for API errors

### Issue: No updates received

**Cause**: Monitoring not started or API quota exceeded

**Solution**:
- Check API console for errors
- Verify OpenRouteService API key in `.env`
- Check status endpoint: `http://localhost:8000/status`

### Issue: UI not refreshing

**Cause**: Auto-refresh disabled or error in WebSocket thread

**Solution**:
- Check browser console for errors
- Restart dashboard
- Check terminal output for Python errors

---

## Testing Scenarios

### Test 1: Basic Flow

1. Start service
2. Launch dashboard
3. Enter "Koramangala" → "MG Road"
4. Click Start
5. Wait 20 seconds for first update
6. Verify metrics display
7. Click Stop

**Expected**: Smooth start, live updates, clean stop

### Test 2: High Congestion Alert

1. Monitor a busy route during peak hours
2. Wait for CI > 1.5
3. Verify red alert banner appears

**Expected**: Alert triggers, banner shows warning

### Test 3: Multiple Routes

1. Start monitoring route A
2. Stop monitoring
3. Start monitoring route B

**Expected**: Clean transition, no stale data

### Test 4: Connection Loss

1. Start monitoring
2. Stop FastAPI service
3. Observe dashboard behavior

**Expected**: Error message, graceful handling

---

## Performance Notes

- **Polling Interval**: 20 seconds (configurable in API)
- **UI Refresh**: 2-3 seconds (prevents excessive reruns)
- **Memory**: ~5KB per update (retained in session_state)
- **Thread Overhead**: Minimal (single daemon thread)

---

## Configuration

### Change API Endpoint

Edit in `authority_dashboard.py`:

```python
API_BASE = "http://localhost:8000"  # Change port if needed
WS_URL = "ws://localhost:8000/ws/live-monitor"
```

### Adjust Refresh Rate

```python
# In Live Monitoring tab
time.sleep(2)  # Change to desired seconds
st.rerun()
```

### Modify Alert Threshold

Edit in `api/live_stream.py`:

```python
alert = congestion_index > 1.5  # Change threshold
```

---

## API Integration

### Start Monitoring

```python
response = requests.post(
    "http://localhost:8000/start-monitoring",
    json={"origin": "...", "destination": "..."}
)
```

### Stop Monitoring

```python
response = requests.post(
    "http://localhost:8000/stop-monitoring"
)
```

### WebSocket Connection

```python
async with websockets.connect("ws://localhost:8000/ws/live-monitor") as ws:
    async for message in ws:
        data = json.loads(message)
        # Process data
```

---

## Security Considerations

1. **Local Only**: Currently runs on localhost
2. **No Auth**: No authentication implemented
3. **CORS**: Enabled for all origins in API

For production:
- Add authentication
- Restrict CORS origins
- Use HTTPS/WSS
- Implement rate limiting

---

## Future Enhancements

Potential improvements:
- [ ] Multi-corridor monitoring (parallel routes)
- [ ] Historical data chart (line graph)
- [ ] Export data to CSV
- [ ] Email/SMS alerts for high congestion
- [ ] Map view with live route overlay
- [ ] Predictive alerts (ML-based)

---

## Related Files

- `authority_dashboard.py` - Main dashboard with Live Monitoring tab
- `api/live_stream.py` - FastAPI WebSocket service
- `api/test_client.py` - Python test client
- `api/test_dashboard.html` - Web test dashboard

---

## Support

**Check Service Status**:
```bash
curl http://localhost:8000/status
```

**View API Docs**:
```
http://localhost:8000/docs
```

**Test WebSocket**:
```bash
pip install websocat
websocat ws://localhost:8000/ws/live-monitor
```

---

**Built for CityFlow AI Hackathon - Authority Command Center**
