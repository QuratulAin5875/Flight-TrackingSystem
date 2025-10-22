#!/usr/bin/env python3
"""
Realistic Flight Simulator - Mimics real FlightAware behavior
Simulates complete flight lifecycle from departure to arrival
"""

import requests
import json
import time
import random
import math
from datetime import datetime, timedelta
import threading

API_BASE_URL = "http://localhost:5000/api"

class FlightSimulator:
    def __init__(self, flight_id, departure, arrival, duration_hours=6):
        self.flight_id = flight_id
        self.departure = departure
        self.arrival = arrival
        self.duration_hours = duration_hours
        self.is_running = False
        self.current_status = "departed"
        
        # Flight phases with realistic timing
        self.phases = [
            {"name": "departed", "duration_minutes": 5, "altitude": 0, "speed": 0},
            {"name": "climbing", "duration_minutes": 15, "altitude": 35000, "speed": 300},
            {"name": "cruising", "duration_minutes": duration_hours * 60 - 30, "altitude": 35000, "speed": 500},
            {"name": "descending", "duration_minutes": 15, "altitude": 10000, "speed": 400},
            {"name": "landed", "duration_minutes": 5, "altitude": 0, "speed": 0}
        ]
        
        # Calculate route
        self.route = self.calculate_route()
        
    def calculate_route(self):
        """Calculate realistic flight path between departure and arrival"""
        # Major airport coordinates
        airports = {
            "JFK": {"lat": 40.6413, "lon": -73.7781},
            "LAX": {"lat": 33.9416, "lon": -118.4085},
            "ORD": {"lat": 41.9786, "lon": -87.9048},
            "DFW": {"lat": 32.8968, "lon": -97.0380},
            "ATL": {"lat": 33.6407, "lon": -84.4277},
            "DEN": {"lat": 39.8561, "lon": -104.6737},
            "SFO": {"lat": 37.6213, "lon": -122.3790},
            "SEA": {"lat": 47.4502, "lon": -122.3088},
            "BOS": {"lat": 42.3656, "lon": -71.0096},
            "MIA": {"lat": 25.7959, "lon": -80.2871}
        }
        
        start = airports.get(self.departure, {"lat": 40.7128, "lon": -74.0060})
        end = airports.get(self.arrival, {"lat": 34.0522, "lon": -118.2437})
        
        # Create waypoints along the route
        waypoints = []
        num_points = 20
        
        for i in range(num_points + 1):
            progress = i / num_points
            lat = start["lat"] + (end["lat"] - start["lat"]) * progress
            lon = start["lon"] + (end["lon"] - start["lon"]) * progress
            
            # Add some realistic variation
            lat += random.uniform(-0.5, 0.5)
            lon += random.uniform(-0.5, 0.5)
            
            waypoints.append({"lat": lat, "lon": lon})
        
        return waypoints
    
    def get_current_position(self, progress):
        """Get current position based on flight progress"""
        if progress >= 1.0:
            return self.route[-1]
        
        point_index = int(progress * (len(self.route) - 1))
        next_index = min(point_index + 1, len(self.route) - 1)
        
        current_point = self.route[point_index]
        next_point = self.route[next_index]
        
        # Interpolate between points
        sub_progress = (progress * (len(self.route) - 1)) - point_index
        
        lat = current_point["lat"] + (next_point["lat"] - current_point["lat"]) * sub_progress
        lon = current_point["lon"] + (next_point["lon"] - current_point["lon"]) * sub_progress
        
        return {"lat": lat, "lon": lon}
    
    def get_flight_phase(self, progress):
        """Determine current flight phase based on progress"""
        if progress < 0.05:
            return "departed"
        elif progress < 0.15:
            return "climbing"
        elif progress < 0.85:
            return "cruising"
        elif progress < 0.95:
            return "descending"
        else:
            return "landed"
    
    def get_flight_data(self, progress):
        """Generate realistic flight data for current progress"""
        position = self.get_current_position(progress)
        phase = self.get_flight_phase(progress)
        
        # Calculate altitude and speed based on phase
        if phase == "departed":
            altitude = 0
            speed = 0
            heading = random.randint(0, 360)
        elif phase == "climbing":
            altitude = int(progress * 35000)
            speed = 300 + int(progress * 200)
            heading = self.calculate_heading(position)
        elif phase == "cruising":
            altitude = 35000 + random.randint(-2000, 2000)
            speed = 500 + random.randint(-50, 50)
            heading = self.calculate_heading(position)
        elif phase == "descending":
            altitude = int(35000 * (1 - progress))
            speed = 400 + int(progress * 100)
            heading = self.calculate_heading(position)
        else:  # landed
            altitude = 0
            speed = 0
            heading = 0
        
        return {
            "flight_id": self.flight_id,
            "latitude": round(position["lat"], 6),
            "longitude": round(position["lon"], 6),
            "altitude": max(0, altitude),
            "speed": max(0, speed),
            "heading": heading,
            "status": phase,
            "timestamp": datetime.now().isoformat(),
            "aircraft_type": "Boeing 737",
            "airline": "American Airlines",
            "departure": self.departure,
            "arrival": self.arrival
        }
    
    def calculate_heading(self, position):
        """Calculate heading based on current position and destination"""
        # Simple heading calculation (in real system, this would be more complex)
        return random.randint(250, 290)  # Generally westbound
    
    def send_flight_data(self, flight_data):
        """Send flight data to the API"""
        try:
            response = requests.post(f"{API_BASE_URL}/flight/update", json=flight_data)
            if response.status_code == 200:
                return True
            else:
                print(f"❌ Failed to send data: {response.json()}")
                return False
        except Exception as e:
            print(f"❌ Error sending data: {e}")
            return False
    
    def run_simulation(self):
        """Run the complete flight simulation"""
        self.is_running = True
        print(f"🚀 Starting flight simulation for {self.flight_id}")
        print(f"   Route: {self.departure} → {self.arrival}")
        print(f"   Duration: {self.duration_hours} hours")
        
        # Calculate update interval (every 30 seconds for realistic simulation)
        total_duration_seconds = self.duration_hours * 3600
        update_interval = 30  # seconds
        total_updates = total_duration_seconds // update_interval
        
        for i in range(total_updates + 1):
            if not self.is_running:
                break
                
            progress = i / total_updates
            flight_data = self.get_flight_data(progress)
            
            # Send data to API
            success = self.send_flight_data(flight_data)
            
            if success:
                phase = flight_data["status"]
                pos = flight_data["latitude"], flight_data["longitude"]
                alt = flight_data["altitude"]
                speed = flight_data["speed"]
                
                print(f"✈️ {self.flight_id}: {phase} at {pos[0]:.4f}, {pos[1]:.4f} "
                      f"(alt: {alt}ft, speed: {speed}kts)")
            
            # Wait before next update
            time.sleep(update_interval)
        
        # Final update to ensure flight is marked as landed
        if self.is_running:
            final_data = self.get_flight_data(1.0)
            final_data["status"] = "landed"
            self.send_flight_data(final_data)
            print(f"🏁 {self.flight_id} has landed!")
        
        self.is_running = False
    
    def stop_simulation(self):
        """Stop the flight simulation"""
        self.is_running = False
        print(f"⏹️ Stopped simulation for {self.flight_id}")

def create_realistic_flights():
    """Create multiple realistic flights with different routes"""
    flights = [
        {"id": "AA100", "departure": "JFK", "arrival": "LAX", "duration": 6},
        {"id": "AA200", "departure": "LAX", "arrival": "ORD", "duration": 4},
        {"id": "AA300", "departure": "ORD", "arrival": "DFW", "duration": 3},
        {"id": "AA400", "departure": "DFW", "arrival": "ATL", "duration": 2},
        {"id": "AA500", "departure": "ATL", "arrival": "DEN", "duration": 4},
        {"id": "AA600", "departure": "DEN", "arrival": "SFO", "duration": 2},
        {"id": "AA700", "departure": "SFO", "arrival": "SEA", "duration": 2},
        {"id": "AA800", "departure": "SEA", "arrival": "BOS", "duration": 5},
        {"id": "AA900", "departure": "BOS", "arrival": "MIA", "duration": 3},
        {"id": "AA1000", "departure": "MIA", "arrival": "JFK", "duration": 3}
    ]
    
    return flights

def run_multiple_flights():
    """Run multiple flights simultaneously"""
    flights_data = create_realistic_flights()
    simulators = []
    threads = []
    
    print("🛩️ Starting Realistic Flight Simulation")
    print("=" * 60)
    
    # Create simulators for all flights
    for flight_data in flights_data:
        simulator = FlightSimulator(
            flight_data["id"],
            flight_data["departure"],
            flight_data["arrival"],
            flight_data["duration"]
        )
        simulators.append(simulator)
    
    # Start all flights with random delays
    for i, simulator in enumerate(simulators):
        # Stagger flight departures
        delay = random.randint(0, 300)  # 0-5 minutes delay
        
        def start_flight_with_delay(sim, delay_time):
            time.sleep(delay_time)
            sim.run_simulation()
        
        thread = threading.Thread(target=start_flight_with_delay, args=(simulator, delay))
        thread.daemon = True
        thread.start()
        threads.append(thread)
        
        print(f"📅 {simulator.flight_id}: Departing {simulator.departure} → {simulator.arrival} "
              f"(in {delay//60}m {delay%60}s)")
    
    print(f"\n🚀 {len(simulators)} flights scheduled for departure!")
    print("💡 Open the frontend to watch flights in real-time!")
    print("💡 Check MongoDB Compass to see data being stored!")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(60)  # Check every minute
            active_count = sum(1 for sim in simulators if sim.is_running)
            if active_count == 0:
                print("\n🏁 All flights completed!")
                break
            print(f"📊 {active_count} flights currently in progress...")
    except KeyboardInterrupt:
        print("\n⏹️ Stopping all flights...")
        for simulator in simulators:
            simulator.stop_simulation()

if __name__ == "__main__":
    run_multiple_flights()
