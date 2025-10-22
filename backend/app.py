from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from backend import database
import json
import math

app = Flask(__name__)
CORS(app)

# Airport coordinates database
AIRPORTS = {
    "JFK": {"lat": 40.6413, "lon": -73.7781, "name": "John F. Kennedy International"},
    "LAX": {"lat": 33.9416, "lon": -118.4085, "name": "Los Angeles International"},
    "ORD": {"lat": 41.9786, "lon": -87.9048, "name": "Chicago O'Hare International"},
    "DFW": {"lat": 32.8968, "lon": -97.0380, "name": "Dallas/Fort Worth International"},
    "ATL": {"lat": 33.6407, "lon": -84.4277, "name": "Hartsfield-Jackson Atlanta International"},
    "DEN": {"lat": 39.8561, "lon": -104.6737, "name": "Denver International"},
    "SFO": {"lat": 37.6213, "lon": -122.3790, "name": "San Francisco International"},
    "SEA": {"lat": 47.4502, "lon": -122.3088, "name": "Seattle-Tacoma International"},
    "BOS": {"lat": 42.3656, "lon": -71.0096, "name": "Logan International"},
    "MIA": {"lat": 25.7959, "lon": -80.2871, "name": "Miami International"},
    "LHR": {"lat": 51.4700, "lon": -0.4543, "name": "London Heathrow"},
    "CDG": {"lat": 49.0097, "lon": 2.5479, "name": "Charles de Gaulle"},
    "NRT": {"lat": 35.7720, "lon": 140.3928, "name": "Narita International"},
    "DXB": {"lat": 25.2532, "lon": 55.3657, "name": "Dubai International"}
}

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers"""
    R = 6371  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2) * math.sin(dlat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2) * math.sin(dlon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calculate_route_progress(current_lat, current_lon, source, destination):
    """Calculate flight progress percentage from source to destination"""
    if not source or not destination or source not in AIRPORTS or destination not in AIRPORTS:
        return 0
    
    source_coords = AIRPORTS[source]
    dest_coords = AIRPORTS[destination]
    
    # Calculate total distance
    total_distance = calculate_distance(
        source_coords["lat"], source_coords["lon"],
        dest_coords["lat"], dest_coords["lon"]
    )
    
    # Calculate distance from current position to destination
    current_to_dest = calculate_distance(
        current_lat, current_lon,
        dest_coords["lat"], dest_coords["lon"]
    )
    
    # Calculate progress percentage
    if total_distance == 0:
        return 100
    
    progress = max(0, min(100, ((total_distance - current_to_dest) / total_distance) * 100))
    return round(progress, 2)

def get_route_waypoints(source, destination, num_points=20):
    """Generate waypoints for a flight route"""
    if not source or not destination or source not in AIRPORTS or destination not in AIRPORTS:
        return []
    
    source_coords = AIRPORTS[source]
    dest_coords = AIRPORTS[destination]
    
    waypoints = []
    for i in range(num_points + 1):
        progress = i / num_points
        lat = source_coords["lat"] + (dest_coords["lat"] - source_coords["lat"]) * progress
        lon = source_coords["lon"] + (dest_coords["lon"] - source_coords["lon"]) * progress
        waypoints.append({"lat": lat, "lon": lon, "progress": progress * 100})
    
    return waypoints


# --------------------------
#  1️⃣ Add or update flight data (Enhanced with better validation)
# --------------------------
@app.route('/api/flight/update', methods=['POST'])
def update_flight():
    data = request.get_json()

    # Enhanced required fields for realistic flight tracking
    required_fields = ["flight_id", "latitude", "longitude", "altitude", "speed", "heading", "status", "timestamp"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing one or more required fields"}), 400

    # Validate data types and ranges
    try:
        data["latitude"] = float(data["latitude"])
        data["longitude"] = float(data["longitude"])
        data["altitude"] = float(data["altitude"])
        data["speed"] = float(data["speed"])
        data["heading"] = float(data["heading"])
        
        # Validate coordinate ranges
        if not (-90 <= data["latitude"] <= 90):
            return jsonify({"error": "Latitude must be between -90 and 90"}), 400
        if not (-180 <= data["longitude"] <= 180):
            return jsonify({"error": "Longitude must be between -180 and 180"}), 400
        if data["altitude"] < 0:
            return jsonify({"error": "Altitude must be positive"}), 400
        if data["speed"] < 0:
            return jsonify({"error": "Speed must be positive"}), 400
        if not (0 <= data["heading"] <= 360):
            return jsonify({"error": "Heading must be between 0 and 360"}), 400
            
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid data types for numeric fields"}), 400

    # Convert timestamp to datetime
    try:
        data["timestamp"] = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": "Invalid timestamp format. Use ISO format"}), 400

    # Add additional metadata
    data["received_at"] = datetime.now()
    
    # Insert into tracking collection
    database.tracking.insert_one(data)

    # Update or create flight entry with additional fields
    flight_update = {
        "flight_id": data["flight_id"],
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "altitude": data["altitude"],
        "speed": data["speed"],
        "heading": data["heading"],
        "status": data["status"],
        "last_updated": data["timestamp"],
        "received_at": data["received_at"]
    }
    
    # Add optional fields if provided
    optional_fields = ["aircraft_type", "airline", "departure", "arrival", "route", "destination", "source"]
    for field in optional_fields:
        if field in data:
            flight_update[field] = data[field]
    
    # Calculate progress towards destination if both source and destination are provided
    if "source" in data and "destination" in data:
        flight_update["route_progress"] = calculate_route_progress(
            data["latitude"], data["longitude"], 
            data.get("source"), data.get("destination")
        )
        
        # Check if flight has reached destination (progress >= 95%)
        if flight_update["route_progress"] >= 95:
            flight_update["status"] = "landed"
            # Mark for auto-completion
            flight_update["ready_for_completion"] = True

    database.flights.update_one(
        {"flight_id": data["flight_id"]},
        {"$set": flight_update},
        upsert=True
    )

    return jsonify({
        "status": "success",
        "message": f"Data received for flight {data['flight_id']}",
        "flight_id": data["flight_id"],
        "timestamp": data["timestamp"].isoformat()
    })


# --------------------------
#  2️⃣ Get latest location
# --------------------------
@app.route('/api/flight/<flight_id>', methods=['GET'])
def get_latest_flight_data(flight_id):
    flight = database.flights.find_one({"flight_id": flight_id})
    if not flight:
        return jsonify({"error": "Flight not found"}), 404

    flight["_id"] = str(flight["_id"])
    flight["last_updated"] = flight["last_updated"].isoformat()
    flight["received_at"] = flight["received_at"].isoformat()
    return jsonify(flight)


# --------------------------
#  2.5️⃣ Get flight location at specific time
# --------------------------
@app.route('/api/flight/<flight_id>/location', methods=['GET'])
def get_flight_location_at_time(flight_id):
    # Get timestamp parameter
    timestamp_str = request.args.get('timestamp')
    if not timestamp_str:
        return jsonify({"error": "Timestamp parameter required"}), 400
    
    try:
        target_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": "Invalid timestamp format. Use ISO format"}), 400
    
    # Find the closest tracking point to the requested time
    tracking_points = list(database.tracking.find({
        "flight_id": flight_id,
        "timestamp": {"$lte": target_time}
    }).sort("timestamp", -1).limit(1))
    
    if not tracking_points:
        return jsonify({"error": "No tracking data found for the specified time"}), 404
    
    point = tracking_points[0]
    point["_id"] = str(point["_id"])
    point["timestamp"] = point["timestamp"].isoformat()
    point["received_at"] = point["received_at"].isoformat()
    
    return jsonify({
        "flight_id": flight_id,
        "requested_time": target_time.isoformat(),
        "actual_time": point["timestamp"],
        "location": {
            "latitude": point["latitude"],
            "longitude": point["longitude"],
            "altitude": point["altitude"],
            "speed": point["speed"],
            "heading": point["heading"],
            "status": point["status"]
        }
    })


# --------------------------
#  3️⃣ Get full tracking history
# --------------------------
@app.route('/api/flight/<flight_id>/history', methods=['GET'])
def get_flight_history(flight_id):
    history = list(database.tracking.find({"flight_id": flight_id}).sort("timestamp", 1))
    if not history:
        return jsonify({"error": "No tracking data found"}), 404

    for item in history:
        item["_id"] = str(item["_id"])
        item["timestamp"] = item["timestamp"].isoformat()

    return jsonify(history)


# --------------------------
#  4️⃣ Mark flight as completed (move to logs)
# --------------------------
@app.route('/api/flight/<flight_id>/complete', methods=['POST'])
def complete_flight(flight_id):
    # Find tracking data
    path_data = list(database.tracking.find({"flight_id": flight_id}).sort("timestamp", 1))
    if not path_data:
        return jsonify({"error": "No data for this flight"}), 404

    # Get flight details
    flight_details = database.flights.find_one({"flight_id": flight_id})
    
    # Save to logs with complete flight information
    log_entry = {
        "flight_id": flight_id,
        "path": path_data,
        "flight_details": flight_details,
        "completed_at": datetime.now(),
        "total_tracking_points": len(path_data),
        "departure_time": path_data[0]["timestamp"] if path_data else None,
        "arrival_time": path_data[-1]["timestamp"] if path_data else None,
        "total_duration_minutes": 0
    }
    
    # Calculate total duration
    if path_data and len(path_data) > 1:
        start_time = path_data[0]["timestamp"]
        end_time = path_data[-1]["timestamp"]
        duration = (end_time - start_time).total_seconds() / 60
        log_entry["total_duration_minutes"] = round(duration, 2)

    database.logs.insert_one(log_entry)

    # Remove from current collections
    database.tracking.delete_many({"flight_id": flight_id})
    database.flights.delete_one({"flight_id": flight_id})

    return jsonify({
        "status": "success", 
        "message": f"Flight {flight_id} completed and logged.",
        "total_points": len(path_data),
        "duration_minutes": log_entry["total_duration_minutes"]
    })


# --------------------------
#  5️⃣ Get all active flights
# --------------------------
@app.route('/api/flights', methods=['GET'])
def get_all_active_flights():
    active = list(database.flights.find())
    for f in active:
        f["_id"] = str(f["_id"])
        f["last_updated"] = f["last_updated"].isoformat()
    return jsonify(active)


# --------------------------
#  6️⃣ Get all completed flights
# --------------------------
@app.route('/api/flights/logs', methods=['GET'])
def get_all_completed_flights():
    logs = list(database.logs.find().sort("completed_at", -1))
    for log in logs:
        log["_id"] = str(log["_id"])
        log["completed_at"] = log["completed_at"].isoformat()
        if log.get("departure_time"):
            log["departure_time"] = log["departure_time"].isoformat()
        if log.get("arrival_time"):
            log["arrival_time"] = log["arrival_time"].isoformat()
    return jsonify(logs)


# --------------------------
#  7️⃣ Auto-complete flights that have landed
# --------------------------
@app.route('/api/flights/auto-complete', methods=['POST'])
def auto_complete_landed_flights():
    # Find flights with status "landed" or ready for completion
    landed_flights = list(database.flights.find({
        "$or": [
            {"status": "landed"},
            {"ready_for_completion": True},
            {"route_progress": {"$gte": 95}}
        ]
    }))
    completed_count = 0
    
    for flight in landed_flights:
        flight_id = flight["flight_id"]
        
        # Get tracking data
        path_data = list(database.tracking.find({"flight_id": flight_id}).sort("timestamp", 1))
        if path_data:
            # Get flight details
            flight_details = database.flights.find_one({"flight_id": flight_id})
            
            # Calculate flight statistics
            total_duration = 0
            departure_time = path_data[0]["timestamp"] if path_data else None
            arrival_time = path_data[-1]["timestamp"] if path_data else None
            
            if path_data and len(path_data) > 1:
                start_time = path_data[0]["timestamp"]
                end_time = path_data[-1]["timestamp"]
                total_duration = (end_time - start_time).total_seconds() / 60
            
            # Save to logs with complete flight information
            log_entry = {
                "flight_id": flight_id,
                "path": path_data,
                "flight_details": flight_details,
                "completed_at": datetime.now(),
                "total_tracking_points": len(path_data),
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "total_duration_minutes": round(total_duration, 2),
                "auto_completed": True,
                "route": {
                    "source": flight.get("source", "Unknown"),
                    "destination": flight.get("destination", "Unknown"),
                    "final_progress": flight.get("route_progress", 0)
                },
                "flight_summary": {
                    "aircraft_type": flight.get("aircraft_type", "Unknown"),
                    "airline": flight.get("airline", "Unknown"),
                    "departure_airport": flight.get("source", "Unknown"),
                    "arrival_airport": flight.get("destination", "Unknown"),
                    "total_distance_km": calculate_flight_distance(path_data) if path_data else 0
                }
            }
            
            database.logs.insert_one(log_entry)
            
            # Remove from active collections
            database.tracking.delete_many({"flight_id": flight_id})
            database.flights.delete_one({"flight_id": flight_id})
            
            completed_count += 1
            print(f"✅ Auto-completed flight {flight_id} (Duration: {round(total_duration, 2)} minutes)")
    
    return jsonify({
        "status": "success",
        "message": f"Auto-completed {completed_count} landed flights",
        "completed_count": completed_count
    })

def calculate_flight_distance(path_data):
    """Calculate total distance flown by the flight"""
    if not path_data or len(path_data) < 2:
        return 0
    
    total_distance = 0
    for i in range(1, len(path_data)):
        prev_point = path_data[i-1]
        curr_point = path_data[i]
        distance = calculate_distance(
            prev_point["latitude"], prev_point["longitude"],
            curr_point["latitude"], curr_point["longitude"]
        )
        total_distance += distance
    
    return round(total_distance, 2)


# --------------------------
#  8️⃣ Get flight statistics
# --------------------------
@app.route('/api/flights/stats', methods=['GET'])
def get_flight_statistics():
    active_count = database.flights.count_documents({})
    completed_count = database.logs.count_documents({})
    total_tracking_points = database.tracking.count_documents({})
    
    # Get recent activity
    recent_flights = list(database.flights.find().sort("last_updated", -1).limit(5))
    recent_completed = list(database.logs.find().sort("completed_at", -1).limit(5))
    
    return jsonify({
        "active_flights": active_count,
        "completed_flights": completed_count,
        "total_tracking_points": total_tracking_points,
        "recent_active": recent_flights,
        "recent_completed": recent_completed
    })


# --------------------------
#  9️⃣ Get flight route and destination info
# --------------------------
@app.route('/api/flight/<flight_id>/route', methods=['GET'])
def get_flight_route(flight_id):
    flight = database.flights.find_one({"flight_id": flight_id})
    if not flight:
        return jsonify({"error": "Flight not found"}), 404
    
    source = flight.get("source")
    destination = flight.get("destination")
    
    if not source or not destination:
        return jsonify({"error": "Flight route information not available"}), 404
    
    # Get route waypoints
    waypoints = get_route_waypoints(source, destination)
    
    # Get current progress
    current_progress = flight.get("route_progress", 0)
    
    # Get source and destination info
    source_info = AIRPORTS.get(source, {})
    dest_info = AIRPORTS.get(destination, {})
    
    return jsonify({
        "flight_id": flight_id,
        "source": {
            "code": source,
            "name": source_info.get("name", source),
            "coordinates": {
                "lat": source_info.get("lat", 0),
                "lon": source_info.get("lon", 0)
            }
        },
        "destination": {
            "code": destination,
            "name": dest_info.get("name", destination),
            "coordinates": {
                "lat": dest_info.get("lat", 0),
                "lon": dest_info.get("lon", 0)
            }
        },
        "waypoints": waypoints,
        "current_progress": current_progress,
        "current_position": {
            "lat": flight.get("latitude", 0),
            "lon": flight.get("longitude", 0)
        }
    })


# --------------------------
#  🔟 Get all airports
# --------------------------
@app.route('/api/airports', methods=['GET'])
def get_airports():
    return jsonify(AIRPORTS)


# --------------------------
#  1️⃣1️⃣ Get flights by route
# --------------------------
@app.route('/api/flights/route/<source>/<destination>', methods=['GET'])
def get_flights_by_route(source, destination):
    flights = list(database.flights.find({
        "source": source,
        "destination": destination
    }))
    
    for flight in flights:
        flight["_id"] = str(flight["_id"])
        flight["last_updated"] = flight["last_updated"].isoformat()
    
    return jsonify(flights)


# --------------------------
#  1️⃣2️⃣ Get flight path with destination tracking
# --------------------------
@app.route('/api/flight/<flight_id>/path', methods=['GET'])
def get_flight_path_with_destination(flight_id):
    # Get flight info
    flight = database.flights.find_one({"flight_id": flight_id})
    if not flight:
        return jsonify({"error": "Flight not found"}), 404
    
    # Get tracking history
    tracking_points = list(database.tracking.find({"flight_id": flight_id}).sort("timestamp", 1))
    
    # Get route waypoints
    source = flight.get("source")
    destination = flight.get("destination")
    waypoints = get_route_waypoints(source, destination) if source and destination else []
    
    # Format tracking points
    for point in tracking_points:
        point["_id"] = str(point["_id"])
        point["timestamp"] = point["timestamp"].isoformat()
    
    return jsonify({
        "flight_id": flight_id,
        "source": source,
        "destination": destination,
        "tracking_points": tracking_points,
        "route_waypoints": waypoints,
        "current_progress": flight.get("route_progress", 0)
    })


@app.route('/')
def home():
    return jsonify({"message": "FlightAware Backend Running"})


if __name__ == '__main__':
    app.run(debug=True)
