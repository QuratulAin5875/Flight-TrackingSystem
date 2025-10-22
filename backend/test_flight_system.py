#!/usr/bin/env python3
"""
FlightAware System Test Script
This script demonstrates the complete FlightAware system functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta
import random

# Configuration
API_BASE_URL = "http://localhost:5000/api"

def test_flight_data():
    """Generate realistic flight data for testing"""
    return {
        "flight_id": f"AA{random.randint(100, 999)}",
        "latitude": round(random.uniform(25.0, 45.0), 6),
        "longitude": round(random.uniform(-80.0, -70.0), 6),
        "altitude": random.randint(20000, 40000),
        "speed": random.randint(300, 600),
        "heading": random.randint(0, 360),
        "status": random.choice(["en-route", "departed", "landed", "delayed"]),
        "timestamp": datetime.now().isoformat(),
        "aircraft_type": random.choice(["Boeing 737", "Airbus A320", "Boeing 777", "Airbus A350"]),
        "airline": random.choice(["American Airlines", "Delta", "United", "Southwest"]),
        "departure": random.choice(["JFK", "LAX", "ORD", "DFW"]),
        "arrival": random.choice(["LAX", "JFK", "SFO", "MIA"])
    }

def send_flight_data(flight_data):
    """Send flight data to the API"""
    try:
        response = requests.post(f"{API_BASE_URL}/flight/update", json=flight_data)
        if response.status_code == 200:
            print(f"✅ Sent data for flight {flight_data['flight_id']}")
            return True
        else:
            print(f"❌ Failed to send data: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Error sending data: {e}")
        return False

def get_flight_location(flight_id, timestamp=None):
    """Get flight location (current or at specific time)"""
    try:
        if timestamp:
            url = f"{API_BASE_URL}/flight/{flight_id}/location?timestamp={timestamp}"
        else:
            url = f"{API_BASE_URL}/flight/{flight_id}"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"📍 Flight {flight_id} location:")
            if 'location' in data:
                loc = data['location']
                print(f"   Position: {loc['latitude']:.6f}, {loc['longitude']:.6f}")
                print(f"   Altitude: {loc['altitude']} ft")
                print(f"   Speed: {loc['speed']} knots")
                print(f"   Heading: {loc['heading']}°")
                print(f"   Status: {loc['status']}")
            else:
                print(f"   Position: {data['latitude']:.6f}, {data['longitude']:.6f}")
                print(f"   Altitude: {data['altitude']} ft")
                print(f"   Speed: {data['speed']} knots")
                print(f"   Heading: {data['heading']}°")
                print(f"   Status: {data['status']}")
            return data
        else:
            print(f"❌ Failed to get flight location: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ Error getting flight location: {e}")
        return None

def get_flight_history(flight_id):
    """Get complete flight tracking history"""
    try:
        response = requests.get(f"{API_BASE_URL}/flight/{flight_id}/history")
        if response.status_code == 200:
            history = response.json()
            print(f"📊 Flight {flight_id} has {len(history)} tracking points")
            return history
        else:
            print(f"❌ Failed to get flight history: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ Error getting flight history: {e}")
        return None

def get_active_flights():
    """Get all active flights"""
    try:
        response = requests.get(f"{API_BASE_URL}/flights")
        if response.status_code == 200:
            flights = response.json()
            print(f"🛫 Found {len(flights)} active flights")
            for flight in flights:
                print(f"   {flight['flight_id']}: {flight['status']} at {flight['latitude']:.4f}, {flight['longitude']:.4f}")
            return flights
        else:
            print(f"❌ Failed to get active flights: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ Error getting active flights: {e}")
        return None

def complete_flight(flight_id):
    """Mark flight as completed and move to logs"""
    try:
        response = requests.post(f"{API_BASE_URL}/flight/{flight_id}/complete")
        if response.status_code == 200:
            print(f"✅ Flight {flight_id} completed and moved to logs")
            return True
        else:
            print(f"❌ Failed to complete flight: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Error completing flight: {e}")
        return False

def get_completed_flights():
    """Get all completed flights from logs"""
    try:
        response = requests.get(f"{API_BASE_URL}/flights/logs")
        if response.status_code == 200:
            logs = response.json()
            print(f"📋 Found {len(logs)} completed flights in logs")
            for log in logs:
                print(f"   {log['flight_id']}: completed at {log['completed_at']} with {len(log['path'])} tracking points")
            return logs
        else:
            print(f"❌ Failed to get completed flights: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ Error getting completed flights: {e}")
        return None

def simulate_flight_journey(flight_id, num_points=10):
    """Simulate a complete flight journey with multiple tracking points"""
    print(f"\n🚀 Simulating flight journey for {flight_id}")
    
    # Starting position (New York)
    start_lat, start_lon = 40.7128, -74.0060
    # Ending position (Los Angeles)
    end_lat, end_lon = 34.0522, -118.2437
    
    for i in range(num_points):
        # Interpolate between start and end positions
        progress = i / (num_points - 1)
        lat = start_lat + (end_lat - start_lat) * progress
        lon = start_lon + (end_lon - start_lon) * progress
        
        # Add some random variation
        lat += random.uniform(-0.5, 0.5)
        lon += random.uniform(-0.5, 0.5)
        
        flight_data = {
            "flight_id": flight_id,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "altitude": random.randint(30000, 40000),
            "speed": random.randint(400, 550),
            "heading": random.randint(250, 290),  # Generally westbound
            "status": "en-route" if i < num_points - 1 else "landed",
            "timestamp": (datetime.now() - timedelta(hours=num_points-i)).isoformat(),
            "aircraft_type": "Boeing 737",
            "airline": "American Airlines",
            "departure": "JFK",
            "arrival": "LAX"
        }
        
        send_flight_data(flight_data)
        time.sleep(0.5)  # Small delay between points

def main():
    """Main test function"""
    print("🛩️  FlightAware System Test")
    print("=" * 50)
    
    # Test 1: Send individual flight data
    print("\n1️⃣ Testing individual flight data submission...")
    flight_data = test_flight_data()
    send_flight_data(flight_data)
    
    # Test 2: Simulate a complete flight journey
    print("\n2️⃣ Simulating complete flight journey...")
    test_flight_id = "TEST123"
    simulate_flight_journey(test_flight_id, 8)
    
    # Test 3: Get current flight location
    print("\n3️⃣ Getting current flight location...")
    get_flight_location(test_flight_id)
    
    # Test 4: Get flight location at specific time
    print("\n4️⃣ Getting flight location at specific time...")
    past_time = (datetime.now() - timedelta(hours=2)).isoformat()
    get_flight_location(test_flight_id, past_time)
    
    # Test 5: Get flight history
    print("\n5️⃣ Getting flight history...")
    get_flight_history(test_flight_id)
    
    # Test 6: Get all active flights
    print("\n6️⃣ Getting all active flights...")
    get_active_flights()
    
    # Test 7: Complete a flight
    print("\n7️⃣ Completing flight...")
    complete_flight(test_flight_id)
    
    # Test 8: Get completed flights
    print("\n8️⃣ Getting completed flights...")
    get_completed_flights()
    
    # Test 9: Send some more test flights
    print("\n9️⃣ Adding more test flights...")
    for i in range(3):
        flight_data = test_flight_data()
        send_flight_data(flight_data)
        time.sleep(1)
    
    # Final check of active flights
    print("\n🔟 Final check of active flights...")
    get_active_flights()
    
    print("\n✅ All tests completed!")
    print("\n📝 API Endpoints Summary:")
    print("   POST /api/flight/update - Send flight tracking data")
    print("   GET  /api/flight/<id> - Get current flight location")
    print("   GET  /api/flight/<id>/location?timestamp=<time> - Get flight location at specific time")
    print("   GET  /api/flight/<id>/history - Get complete flight tracking history")
    print("   POST /api/flight/<id>/complete - Mark flight as completed")
    print("   GET  /api/flights - Get all active flights")
    print("   GET  /api/flights/logs - Get all completed flights")

if __name__ == "__main__":
    main()
