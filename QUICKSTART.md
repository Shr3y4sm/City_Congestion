# CityFlow AI - Quick Start Guide 🚦

## 🎯 Three Easy Ways to Use Live Monitoring

### **Method 1: Terminal Viewer (What You Just Used!)**

**Step 1:** Start API service
```bash
python api/live_stream.py
```

**Step 2:** Start monitoring
```bash
python start_monitoring.py
```

**Step 3:** Watch live updates
```bash
python watch_traffic.py
```

You'll see colorful real-time updates like:
```
━━━ Update #2 ━━━
Time: 2026-02-27T15:33:24
Route: Koramangala, Bangalore → MG Road, Bangalore
Distance: 7.13 km  |  Duration: 31.5 min
Congestion: HIGH (Index: 2.58)  |  Risk: 10.0/10
⚠️  ALERT: HIGH CONGESTION DETECTED!
```

---

### **Method 2: Streamlit Dashboard (GUI)**

**Step 1:** Start API service
```bash
python api/live_stream.py
```

**Step 2:** Start dashboard
```bash
streamlit run authority_dashboard.py
```

**Step 3:** Open browser
```
http://localhost:8501
```

**Step 4:** Go to "Live Monitoring" tab
- Enter origin and destination
- Click "Start Monitoring"
- Watch live updates in the dashboard

---

### **Method 3: PowerShell (Windows)**

**Start monitoring:**
```powershell
.\start-monitoring.ps1
```

**With custom route:**
```powershell
.\start-monitoring.ps1 -Origin "Whitefield, Bangalore" -Destination "Electronic City, Bangalore"
```

---

## 📊 Current Configuration

### Active Services:
- ✅ **API Service:** Port 8000 (FastAPI + WebSocket)
- ✅ **Traffic Provider:** TomTom (auto-selected)
- ✅ **Dashboard:** Port 8501 (Streamlit)

### API Keys Configured:
- ✅ `TOMTOM_API_KEY` (Active provider)
- ✅ `MAPPLS_API_KEY` (Backup)
- ✅ `OPENROUTESERVICE_API_KEY` (Static routing)

---

## 🎨 Terminal Features

Your terminal viewer shows:
- 🎨 **Color-coded congestion levels:**
  - 🟢 **GREEN** = LOW congestion (CI < 1.2)
  - 🟡 **YELLOW** = MEDIUM congestion (CI 1.2-1.5)
  - 🔴 **RED** = HIGH congestion (CI ≥ 1.5)
  
- ⚡ **Updates every 20 seconds**
- 🚨 **Automatic alerts** for high congestion
- 📊 **Risk scores** (0-10 scale)
- ⌨️ **Press Ctrl+C to stop**

---

## 🔧 Common Commands

### Check if API is running:
```bash
curl http://localhost:8000/
```

### Check monitoring status:
```bash
curl http://localhost:8000/status
```

### Stop monitoring:
```bash
curl -X POST http://localhost:8000/stop-monitoring
```

### Test TomTom provider:
```bash
python services/tomtom_provider.py
```

---

## 🐛 Troubleshooting

### API service not responding?
```bash
# Check if port is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F

# Restart service
python api/live_stream.py
```

### Monitoring not starting?
```bash
# Check service status first
curl http://localhost:8000/

# Then start monitoring
python start_monitoring.py
```

### Want to change provider?
Edit `.env` file:
- Remove `TOMTOM_API_KEY` to use Mappls
- Add `TOMTOM_API_KEY` to use TomTom

Restart API service after changes.

---

## 🎓 Understanding the Metrics

### **Congestion Index (CI)**
```
CI = Actual Travel Time / Free-Flow Travel Time

Example:
  Normal: 15 minutes → CI = 1.0
  Light traffic: 18 minutes → CI = 1.2 (MEDIUM)
  Heavy traffic: 30 minutes → CI = 2.0 (HIGH)
```

### **Risk Score**
```
Risk = CI × 5 (capped at 10)

Examples:
  CI 1.0 → Risk 5.0/10 (Normal)
  CI 1.5 → Risk 7.5/10 (Caution)
  CI 2.0 → Risk 10.0/10 (Avoid!)
```

---

## 🚀 For Hackathons/Demos

### Quick Demo Script:
```bash
# Terminal 1
python api/live_stream.py

# Terminal 2
python start_monitoring.py

# Terminal 3
python watch_traffic.py
```

**Show the audience:**
1. ✅ Real-time traffic updates in terminal
2. ✅ Color-coded congestion levels
3. ✅ Automatic high-traffic alerts
4. ✅ TomTom global traffic data integration

**Key talking points:**
- "Live traffic data from TomTom's global network"
- "Real-time congestion analysis with 20-second updates"
- "Smart alerting system for traffic hotspots"
- "Production-ready with multiple provider support"

---

## 📝 Example Routes to Try

### Bangalore:
```bash
python start_monitoring.py "Koramangala, Bangalore" "MG Road, Bangalore"
python start_monitoring.py "Whitefield, Bangalore" "Electronic City, Bangalore"
```

### Other Cities:
```bash
python start_monitoring.py "Marina Beach, Chennai" "T Nagar, Chennai"
python start_monitoring.py "Bandra, Mumbai" "Andheri, Mumbai"
```

---

## 🎯 What's Running Right Now

Based on your terminal, you have:
- ✅ API service active on port 8000
- ✅ TomTom provider connected
- ✅ Monitoring: Koramangala → MG Road
- ✅ Terminal viewer showing live updates
- ⚠️ Current congestion: **HIGH** (CI: 2.58, Risk: 10/10)

**Your system is fully operational and demo-ready!** 🚀

---

## 📚 Documentation Files

- `TOMTOM_INTEGRATION.md` - TomTom provider details
- `MAPPLS_SETUP.md` - Mappls API setup guide
- `API_ARCHITECTURE.md` - API separation strategy
- `README.md` - Main project documentation

---

## 💡 Pro Tips

1. **Terminal viewer runs in background** - Let it run while you demo other features
2. **Use PowerShell script** for quick testing - `.\start-monitoring.ps1`
3. **Dashboard + Terminal** together make impressive demos
4. **Multiple instances** - Run viewers in different terminals for different routes
5. **Risk score > 7.5** means recommend alternate routes

---

**Ready for your hackathon! Good luck! 🏆**
