# Mappls API Setup Guide for Live Monitoring

## Overview

The **Live Monitoring** feature now uses **Mappls API** (formerly MapmyIndia) for real-time traffic data in India, while other features continue using **OpenRouteService**.

### Why Mappls?
- ✅ **Better Indian Traffic Data**: Mappls specializes in Indian maps and traffic
- ✅ **Real-time Updates**: Accurate traffic conditions for Bangalore and other Indian cities
- ✅ **Higher Accuracy**: More precise routing for Indian road networks

---

## API Usage Split

| Feature | Service | API Used | Reason |
|---------|---------|----------|---------|
| **Live Monitoring** | `api/live_stream.py` | **Mappls API** | Real-time Indian traffic |
| **Dashboard** | `dashboard.py` | **OpenRouteService** | Global coverage |
| **Demo** | `demo.py` | **OpenRouteService** | Consistent with dashboard |
| **Authority Dashboard** | `authority_dashboard.py` | **OpenRouteService** | Mock data + ORS |

---

## Getting Your Mappls API Key

### Step 1: Create Mappls Account

1. Visit: **https://apis.mappls.com/console/**
2. Click **"Sign Up"** or **"Register"**
3. Fill in your details:
   - Name
   - Email
   - Mobile number
   - Company/Organization (can use "Personal Project")
4. Verify your email and mobile

### Step 2: Get API Key

1. Log in to Mappls Console: https://apis.mappls.com/console/
2. Go to **"Credentials"** section
3. Click **"Create New Credentials"**
4. Select:
   - **API**: `Mappls APIs`
   - **Type**: `REST API`
5. Your **REST API Key** will be generated
6. Copy the key (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

### Step 3: Add to .env File

Open `.env` in your project root and add:

```env
MAPPLS_API_KEY=your_actual_api_key_here
```

Example:
```env
OPENROUTESERVICE_API_KEY=eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImRlOGU3MmJhOWMyNDQwMzA4NTRjYTE1NDAxMDUwZWIzIiwiaCI6Im11cm11cjY0In0=
MAPPLS_API_KEY=abc123def456ghi789jkl012mno345pq
```

### Step 4: Restart the Live Monitoring Service

```bash
python api/live_stream.py
```

You should see:
```
[INIT] Live monitoring using Mappls API for real-time traffic
```

---

## Free Tier Limits

Mappls offers a free tier with generous limits:

| API | Free Tier Limit | Sufficient For |
|-----|----------------|----------------|
| Geocoding | 10,000 requests/day | ✅ Testing & demos |
| Routing | 10,000 requests/day | ✅ Live monitoring |
| Traffic | Included with routing | ✅ Real-time updates |

**For Live Monitoring**:
- Updates every 20 seconds
- 3 updates/minute = 180/hour = 4,320/day
- Well within free tier! ✅

---

## Fallback Mode

If `MAPPLS_API_KEY` is not set or invalid, the system automatically falls back to:

1. **Hardcoded Coordinates** for common Bangalore locations:
   - Koramangala: (12.9352, 77.6245)
   - MG Road: (12.9716, 77.6412)
   - Whitefield: (12.9698, 77.7499)
   - Electronic City: (12.8387, 77.6873)

2. **Simulated Traffic** based on time of day:
   - Peak hours (7-10 AM, 5-8 PM): 1.5-2.5x baseline
   - Off-peak: 0.9-1.3x baseline

You'll see:
```
[WARNING] MAPPLS_API_KEY not found in .env. Using fallback mode.
[MAPPLS FALLBACK] Generated traffic data: 15min -> 22.5min
```

---

## Testing the Integration

### Test 1: Verify Mappls Connection

```bash
# Start the service
python api/live_stream.py

# Check console output
# Should see: [INIT] Live monitoring using Mappls API for real-time traffic
```

### Test 2: Start Live Monitoring

```bash
# In another terminal, launch dashboard
streamlit run authority_dashboard.py

# Navigate to "Live Monitoring" tab
# Start monitoring: Koramangala → MG Road
# Check for: [MAPPLS] Successfully fetched X route(s) with live traffic
```

### Test 3: Compare with OpenRouteService

```bash
# Run the regular dashboard (uses OpenRouteService)
streamlit run dashboard.py

# Enter same route: Koramangala → MG Road
# Compare duration and congestion values
```

---

## API Endpoints Used

### 1. Geocoding
```
GET https://apis.mappls.com/advancedmaps/v1/{api_key}/geo_code
Params:
  - address: "Koramangala, Bangalore"

Returns:
  - latitude: 12.9352
  - longitude: 77.6245
```

### 2. Routing with Traffic
```
GET https://apis.mappls.com/advancedmaps/v1/{api_key}/route_adv/driving/{origin};{destination}
Params:
  - rtype: 0 (optimal route)
  - region: IND

Returns:
  - distance: meters
  - duration: seconds (includes real-time traffic)
  - geometry: route polyline
```

---

## Troubleshooting

### Issue: "MAPPLS_API_KEY not found"

**Solution**:
1. Check `.env` file exists in project root
2. Verify key name is exactly `MAPPLS_API_KEY`
3. Remove quotes around the key value
4. Restart the service

### Issue: "API error: 401"

**Cause**: Invalid API key

**Solution**:
1. Verify key from Mappls Console
2. Ensure no extra spaces in `.env`
3. Check key hasn't expired
4. Regenerate key if needed

### Issue: "API error: 403"

**Cause**: Free tier limit exceeded or API not enabled

**Solution**:
1. Check usage in Mappls Console
2. Wait for daily limit reset (midnight IST)
3. Enable "Routing API" in console if disabled

### Issue: No traffic updates

**Check**:
1. Console shows: `[MAPPLS] Successfully fetched routes`
2. If showing fallback, API might be unavailable
3. Check network connectivity
4. Verify Mappls API status: https://status.mappls.com/

---

## Advantages of Mappls for Indian Traffic

### 1. **Hyperlocal Data**
- Knows Indian road peculiarities
- Accounts for auto-rickshaws, two-wheelers
- Understands Indian traffic patterns

### 2. **Better Coverage**
- Detailed maps for tier 2/3 cities
- Accurate lane information
- Traffic signals and speed limits

### 3. **Real-time Accuracy**
- Live traffic from millions of Indian users
- Festival/event traffic patterns
- Weather-based routing

### 4. **Language Support**
- Hindi and regional languages
- Local landmark recognition
- Native address formats

---

## Cost Comparison

| Feature | Mappls Free | OpenRouteService Free |
|---------|-------------|----------------------|
| Requests/day | 10,000 | 2,000 |
| Traffic data | ✅ Real-time | ❌ No traffic |
| Indian coverage | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Setup time | 5 minutes | 2 minutes |
| Best for | 🇮🇳 Live Indian traffic | 🌍 Global routing |

---

## Example Output

### With Mappls API:
```
[INIT] Live monitoring using Mappls API for real-time traffic
[MONITOR] Started monitoring: Koramangala, Bangalore -> MG Road, Bangalore
[MAPPLS] Successfully fetched 1 route(s) with live traffic
[UPDATE] Distance: 8.5 km, Duration: 23.5 min, CI: 1.67 (HIGH)
[ALERT] High congestion detected! CI=1.67
```

### With Fallback Mode:
```
[WARNING] MAPPLS_API_KEY not found in .env. Using fallback mode.
[INIT] Live monitoring using Mappls API for real-time traffic
[MONITOR] Started monitoring: Koramangala, Bangalore -> MG Road, Bangalore
[MAPPLS FALLBACK] Generated traffic data: 15min -> 22.5min
[UPDATE] Distance: 8.5 km, Duration: 22.5 min, CI: 1.50 (HIGH)
```

---

## Migration Checklist

- [ ] Create Mappls account
- [ ] Get REST API key
- [ ] Add `MAPPLS_API_KEY` to `.env`
- [ ] Test with `python api/live_stream.py`
- [ ] Verify live monitoring in Authority Dashboard
- [ ] Compare results with OpenRouteService
- [ ] Monitor API usage in Mappls Console

---

## Support Resources

- **Mappls API Docs**: https://docs.mappls.com/
- **Console**: https://apis.mappls.com/console/
- **Support**: support@mappls.com
- **Community**: https://community.mappls.com/

---

## Summary

✅ **Live Monitoring** (api/live_stream.py) → **Mappls API** (Indian traffic)  
✅ **Dashboard/Demo** (dashboard.py, demo.py) → **OpenRouteService** (Global)  
✅ **Fallback Mode** → Works without Mappls key (simulated data)  
✅ **Free Tier** → 10,000 requests/day (plenty for demos)  

---

**Your live monitoring now uses the best Indian traffic data available!** 🇮🇳 🚦
