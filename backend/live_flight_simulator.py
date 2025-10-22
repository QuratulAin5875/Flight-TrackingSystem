#!/usr/bin/env python3
"""
Live Flight Simulator - Creates moving flights with real-time tracking
"""

import requests
import json
import time
import random
import math
import threading
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:5000/api"

# Airport coordinates
AIRPORTS = {
    "JFK": {"lat": 40.6413, "lon": -73.7781, "name": "New York JFK"},
    "LAX": {"lat": 33.9416, "lon": -118.4085, "name": "Los Angeles"},
    "ORD": {"lat": 41.9786, "lon": -87.9048, "name": "Chicago O'Hare"},
    "DFW": {"lat": 32.8968, "lon": -97.0380, "name": "Dallas/Fort Worth"},
    "ATL": {"lat": 33.6407, "lon": -84.4277, "name": "Atlanta"},
    "DEN": {"lat": 39.8561, "lon": -104.6737, "name": "Denver"},
    "SFO": {"lat": 37.6213, "lon": -122.3790, "name": "San Francisco"},
    "SEA": {"lat": 47.4502, "lon": -122.3088, "name": "Seattle"},
    "BOS": {"lat": 42.3656, "lon": -71.0096, "name": "Boston"},
    "MIA": {"lat": 25.7959, "lon": -80.2871, "name": "Miami"}
}

class LiveFlight:
    def __init__(self, flight_id, source, destination, duration_minutes=30):
        self.flight_id = flight_id
        self.source = source
        self.destination = destination
        self.duration_minutes = duration_minutes
        self.is_running = False
        self.current_progress = 0
        self.current_position = AIRPORTS[source].copy()
        self.start_time = None
        self.expected_end_time = None
        
        # Calculate route
        self.route = self.calculate_route()
        self.total_points = len(self.route)
        self.current_point_index = 0
        
    def calculate_route(self):
        """Calculate flight route with waypoints"""
        source_coords = AIRPORTS[self.source]
        dest_coords = AIRPORTS[self.destination]
        
        # Create waypoints along the route
        num_waypoints = 20
        waypoints = []
        
        for i in range(num_waypoints + 1):
            progress = i / num_waypoints
            lat = source_coords["lat"] + (dest_coords["lat"] - source_coords["lat"]) * progress
            lon = source_coords["lon"] + (dest_coords["lon"] - source_coords["lon"]) * progress
            
            # Add some realistic variation
            lat += random.uniform(-0.2, 0.2)
            lon += random.uniform(-0.2, 0.2)
            
            waypoints.append({
                "lat": lat,
                "lon": lon,
                "progress": progress * 100
            })
        
        return waypoints
    
    def get_current_position(self):
        """Get current flight position"""
        if self.current_point_index >= len(self.route):
            return self.route[-1]
        return self.route[self.current_point_index]
    
    def get_flight_status(self):
        """Get current flight status based on progress"""
        progress = self.current_progress
        
        if progress < 5:
            return "departed"
        elif progress < 15:
            return "climbing"
        elif progress < 85:
            return "cruising"
        elif progress < 95:
            return "descending"
        else:
            return "landed"
    
    def get_flight_data(self):
        """Generate current flight data"""
        position = self.get_current_position()
        status = self.get_flight_status()
        
        # Calculate altitude and speed based on status
        if status == "departed":
            altitude = 0
            speed = 0
        elif status == "climbing":
            altitude = int(self.current_progress * 2000)
            speed = 300 + int(self.current_progress * 20)
        elif status == "cruising":
            altitude = 35000 + random.randint(-1000, 1000)
            speed = 500 + random.randint(-50, 50)
        elif status == "descending":
            altitude = int(35000 * (1 - (self.current_progress - 85) / 10))
            speed = 400 + int((self.current_progress - 85) * 10)
        else:  # landed
            altitude = 0
            speed = 0
        
        return {
            "flight_id": self.flight_id,
            "latitude": round(position["lat"], 6),
            "longitude": round(position["lon"], 6),
            "altitude": max(0, altitude),
            "speed": max(0, speed),
            "heading": random.randint(250, 290),
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "source": self.source,
            "destination": self.destination,
            "route_progress": round(self.current_progress, 2)
        }
    
    def send_flight_data(self):
        """Send current flight data to API"""
        try:
            flight_data = self.get_flight_data()
            response = requests.post(f"{API_BASE_URL}/flight/update", json=flight_data)
            
            if response.status_code == 200:
                print(f"✈️ {self.flight_id}: {flight_data['status']} at {flight_data['latitude']:.4f}, {flight_data['longitude']:.4f} "
                      f"(alt: {flight_data['altitude']}ft, speed: {flight_data['speed']}kts, progress: {flight_data['route_progress']}%)")
                return True
            else:
                print(f"❌ Failed to send data for {self.flight_id}: {response.json()}")
                return False
        except Exception as e:
            print(f"❌ Error sending data for {self.flight_id}: {e}")
            return False
    
    def run_flight(self):
        """Run the complete flight simulation"""
        self.is_running = True
        self.start_time = datetime.now()
        self.expected_end_time = self.start_time + timedelta(minutes=self.duration_minutes)
        
        print(f"🚀 Starting flight {self.flight_id}: {self.source} → {self.destination} (Duration: {self.duration_minutes} min)")
        
        # Calculate update interval (every 10 seconds for 30-minute flight)
        update_interval = 10  # seconds
        total_updates = (self.duration_minutes * 60) // update_interval
        
        for i in range(total_updates + 1):
            if not self.is_running:
                break
            
            # Check if flight duration has elapsed
            current_time = datetime.now()
            if current_time >= self.expected_end_time:
                print(f"⏰ Flight {self.flight_id} duration completed ({self.duration_minutes} min)")
                break
            
            # Update progress
            self.current_progress = (i / total_updates) * 100
            self.current_point_index = int((i / total_updates) * (self.total_points - 1))
            
            # Send flight data
            self.send_flight_data()
            
            # Wait before next update
            time.sleep(update_interval)
        
        # Final update to mark as landed
        if self.is_running:
            self.current_progress = 100
            self.current_point_index = self.total_points - 1
            final_data = self.get_flight_data()
            final_data["status"] = "landed"
            final_data["route_progress"] = 100.0
            self.send_flight_data()
            
            # Calculate actual flight duration
            actual_duration = (datetime.now() - self.start_time).total_seconds() / 60
            print(f"🏁 {self.flight_id} has landed at {self.destination}! (Actual duration: {actual_duration:.1f} min)")
        
        self.is_running = False
    
    def stop_flight(self):
        """Stop the flight simulation"""
        self.is_running = False
        print(f"⏹️ Stopped flight {self.flight_id}")

def create_live_flights():
    """Create multiple live flights"""
    flights = [
        {"id": "AA100", "source": "JFK", "destination": "LAX", "duration": 30},
        {"id": "AA200", "source": "LAX", "destination": "ORD", "duration": 25},
        {"id": "AA300", "source": "ORD", "destination": "DFW", "duration": 20},
        {"id": "AA400", "source": "DFW", "destination": "ATL", "duration": 15},
        {"id": "AA500", "source": "ATL", "destination": "DEN", "duration": 25},
        {"id": "AA600", "source": "DEN", "destination": "SFO", "duration": 20},
        {"id": "AA700", "source": "SFO", "destination": "SEA", "duration": 15},
        {"id": "AA800", "source": "SEA", "destination": "BOS", "duration": 30},
        {"id": "AA900", "source": "BOS", "destination": "MIA", "duration": 20},
        {"id": "AA1000", "source": "MIA", "destination": "JFK", "duration": 25}
    ]
    
    return flights

def run_live_flight_simulation():
    """Run the live flight simulation"""
    print("🛩️ Starting Live Flight Simulation")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:5000")
        print("✅ Backend is running")
    except:
        print("❌ Backend not running. Please start with: python app.py")
        return
    
    # Create flights
    flights_data = create_live_flights()
    live_flights = []
    threads = []
    
    # Create flight objects
    for flight_data in flights_data:
        flight = LiveFlight(
            flight_data["id"],
            flight_data["source"],
            flight_data["destination"],
            flight_data["duration"]
        )
        live_flights.append(flight)
    
    # Start all flights with random delays
    for i, flight in enumerate(live_flights):
        delay = random.randint(0, 60)  # 0-1 minute delay
        
        def start_flight_with_delay(flight_obj, delay_time):
            time.sleep(delay_time)
            flight_obj.run_flight()
        
        thread = threading.Thread(target=start_flight_with_delay, args=(flight, delay))
        thread.daemon = True
        thread.start()
        threads.append(thread)
        
        print(f"📅 {flight.flight_id}: Departing {flight.source} → {flight.destination} "
              f"(in {delay}s, duration: {flight.duration_minutes}min)")
    
    print(f"\n🚀 {len(live_flights)} flights scheduled for departure!")
    print("💡 Open the frontend to watch flights move in real-time!")
    print("💡 Flights will update every 10 seconds with new positions!")
    
    # Monitor flights
    try:
        while True:
            time.sleep(30)  # Check every 30 seconds
            active_count = sum(1 for flight in live_flights if flight.is_running)
            if active_count == 0:
                print("\n🏁 All flights completed!")
                break
            print(f"📊 {active_count} flights currently in progress...")
    except KeyboardInterrupt:
        print("\n⏹️ Stopping all flights...")
        for flight in live_flights:
            flight.stop_flight()

if __name__ == "__main__":
    run_live_flight_simulation()
