import requests
from datetime import datetime
import time

url = "http://127.0.0.1:5000/api/flight/update"

# simulate a flight moving from Lahore to Karachi
flight_id = "PK301"
path = [
    (31.582045, 74.329376),  # Lahore
    (30.0, 71.5),
    (28.5, 69.5),
    (27.7, 67.7),
    (24.8607, 67.0011)       # Karachi
]

for i, (lat, lon) in enumerate(path):
    data = {
        "flight_id": flight_id,
        "latitude": lat,
        "longitude": lon,
        "altitude": 35000 - i * 2000,
        "speed": 800 - i * 50,
        "status": "en route",
        "timestamp": datetime.now().isoformat()
    }
    res = requests.post(url, json=data)
    print(res.json())
    time.sleep(1)  # 1 second delay between updates
