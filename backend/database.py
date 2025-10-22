from pymongo import MongoClient
from backend import config

# Initialize MongoDB connection
client = MongoClient(config.MONGO_URI)
db = client[config.DB_NAME]

# Collections
flights = db.flights
tracking = db.flight_tracking
logs = db.flight_logs
