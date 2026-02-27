"""
Quick Test Script for Live Monitoring Feature
==============================================
Tests the integration between FastAPI service and Authority Dashboard
"""

import time
import subprocess
import sys
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60 + "\n")

def print_step(num, text):
    print(f"\n[STEP {num}] {text}")
    print("-" * 60)

def main():
    print_header("CityFlow AI - Live Monitoring Test Script")
    
    print("This script will guide you through testing the Live Monitoring feature.")
    print("\nPrerequisites:")
    print("  1. Virtual environment activated")
    print("  2. All dependencies installed (pip install -r requirements.txt)")
    print("  3. .env file with OPENROUTESERVICE_API_KEY")
    
    input("\nPress Enter to continue...")
    
    # Step 1: Check FastAPI service
    print_step(1, "Checking FastAPI Service")
    print("We need to start the FastAPI service first.")
    print("\nOpen a NEW terminal and run:")
    print("  cd City_Congestion")
    print("  python api/live_stream.py")
    print("\nWait until you see: 'Uvicorn running on http://0.0.0.0:8000'")
    
    input("\nPress Enter once the service is running...")
    
    # Step 2: Verify service is up
    print_step(2, "Verifying Service Connection")
    try:
        import requests
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("[OK] FastAPI service is running")
            data = response.json()
            print(f"     Service: {data.get('service')}")
            print(f"     Status: {data.get('status')}")
        else:
            print("[ERROR] Service returned unexpected status")
            return
    except Exception as e:
        print(f"[ERROR] Cannot connect to service: {e}")
        print("\nMake sure the FastAPI service is running!")
        return
    
    # Step 3: Launch Authority Dashboard
    print_step(3, "Launching Authority Dashboard")
    print("Starting Streamlit dashboard...")
    print("\nThe dashboard will open in your browser automatically.")
    print("Navigate to the 'Live Monitoring' tab (third tab)")
    
    input("\nPress Enter to launch dashboard...")
    
    try:
        # Launch Streamlit
        print("\n[INFO] Starting Streamlit...")
        print("[INFO] Press CTRL+C in this terminal to stop the dashboard")
        print("[INFO] The dashboard will open at: http://localhost:8501")
        print("-" * 60)
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "authority_dashboard.py",
            "--server.headless", "true"
        ])
    
    except KeyboardInterrupt:
        print("\n\n[INFO] Dashboard stopped by user")
    
    except Exception as e:
        print(f"\n[ERROR] Failed to launch dashboard: {e}")
    
    # Step 4: Instructions
    print_step(4, "Testing Instructions")
    print("""
Once the dashboard opens:

1. Click on the "Live Monitoring" tab (third tab)

2. Enter route details:
   - Origin: Koramangala, Bangalore
   - Destination: MG Road, Bangalore

3. Click "Start Monitoring"

4. Wait ~20 seconds for first update

5. Observe live updates:
   - Congestion Index
   - Risk Score
   - Alert banners
   - Auto-refreshing data

6. Click "Stop Monitoring" when done

Expected Behavior:
- Green "Connected" status after starting
- Updates every 20 seconds
- Red alert if CI > 1.5
- Metrics showing distance, duration, CI, risk score
    """)
    
    print_header("Test Complete!")
    print("To test again:")
    print("  1. Keep FastAPI service running")
    print("  2. Refresh the Streamlit dashboard")
    print("  3. Go to Live Monitoring tab")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[EXIT] Test script stopped")
