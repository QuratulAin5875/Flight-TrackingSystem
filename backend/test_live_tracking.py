#!/usr/bin/env python3
"""
Test Live Flight Tracking - Simulate real-time flight updates
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:5000/api"

def simulate_live_flight(flight_id, duration_minutes=5):
    """Simulate a live flight with continuous updates"""
    print(f"🚀 Starting live simulation for flight {flight_id}")
    
    # Starting position (New York)
    start_lat, start_lon = 40.7128, -74.0060
    # Ending position (Los Angeles) 
    end_lat, end_lon = 34.0522, -118.2437
    
    # Calculate total updates (every 10 seconds for duration)
    total_updates = (duration_minutes * 60) // 10
    
    for i in range(total_updates):
        # Interpolate between start and end positions
        progress = i / (total_updates - 1)
        lat = start_lat + (end_lat - start_lat) * progress
        lon = start_lon + (end_lon - start_lon) * progress
        
        # Add some random variation for realism
        lat += random.uniform(-0.1, 0.1)
        lon += random.uniform(-0.1, 0.1)
        
        # Vary altitude and speed realistically
        altitude = max(0, 35000 - (progress * 10000) + random.randint(-1000, 1000))
        speed = max(0, 500 - (progress * 200) + random.randint(-50, 50))
        heading = 270 + random.randint(-10, 10)  # Generally westbound
        
        # Determine status
        if progress < 0.1:
            status = "departed"
        elif progress > 0.9:
            status = "landed"
        else:
            status = "en-route"
        
        flight_data = {
            "flight_id": flight_id,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "altitude": int(altitude),
            "speed": int(speed),
            "heading": int(heading),
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "aircraft_type": "Boeing 737",
            "airline": "American Airlines",
            "departure": "JFK",
            "arrival": "LAX"
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/flight/update", json=flight_data)
            if response.status_code == 200:
                print(f"✅ Update {i+1}/{total_updates}: {status} at {lat:.4f}, {lon:.4f} (alt: {altitude}ft, speed: {speed}kts)")
            else:
                print(f"❌ Failed to send update {i+1}: {response.json()}")
        except Exception as e:
            print(f"❌ Error sending update {i+1}: {e}")
        
        # Wait 10 seconds before next update
        time.sleep(10)
    
    print(f"🏁 Flight {flight_id} simulation completed!")

def create_test_flights():
    """Create multiple test flights for live tracking"""
    test_flights = [
        {"id": "LIVE001", "route": "NYC to Boston", "duration": 2},
        {"id": "LIVE002", "route": "NYC to Chicago", "duration": 3},
        {"id": "LIVE003", "route": "NYC to Miami", "duration": 4}
    ]
    
    for flight in test_flights:
        print(f"\n📡 Creating test flight {flight['id']} ({flight['route']})")
        
        # Send initial flight data
        initial_data = {
            "flight_id": flight['id'],
            "latitude": 40.7128 + random.uniform(-0.5, 0.5),
            "longitude": -74.0060 + random.uniform(-0.5, 0.5),
            "altitude": 35000,
            "speed": 450,
            "heading": 270,
            "status": "departed",
            "timestamp": datetime.now().isoformat(),
            "aircraft_type": "Boeing 737",
            "airline": "American Airlines",
            "departure": "JFK",
            "arrival": "LAX"
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/flight/update", json=initial_data)
            if response.status_code == 200:
                print(f"✅ Created flight {flight['id']}")
            else:
                print(f"❌ Failed to create flight {flight['id']}: {response.json()}")
        except Exception as e:
            print(f"❌ Error creating flight {flight['id']}: {e}")

def main():
    print("🛩️ Live Flight Tracking Test")
    print("=" * 50)
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:5000")
        print("✅ Backend is running")
    except:
        print("❌ Backend not running. Please start with: python app.py")
        return
    
    # Create test flights
    print("\n📡 Creating test flights...")
    create_test_flights()
    
    # Show active flights
    print("\n📊 Active flights:")
    try:
        response = requests.get(f"{API_BASE_URL}/flights")
        if response.status_code == 200:
            flights = response.json()
            for flight in flights:
                print(f"  ✈️ {flight['flight_id']}: {flight['status']} at {flight['latitude']:.4f}, {flight['longitude']:.4f}")
        else:
            print("❌ Failed to get active flights")
    except Exception as e:
        print(f"❌ Error getting flights: {e}")
    
    print("\n🎯 Now you can:")
    print("1. Open frontend/index.html in your browser")
    print("2. Click '🔴 Live' buttons to start live tracking")
    print("3. Watch flights update in real-time on the map")
    print("4. Use '🔴 Live All' to track all flights at once")
    
    print("\n💡 The frontend will automatically update every 2 seconds")
    print("   for any flights you're tracking live!")

if __name__ == "__main__":
    main()
