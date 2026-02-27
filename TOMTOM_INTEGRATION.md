# TomTom Traffic Integration Guide

## Overview

CityFlow AI now supports **TomTom Traffic API** for real-time traffic data with automatic provider selection.

## Features

- ✅ Real-time traffic data from TomTom's global network
- ✅ Automatic congestion index calculation
- ✅ Geocoding support for address-based routing
- ✅ Seamless fallback to mock data if API key missing
- ✅ Production-ready error handling

## Provider Selection Logic

The system automatically selects the best provider:

```
Priority:
1. TomTom (if TOMTOM_API_KEY is set)
2. Mappls (if MAPPLS_API_KEY is set)
3. Fallback mode (simulated data)
```

## API Credentials

### Your Current Setup:
```env
TOMTOM_API_KEY=c573sBS8yJhoTw0D3rSem80RQx5SxtCB  ✓ Active
MAPPLS_API_KEY=0247858b171e495cec0a98bb8a9f5309
```

**Current Provider:** TomTom (auto-selected)

## Testing TomTom Provider

### Standalone Test:
```bash
python services/tomtom_provider.py
```

Expected output:
```
============================================================
LIVE TRAFFIC DATA
============================================================
Distance:         6.78 km
Duration:         26.12 min
Congestion Index: 1.02
Congestion Level: LOW
Risk Score:       5.11/10
============================================================
```

### Full System Test:

**Terminal 1:** Start API service
```bash
python api/live_stream.py
```

**Terminal 2:** Start monitoring
```bash
curl -X POST http://localhost:8000/start-monitoring \
  -H "Content-Type: application/json" \
  -d '{"origin":"Koramangala, Bangalore","destination":"MG Road, Bangalore"}'
```

**Terminal 3:** Watch live data
```bash
python watch_traffic.py
```

## Congestion Calculation

TomTom provides both actual and free-flow travel times:

```python
Congestion Index = travelTimeInSeconds / noTrafficTravelTimeInSeconds

Levels:
  < 1.2  →  LOW     (Green)
  1.2-1.5  →  MEDIUM  (Yellow)
  ≥ 1.5  →  HIGH    (Red)

Risk Score = Congestion Index × 5 (max 10)
```

## API Endpoints

### Check Active Provider:
```bash
curl http://localhost:8000/
```

Response:
```json
{
  "service": "CityFlow AI - Live Traffic Monitor",
  "status": "operational",
  "version": "1.0.0",
  "traffic_provider": "TomTom"
}
```

### Get Monitoring Status:
```bash
curl http://localhost:8000/status
```

Response:
```json
{
  "is_monitoring": true,
  "origin": "Koramangala, Bangalore",
  "destination": "MG Road, Bangalore",
  "connected_clients": 1,
  "provider": "TomTom"
}
```

## Switching Providers

### Force Mappls:
Remove or comment out `TOMTOM_API_KEY` in `.env`:
```env
# TOMTOM_API_KEY=...
MAPPLS_API_KEY=0247858b171e495cec0a98bb8a9f5309
```

### Force TomTom:
Ensure `TOMTOM_API_KEY` is set (already configured):
```env
TOMTOM_API_KEY=c573sBS8yJhoTw0D3rSem80RQx5SxtCB
```

Restart the service to apply changes.

## Comparison: TomTom vs Mappls

| Feature | TomTom | Mappls |
|---------|--------|--------|
| **Coverage** | Global | India-focused |
| **Traffic Accuracy** | Enterprise-grade | Local expertise |
| **Geocoding** | Built-in | Built-in |
| **No-Traffic Time** | ✓ Provided | ✗ Estimated |
| **API Limits** | Generous free tier | Limited free tier |
| **Best For** | Global routes | Indian cities |

## TomTom API Details

**Routing Endpoint:**
```
GET https://api.tomtom.com/routing/1/calculateRoute/{origin}:{destination}/json
```

**Parameters:**
- `key` - Your API key
- `traffic` - Set to "true" for live traffic

**Response Fields:**
```json
{
  "routes": [{
    "summary": {
      "lengthInMeters": 6780,
      "travelTimeInSeconds": 1567,
      "noTrafficTravelTimeInSeconds": 1534,
      "trafficDelayInSeconds": 33
    }
  }]
}
```

## Production Deployment

### Environment Variables:
```env
TOMTOM_API_KEY=your_production_key
MAPPLS_API_KEY=your_backup_key
```

### Docker:
```dockerfile
ENV TOMTOM_API_KEY=${TOMTOM_API_KEY}
ENV MAPPLS_API_KEY=${MAPPLS_API_KEY}
```

### Rate Limiting:
TomTom free tier: 2,500 requests/day
Consider implementing request caching for production.

## Troubleshooting

### Issue: "TOMTOM_API_KEY not found"
**Solution:** Add key to `.env` file and restart service.

### Issue: "No routes returned"
**Solution:** Check coordinates are valid or try different addresses.

### Issue: Service uses Mappls instead of TomTom
**Solution:** Verify `TOMTOM_API_KEY` is set and restart service.

## Next Steps

1. ✓ TomTom provider implemented
2. ✓ Auto-detection configured
3. ✓ Service running with TomTom
4. 🎯 Test with your dashboard
5. 🎯 Compare results with Mappls

## Support

For issues or questions:
- Check service status: `curl http://localhost:8000/status`
- View logs: Check terminal output from `api/live_stream.py`
- Test provider: `python services/tomtom_provider.py`
