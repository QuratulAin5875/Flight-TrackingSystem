#!/usr/bin/env python3
"""
Test MongoDB connection and create sample data
"""

import requests
import json
from datetime import datetime
import time

# Test the backend connection
def test_backend():
    try:
        response = requests.get("http://localhost:5000")
        print("✅ Backend is running!")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Backend not running: {e}")
        return False

# Send sample flight data
def send_sample_data():
    sample_flight = {
        "flight_id": "AA123",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "altitude": 35000,
        "speed": 450,
        "heading": 270,
        "status": "en-route",
        "timestamp": datetime.now().isoformat(),
        "aircraft_type": "Boeing 737",
        "airline": "American Airlines",
        "departure": "JFK",
        "arrival": "LAX"
    }
    
    try:
        response = requests.post("http://localhost:5000/api/flight/update", json=sample_flight)
        if response.status_code == 200:
            print("✅ Sample flight data sent successfully!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Failed to send data: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Error sending data: {e}")
        return False

# Send multiple tracking points to simulate a flight
def simulate_flight_journey():
    print("\n🚀 Simulating flight journey...")
    
    # Flight path from NYC to LA
    waypoints = [
        {"lat": 40.7128, "lon": -74.0060, "alt": 35000, "speed": 450, "heading": 270, "status": "departed"},
        {"lat": 40.5, "lon": -75.0, "alt": 36000, "speed": 480, "heading": 270, "status": "en-route"},
        {"lat": 40.0, "lon": -80.0, "alt": 37000, "speed": 500, "heading": 270, "status": "en-route"},
        {"lat": 39.0, "lon": -85.0, "alt": 38000, "speed": 520, "heading": 270, "status": "en-route"},
        {"lat": 38.0, "lon": -90.0, "alt": 39000, "speed": 540, "heading": 270, "status": "en-route"},
        {"lat": 37.0, "lon": -95.0, "alt": 38000, "speed": 520, "heading": 270, "status": "en-route"},
        {"lat": 36.0, "lon": -100.0, "alt": 37000, "speed": 500, "heading": 270, "status": "en-route"},
        {"lat": 35.0, "lon": -105.0, "alt": 36000, "speed": 480, "heading": 270, "status": "en-route"},
        {"lat": 34.5, "lon": -110.0, "alt": 35000, "speed": 460, "heading": 270, "status": "en-route"},
        {"lat": 34.0522, "lon": -118.2437, "alt": 0, "speed": 0, "heading": 0, "status": "landed"}
    ]
    
    for i, point in enumerate(waypoints):
        flight_data = {
            "flight_id": "AA123",
            "latitude": point["lat"],
            "longitude": point["lon"],
            "altitude": point["alt"],
            "speed": point["speed"],
            "heading": point["heading"],
            "status": point["status"],
            "timestamp": (datetime.now() - timedelta(hours=10-i)).isoformat(),
            "aircraft_type": "Boeing 737",
            "airline": "American Airlines",
            "departure": "JFK",
            "arrival": "LAX"
        }
        
        try:
            response = requests.post("http://localhost:5000/api/flight/update", json=flight_data)
            if response.status_code == 200:
                print(f"✅ Point {i+1}/10 sent: {point['status']} at {point['lat']:.2f}, {point['lon']:.2f}")
            else:
                print(f"❌ Failed to send point {i+1}: {response.json()}")
        except Exception as e:
            print(f"❌ Error sending point {i+1}: {e}")
        
        time.sleep(0.5)  # Small delay between points

# Get all active flights
def get_active_flights():
    try:
        response = requests.get("http://localhost:5000/api/flights")
        if response.status_code == 200:
            flights = response.json()
            print(f"\n📊 Active Flights: {len(flights)}")
            for flight in flights:
                print(f"  ✈️ {flight['flight_id']}: {flight['status']} at {flight['latitude']:.4f}, {flight['longitude']:.4f}")
            return flights
        else:
            print(f"❌ Failed to get flights: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ Error getting flights: {e}")
        return None

# Get flight history
def get_flight_history(flight_id):
    try:
        response = requests.get(f"http://localhost:5000/api/flight/{flight_id}/history")
        if response.status_code == 200:
            history = response.json()
            print(f"\n📈 Flight {flight_id} History: {len(history)} tracking points")
            return history
        else:
            print(f"❌ Failed to get history: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ Error getting history: {e}")
        return None

# Complete a flight
def complete_flight(flight_id):
    try:
        response = requests.post(f"http://localhost:5000/api/flight/{flight_id}/complete")
        if response.status_code == 200:
            print(f"✅ Flight {flight_id} completed and moved to logs!")
            return True
        else:
            print(f"❌ Failed to complete flight: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Error completing flight: {e}")
        return False

# Get completed flights
def get_completed_flights():
    try:
        response = requests.get("http://localhost:5000/api/flights/logs")
        if response.status_code == 200:
            logs = response.json()
            print(f"\n📋 Completed Flights: {len(logs)}")
            for log in logs:
                print(f"  ✅ {log['flight_id']}: completed with {len(log['path'])} tracking points")
            return logs
        else:
            print(f"❌ Failed to get completed flights: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ Error getting completed flights: {e}")
        return None

if __name__ == "__main__":
    from datetime import timedelta
    
    print("🛩️ FlightAware System Test")
    print("=" * 50)
    
    # Test 1: Check backend
    if not test_backend():
        print("Please start the backend first: python app.py")
        exit(1)
    
    # Test 2: Send sample data
    print("\n" + "="*50)
    print("📡 Sending sample flight data...")
    send_sample_data()
    
    # Test 3: Simulate flight journey
    print("\n" + "="*50)
    simulate_flight_journey()
    
    # Test 4: Get active flights
    print("\n" + "="*50)
    get_active_flights()
    
    # Test 5: Get flight history
    print("\n" + "="*50)
    get_flight_history("AA123")
    
    # Test 6: Complete flight
    print("\n" + "="*50)
    complete_flight("AA123")
    
    # Test 7: Get completed flights
    print("\n" + "="*50)
    get_completed_flights()
    
    print("\n🎉 All tests completed!")
    print("\n📝 Now check MongoDB Compass:")
    print("   1. Connect to mongodb://localhost:27017")
    print("   2. Open database 'flightaware'")
    print("   3. Check collections: flights, flight_tracking, flight_logs")
