# 🛩️ FlightAware System - Complete Setup Guide

## 📋 Prerequisites Checklist

- ✅ Python 3.8+ installed
- ✅ MongoDB installed and running
- ✅ All dependencies installed (flask, flask-cors, pymongo, requests)

## 🚀 Step-by-Step Running Instructions

### Step 1: Start MongoDB
**Option A: Using MongoDB Compass (Recommended)**
1. Open MongoDB Compass
2. Connect to `mongodb://localhost:27017`
3. Create a new database called `flightaware`

**Option B: Using Command Line**
```bash
# Start MongoDB service
net start MongoDB
```

### Step 2: Start the Backend Server
```bash
cd backend
python app.py
```
**Expected Output:**
```
* Running on http://127.0.0.1:5000
* Debug mode: on
```

### Step 3: Open the Frontend
1. Navigate to the `frontend` folder
2. Open `index.html` in your web browser
3. **Important**: For MapBox to work, you need to:
   - Get a free MapBox token from https://mapbox.com
   - Replace `your_token_here` in `frontend/script.js` line 4

## 🧪 Testing the APIs

### Test 1: Check if Backend is Running
Open your browser and go to: `http://localhost:5000`
**Expected Response:**
```json
{"message": "FlightAware Backend Running"}
```

### Test 2: Send Flight Data (POST API)
**Using Browser (Easiest):**
1. Open the frontend (`frontend/index.html`)
2. Fill in the form with sample data:
   - Flight ID: `AA123`
   - Latitude: `40.7128`
   - Longitude: `-74.0060`
   - Altitude: `35000`
   - Speed: `450`
   - Heading: `270`
   - Status: `en-route`
3. Click "Send Data"

**Using cURL:**
```bash
curl -X POST http://localhost:5000/api/flight/update \
  -H "Content-Type: application/json" \
  -d '{
    "flight_id": "AA123",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "altitude": 35000,
    "speed": 450,
    "heading": 270,
    "status": "en-route",
    "timestamp": "2024-01-15T10:30:00Z"
  }'
```

### Test 3: Get Flight Location (GET API)
**Using Browser:**
1. Go to: `http://localhost:5000/api/flight/AA123`

**Using cURL:**
```bash
curl http://localhost:5000/api/flight/AA123
```

### Test 4: Get Flight at Specific Time
**Using Browser:**
1. Go to: `http://localhost:5000/api/flight/AA123/location?timestamp=2024-01-15T10:30:00Z`

### Test 5: Get All Active Flights
**Using Browser:**
1. Go to: `http://localhost:5000/api/flights`

## 🗄️ MongoDB Compass - Database Structure

### Database: `flightaware`

#### Collection 1: `flights` (Active Flights)
```json
{
  "_id": ObjectId("..."),
  "flight_id": "AA123",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "altitude": 35000,
  "speed": 450,
  "heading": 270,
  "status": "en-route",
  "last_updated": ISODate("2024-01-15T10:30:00Z"),
  "received_at": ISODate("2024-01-15T10:30:05Z"),
  "aircraft_type": "Boeing 737",
  "airline": "American Airlines",
  "departure": "JFK",
  "arrival": "LAX"
}
```

#### Collection 2: `flight_tracking` (Complete Tracking History)
```json
{
  "_id": ObjectId("..."),
  "flight_id": "AA123",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "altitude": 35000,
  "speed": 450,
  "heading": 270,
  "status": "en-route",
  "timestamp": ISODate("2024-01-15T10:30:00Z"),
  "received_at": ISODate("2024-01-15T10:30:05Z")
}
```

#### Collection 3: `flight_logs` (Completed Flights)
```json
{
  "_id": ObjectId("..."),
  "flight_id": "AA123",
  "path": [
    {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "altitude": 35000,
      "speed": 450,
      "heading": 270,
      "status": "en-route",
      "timestamp": ISODate("2024-01-15T10:30:00Z")
    }
  ],
  "completed_at": ISODate("2024-01-15T12:30:00Z")
}
```

## 🔍 How to Monitor Data in MongoDB Compass

### 1. View Active Flights
- Open MongoDB Compass
- Connect to `mongodb://localhost:27017`
- Select database `flightaware`
- Click on collection `flights`
- You'll see all currently active flights

### 2. View Tracking History
- Click on collection `flight_tracking`
- This shows every tracking point for all flights
- Use filters to find specific flights: `{"flight_id": "AA123"}`

### 3. View Completed Flights
- Click on collection `flight_logs`
- This shows completed flights with their full paths

### 4. Real-time Monitoring
- Keep MongoDB Compass open while using the system
- Watch data appear in real-time as you send flight data
- Use the refresh button to see updates

## 🧪 Automated Testing

### Run the Test Script
```bash
cd backend
python test_flight_system.py
```

**This will:**
1. Send sample flight data
2. Simulate a complete flight journey
3. Test all API endpoints
4. Show you the complete workflow

## 🗺️ Frontend Features

### 1. Send Flight Data Form
- Fill in flight information
- Click "Send Data" to send to API
- See success/error messages

### 2. Track Flight
- Enter flight ID to track
- Optionally specify a time
- See flight information and location

### 3. Interactive Map
- View all active flights on map
- Click on flights for details
- See flight paths and trajectories

### 4. Active Flights List
- See all currently active flights
- Click on any flight to track it
- Real-time updates every 30 seconds

## 🚨 Troubleshooting

### Backend Not Starting
```bash
# Check if port 5000 is in use
netstat -an | findstr :5000

# Kill process using port 5000
taskkill /PID <process_id> /F
```

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
net start | findstr MongoDB

# Start MongoDB if not running
net start MongoDB
```

### Frontend Map Not Loading
1. Get MapBox token from https://mapbox.com
2. Replace token in `frontend/script.js` line 4
3. Refresh the page

### API Not Responding
1. Check if backend is running on http://localhost:5000
2. Check browser console for CORS errors
3. Verify MongoDB is connected

## 📊 Sample Data for Testing

### Sample Flight Data
```json
{
  "flight_id": "AA123",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "altitude": 35000,
  "speed": 450,
  "heading": 270,
  "status": "en-route",
  "timestamp": "2024-01-15T10:30:00Z",
  "aircraft_type": "Boeing 737",
  "airline": "American Airlines",
  "departure": "JFK",
  "arrival": "LAX"
}
```

### Multiple Flight Scenarios
1. **Short Flight**: NYC to Boston (1 hour)
2. **Long Flight**: NYC to LA (6 hours)
3. **International**: NYC to London (8 hours)
4. **Delayed Flight**: Show delay status

## 🎯 Complete Workflow Example

1. **Start System**: Backend + MongoDB + Frontend
2. **Send Initial Data**: Use form to send flight AA123
3. **Check MongoDB**: See data in `flights` and `flight_tracking` collections
4. **Track Flight**: Use frontend to track AA123
5. **Send More Data**: Send additional tracking points
6. **View on Map**: See flight moving on map
7. **Complete Flight**: Mark flight as completed
8. **Check Logs**: See completed flight in `flight_logs` collection

## 🚀 Production Deployment Notes

- Change MongoDB URI for production
- Add authentication and security
- Use environment variables for configuration
- Implement proper error handling
- Add logging and monitoring

---

**🎉 Your FlightAware system is now ready to use!**
