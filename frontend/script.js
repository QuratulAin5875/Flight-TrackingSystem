// FlightAware Frontend JavaScript with Real-Time Tracking
// Using OpenStreetMap for better visualization

// Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Global variables
let map;
let flightMarkers = [];
let flightPaths = [];
let currentFlight = null;

// Live tracking functionality
let liveTrackingInterval = null;
let trackedFlights = new Set();

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    setupEventListeners();
    loadActiveFlights();
    loadSystemStats();
});

// Initialize Leaflet map (OpenStreetMap)
function initializeMap() {
    map = L.map('map').setView([40.7128, -74.0060], 6);
    
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18
}).addTo(map);

    console.log('Map loaded successfully');
}

// Setup event listeners
function setupEventListeners() {
    // Flight form submission
    document.getElementById('flightForm').addEventListener('submit', function(e) {
        e.preventDefault();
        sendFlightData();
    });
}

// Send flight data to the API
async function sendFlightData() {
    const formData = {
        flight_id: document.getElementById('flightId').value,
        latitude: parseFloat(document.getElementById('latitude').value),
        longitude: parseFloat(document.getElementById('longitude').value),
        altitude: parseFloat(document.getElementById('altitude').value),
        speed: parseFloat(document.getElementById('speed').value),
        heading: parseFloat(document.getElementById('heading').value),
        status: document.getElementById('status').value,
        timestamp: new Date().toISOString(),
        source: document.getElementById('source').value,
        destination: document.getElementById('destination').value
    };

    try {
        const response = await fetch(`${API_BASE_URL}/flight/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            showAlert('success', `Flight data sent successfully for ${formData.flight_id}`);
            // Clear form
            document.getElementById('flightForm').reset();
            // Refresh active flights
            loadActiveFlights();
        } else {
            showAlert('error', result.error || 'Failed to send flight data');
        }
    } catch (error) {
        showAlert('error', 'Network error: ' + error.message);
    }
}

// Track a specific flight
async function trackFlight() {
    const flightId = document.getElementById('trackFlightId').value;
    const trackTime = document.getElementById('trackTime').value;
    
    if (!flightId) {
        showAlert('error', 'Please enter a flight ID');
        return;
    }

    try {
        let url = `${API_BASE_URL}/flight/${flightId}`;
        if (trackTime) {
            url += `/location?timestamp=${new Date(trackTime).toISOString()}`;
        }

        const response = await fetch(url);
        const result = await response.json();

        if (response.ok) {
            displayFlightInfo(result);
            if (result.location) {
                // Show location on map
                showFlightOnMap(result);
            } else {
                // Show current location
                showFlightOnMap(result);
                // Start live tracking for current flight
                startLiveTracking(flightId);
            }
        } else {
            showAlert('error', result.error || 'Flight not found');
        }
    } catch (error) {
        showAlert('error', 'Network error: ' + error.message);
    }
}

// Display flight information
function displayFlightInfo(flightData) {
    const flightInfo = document.getElementById('flightInfo');
    
    if (flightData.location) {
        // Time-based query result
        flightInfo.innerHTML = `
            <h4>✈️ ${flightData.flight_id} <span class="historical-indicator">📅 HISTORICAL</span></h4>
            <p><strong>Requested Time:</strong> ${new Date(flightData.requested_time).toLocaleString()}</p>
            <p><strong>Actual Time:</strong> ${new Date(flightData.actual_time).toLocaleString()}</p>
            <p><strong>Location:</strong> ${flightData.location.latitude.toFixed(6)}, ${flightData.location.longitude.toFixed(6)}</p>
            <p><strong>Altitude:</strong> ${flightData.location.altitude} ft</p>
            <p><strong>Speed:</strong> ${flightData.location.speed} knots</p>
            <p><strong>Heading:</strong> ${flightData.location.heading}°</p>
            <p><strong>Status:</strong> <span class="status ${flightData.location.status}">${flightData.location.status}</span></p>
        `;
    } else {
        // Current flight data with live tracking option
        const isLiveTracking = trackedFlights.has(flightData.flight_id);
        flightInfo.innerHTML = `
            <h4>✈️ ${flightData.flight_id} ${isLiveTracking ? '<span class="live-indicator">🔴 LIVE</span>' : ''}</h4>
            <p><strong>Last Updated:</strong> ${new Date(flightData.last_updated).toLocaleString()}</p>
            <p><strong>Location:</strong> ${flightData.latitude.toFixed(6)}, ${flightData.longitude.toFixed(6)}</p>
            <p><strong>Altitude:</strong> ${flightData.altitude} ft</p>
            <p><strong>Speed:</strong> ${flightData.speed} knots</p>
            <p><strong>Heading:</strong> ${flightData.heading}°</p>
            <p><strong>Status:</strong> <span class="status ${flightData.status}">${flightData.status}</span></p>
            <div class="tracking-controls">
                ${!isLiveTracking ? 
                    `<button onclick="startLiveTracking('${flightData.flight_id}')" class="start-tracking-btn">🔴 Start Live Tracking</button>` :
                    `<button onclick="stopLiveTracking('${flightData.flight_id}')" class="stop-tracking-btn">⏹️ Stop Live Tracking</button>`
                }
            </div>
        `;
    }
}

// Show flight on map
function showFlightOnMap(flightData) {
    const coords = flightData.location ? 
        [flightData.location.latitude, flightData.location.longitude] :
        [flightData.latitude, flightData.longitude];

    // Remove existing markers for this flight
    removeFlightMarkers(flightData.flight_id);

    // Create custom icon
    const flightIcon = L.divIcon({
        className: 'flight-marker',
        html: `<div style="background: ${getStatusColor(flightData.status)}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>`,
        iconSize: [12, 12],
        iconAnchor: [6, 6]
    });

    // Add new marker
    const marker = L.marker(coords, { icon: flightIcon })
        .bindPopup(`
            <div>
                <h3>✈️ ${flightData.flight_id}</h3>
                <p><strong>Status:</strong> ${flightData.location?.status || flightData.status}</p>
                <p><strong>Altitude:</strong> ${flightData.location?.altitude || flightData.altitude} ft</p>
                <p><strong>Speed:</strong> ${flightData.location?.speed || flightData.speed} knots</p>
                <p><strong>Progress:</strong> ${flightData.route_progress || 0}%</p>
            </div>
        `)
        .addTo(map);

    flightMarkers.push({ flightId: flightData.flight_id, marker: marker });

    // Center map on flight
    map.setView(coords, 8);
}

// Load and display active flights
async function loadActiveFlights() {
    try {
        const response = await fetch(`${API_BASE_URL}/flights`);
        const flights = await response.json();

        const activeFlightsDiv = document.getElementById('activeFlights');
        
        if (flights.length === 0) {
            activeFlightsDiv.innerHTML = '<p>No active flights</p>';
            return;
        }

        activeFlightsDiv.innerHTML = flights.map(flight => {
            const isLiveTracking = trackedFlights.has(flight.flight_id);
            return `
                <div class="flight-item">
                    <div onclick="trackFlightById('${flight.flight_id}')" class="flight-info">
                        <h4>✈️ ${flight.flight_id} ${isLiveTracking ? '<span class="live-indicator">🔴 LIVE</span>' : ''}</h4>
                        <p><strong>Status:</strong> <span class="status ${flight.status}">${flight.status}</span></p>
                        <p><strong>Altitude:</strong> ${flight.altitude} ft</p>
                        <p><strong>Speed:</strong> ${flight.speed} knots</p>
                        <p><strong>Last Update:</strong> ${new Date(flight.last_updated).toLocaleString()}</p>
                    </div>
                    <div class="flight-actions">
                        ${!isLiveTracking ? 
                            `<button onclick="startLiveTracking('${flight.flight_id}')" class="start-tracking-btn">🔴 Live</button>` :
                            `<button onclick="stopLiveTracking('${flight.flight_id}')" class="stop-tracking-btn">⏹️ Stop</button>`
                        }
                        <button onclick="trackFlightById('${flight.flight_id}')" class="track-btn">📍 Track</button>
                    </div>
                </div>
            `;
        }).join('');

        // Show all flights on map
        showAllFlightsOnMap(flights);

    } catch (error) {
        showAlert('error', 'Failed to load active flights: ' + error.message);
    }
}

// Track flight by ID (for clicking on flight list)
function trackFlightById(flightId) {
    document.getElementById('trackFlightId').value = flightId;
    trackFlight();
}

// Show all flights on map with their paths
function showAllFlightsOnMap(flights) {
    // Clear existing markers
    clearMap();

    if (flights.length === 0) return;

    const bounds = L.latLngBounds();

    flights.forEach(flight => {
        const coords = [flight.latitude, flight.longitude];
        bounds.extend(coords);

        // Create custom icon
        const flightIcon = L.divIcon({
            className: 'flight-marker',
            html: `<div style="background: ${getStatusColor(flight.status)}; width: 10px; height: 10px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>`,
            iconSize: [10, 10],
            iconAnchor: [5, 5]
        });

        const marker = L.marker(coords, { icon: flightIcon })
            .bindPopup(`
                <div>
                    <h3>✈️ ${flight.flight_id}</h3>
                    <p><strong>Status:</strong> ${flight.status}</p>
                    <p><strong>Altitude:</strong> ${flight.altitude} ft</p>
                    <p><strong>Speed:</strong> ${flight.speed} knots</p>
                    <p><strong>Route:</strong> ${flight.source || 'Unknown'} → ${flight.destination || 'Unknown'}</p>
                    <p><strong>Progress:</strong> ${flight.route_progress || 0}%</p>
                    <button onclick="showFlightPath('${flight.flight_id}')" style="margin-top: 10px; padding: 5px 10px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer;">Show Complete Path</button>
                </div>
            `)
            .addTo(map);

        flightMarkers.push({ flightId: flight.flight_id, marker: marker });
    });

    // Fit map to show all flights
    map.fitBounds(bounds, { padding: [20, 20] });
}

// Get color based on flight status
function getStatusColor(status) {
    const colors = {
        'en-route': '#667eea',
        'departed': '#4299e1',
        'landed': '#48bb78',
        'delayed': '#f56565',
        'climbing': '#ed8936',
        'cruising': '#667eea',
        'descending': '#9f7aea'
    };
    return colors[status] || '#667eea';
}

// Remove markers for a specific flight
function removeFlightMarkers(flightId) {
    flightMarkers = flightMarkers.filter(item => {
        if (item.flightId === flightId) {
            map.removeLayer(item.marker);
            return false;
        }
        return true;
    });
}

// Clear all markers from map
function clearMap() {
    flightMarkers.forEach(item => map.removeLayer(item.marker));
    flightMarkers = [];
    
    clearFlightPaths();
}

// Center map on default location
function centerMap() {
    map.setView([40.7128, -74.0060], 6);
}

// Show alert messages
function showAlert(type, message) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());

    // Create new alert
    const alert = document.createElement('div');
    alert.className = `alert ${type}`;
    alert.textContent = message;
    
    // Insert at the top of the sidebar
    const sidebar = document.querySelector('.sidebar');
    sidebar.insertBefore(alert, sidebar.firstChild);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

// Live tracking functionality
function startLiveTracking(flightId) {
    if (!trackedFlights.has(flightId)) {
        trackedFlights.add(flightId);
        console.log(`🛩️ Started live tracking for ${flightId}`);
        
        // Update every 2 seconds for live tracking
        if (!liveTrackingInterval) {
            liveTrackingInterval = setInterval(updateLiveFlights, 2000);
        }
        
        // Immediately load the flight
        updateSingleFlight(flightId);
        
        // Show notification and update status
        showLiveNotification(flightId, 'start');
        updateLiveTrackingStatus();
    }
}

function stopLiveTracking(flightId) {
    trackedFlights.delete(flightId);
    console.log(`✋ Stopped live tracking for ${flightId}`);
    
    if (trackedFlights.size === 0 && liveTrackingInterval) {
        clearInterval(liveTrackingInterval);
        liveTrackingInterval = null;
    }
    
    // Show notification and update status
    showLiveNotification(flightId, 'stop');
    updateLiveTrackingStatus();
    
    // Refresh the active flights display
    loadActiveFlights();
}

async function updateLiveFlights() {
    for (let flightId of trackedFlights) {
        await updateSingleFlight(flightId);
    }
}

async function updateSingleFlight(flightId) {
    try {
        const response = await fetch(`${API_BASE_URL}/flight/${flightId}`);
        if (response.ok) {
            const flightData = await response.json();
            updateFlightOnMap(flightData);
            updateFlightInfo(flightData);
        } else {
            console.log(`Flight ${flightId} not found or no longer active`);
            stopLiveTracking(flightId);
        }
    } catch (error) {
        console.error(`Error updating flight ${flightId}:`, error);
    }
}

function updateFlightOnMap(flightData) {
    const coords = [flightData.longitude, flightData.latitude];
    
    // Remove existing marker for this flight
    removeFlightMarkers(flightData.flight_id);
    
    // Add updated marker
    const marker = new mapboxgl.Marker({
        color: getStatusColor(flightData.status),
        scale: 1.2
    })
    .setLngLat(coords)
    .setPopup(new mapboxgl.Popup().setHTML(`
        <div>
            <h3>✈️ ${flightData.flight_id}</h3>
            <p><strong>Status:</strong> ${flightData.status}</p>
            <p><strong>Altitude:</strong> ${flightData.altitude} ft</p>
            <p><strong>Speed:</strong> ${flightData.speed} knots</p>
            <p><strong>Heading:</strong> ${flightData.heading}°</p>
            <p><strong>Last Update:</strong> ${new Date(flightData.last_updated).toLocaleString()}</p>
        </div>
    `))
    .addTo(map);

    flightMarkers.push({ flightId: flightData.flight_id, marker: marker });
}

function updateFlightInfo(flightData) {
    const flightInfo = document.getElementById('flightInfo');
    if (flightInfo && flightInfo.innerHTML.includes(flightData.flight_id)) {
        flightInfo.innerHTML = `
            <h4>✈️ ${flightData.flight_id} <span class="live-indicator">🔴 LIVE</span></h4>
            <p><strong>Last Updated:</strong> ${new Date(flightData.last_updated).toLocaleString()}</p>
            <p><strong>Location:</strong> ${flightData.latitude.toFixed(6)}, ${flightData.longitude.toFixed(6)}</p>
            <p><strong>Altitude:</strong> ${flightData.altitude} ft</p>
            <p><strong>Speed:</strong> ${flightData.speed} knots</p>
            <p><strong>Heading:</strong> ${flightData.heading}°</p>
            <p><strong>Status:</strong> <span class="status ${flightData.status}">${flightData.status}</span></p>
            <button onclick="stopLiveTracking('${flightData.flight_id}')" class="stop-tracking-btn">Stop Live Tracking</button>
        `;
    }
}

// Start live tracking for all active flights
async function startLiveTrackingAll() {
    try {
        const response = await fetch(`${API_BASE_URL}/flights`);
        if (response.ok) {
            const flights = await response.json();
            flights.forEach(flight => {
                startLiveTracking(flight.flight_id);
            });
            showAlert('success', `Started live tracking for ${flights.length} flights`);
            updateLiveTrackingStatus();
        }
    } catch (error) {
        showAlert('error', 'Failed to start live tracking: ' + error.message);
    }
}

// Stop live tracking for all flights
function stopLiveTrackingAll() {
    const count = trackedFlights.size;
    trackedFlights.clear();
    if (liveTrackingInterval) {
        clearInterval(liveTrackingInterval);
        liveTrackingInterval = null;
    }
    showAlert('info', `Stopped live tracking for ${count} flights`);
    updateLiveTrackingStatus();
    loadActiveFlights(); // Refresh the display
}

// Update live tracking status display
function updateLiveTrackingStatus() {
    const statusDiv = document.getElementById('liveTrackingStatus');
    const liveFlightsDiv = document.getElementById('liveFlights');
    
    if (trackedFlights.size === 0) {
        statusDiv.innerHTML = '<p>No flights being tracked live</p>';
        liveFlightsDiv.innerHTML = '';
    } else {
        statusDiv.innerHTML = `<p>🔴 Live tracking ${trackedFlights.size} flight(s)</p>`;
        
        // Show live flights list
        const liveFlightsList = Array.from(trackedFlights).map(flightId => `
            <div class="live-flight-item">
                <span>✈️ ${flightId}</span>
                <button onclick="stopLiveTracking('${flightId}')" class="stop-tracking-btn">Stop</button>
            </div>
        `).join('');
        
        liveFlightsDiv.innerHTML = liveFlightsList;
    }
}

// Show live tracking notification
function showLiveNotification(flightId, action) {
    const notification = document.createElement('div');
    notification.className = 'live-notification';
    notification.innerHTML = `
        <strong>${action === 'start' ? '🔴 Started' : '⏹️ Stopped'}</strong> live tracking for ${flightId}
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Load completed flights
async function loadCompletedFlights() {
    try {
        const response = await fetch(`${API_BASE_URL}/flights/logs`);
        const completedFlights = await response.json();
        
        const completedFlightsDiv = document.getElementById('completedFlights');
        
        if (completedFlights.length === 0) {
            completedFlightsDiv.innerHTML = '<p>No completed flights</p>';
            return;
        }
        
        completedFlightsDiv.innerHTML = completedFlights.map(flight => `
            <div class="completed-flight-item">
                <h4>✈️ ${flight.flight_id}</h4>
                <p><strong>Completed:</strong> ${new Date(flight.completed_at).toLocaleString()}</p>
                <p><strong>Duration:</strong> ${flight.total_duration_minutes || 0} minutes</p>
                <p><strong>Tracking Points:</strong> ${flight.total_tracking_points || 0}</p>
                <p><strong>Route:</strong> ${flight.flight_details?.departure || 'Unknown'} → ${flight.flight_details?.arrival || 'Unknown'}</p>
                <button onclick="viewFlightPath('${flight.flight_id}')" class="view-path-btn">📍 View Path</button>
            </div>
        `).join('');
        
    } catch (error) {
        showAlert('error', 'Failed to load completed flights: ' + error.message);
    }
}

// Auto-complete flights that have landed
async function autoCompleteFlights() {
    try {
        const response = await fetch(`${API_BASE_URL}/flights/auto-complete`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (response.ok) {
            if (result.completed_count > 0) {
                showAlert('success', `Auto-completed ${result.completed_count} flights`);
                console.log(`✅ Auto-completed ${result.completed_count} flights`);
                loadActiveFlights();
                loadCompletedFlights();
                loadSystemStats();
            }
        } else {
            showAlert('error', result.message || 'Failed to auto-complete flights');
        }
    } catch (error) {
        showAlert('error', 'Failed to auto-complete flights: ' + error.message);
    }
}

// Load system statistics
async function loadSystemStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/flights/stats`);
        const stats = await response.json();
        
        const statsDiv = document.getElementById('systemStats');
        statsDiv.innerHTML = `
            <div class="stat-item">
                <strong>Active Flights:</strong> ${stats.active_flights}
            </div>
            <div class="stat-item">
                <strong>Completed Flights:</strong> ${stats.completed_flights}
            </div>
            <div class="stat-item">
                <strong>Total Tracking Points:</strong> ${stats.total_tracking_points}
            </div>
            <div class="stat-item">
                <strong>Live Tracking:</strong> ${trackedFlights.size} flights
            </div>
        `;
        
    } catch (error) {
        console.error('Failed to load system stats:', error);
    }
}

// Show complete flight path on map
async function showFlightPath(flightId) {
    try {
        const response = await fetch(`${API_BASE_URL}/flight/${flightId}/history`);
        const pathData = await response.json();

        if (response.ok && pathData.length > 0) {
            // Clear existing paths
            clearFlightPaths();
            
            // Create path coordinates
            const pathCoordinates = pathData.map(point => [point.latitude, point.longitude]);
            
            // Create polyline for the flight path
            const flightPath = L.polyline(pathCoordinates, {
                color: getStatusColor('en-route'),
                weight: 4,
                opacity: 0.8,
                smoothFactor: 1
            }).addTo(map);

            // Add start marker
            const startMarker = L.marker(pathCoordinates[0], {
                icon: L.divIcon({
                    className: 'path-marker',
                    html: '<div style="background: #48bb78; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
                    iconSize: [12, 12],
                    iconAnchor: [6, 6]
                })
            }).bindPopup(`
                <div>
                    <h3>🛫 Departure</h3>
                    <p><strong>Flight:</strong> ${flightId}</p>
                    <p><strong>Time:</strong> ${new Date(pathData[0].timestamp).toLocaleString()}</p>
                    <p><strong>Status:</strong> ${pathData[0].status}</p>
                </div>
            `).addTo(map);

            // Add end marker
            const endMarker = L.marker(pathCoordinates[pathCoordinates.length - 1], {
                icon: L.divIcon({
                    className: 'path-marker',
                    html: '<div style="background: #e53e3e; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
                    iconSize: [12, 12],
                    iconAnchor: [6, 6]
                })
            }).bindPopup(`
                <div>
                    <h3>🛬 Latest Position</h3>
                    <p><strong>Flight:</strong> ${flightId}</p>
                    <p><strong>Time:</strong> ${new Date(pathData[pathData.length - 1].timestamp).toLocaleString()}</p>
                    <p><strong>Status:</strong> ${pathData[pathData.length - 1].status}</p>
                </div>
            `).addTo(map);

            // Store path for cleanup
            flightPaths.push(flightPath);
            flightPaths.push(startMarker);
            flightPaths.push(endMarker);

            // Fit map to show the complete path
            map.fitBounds(flightPath.getBounds(), { padding: [20, 20] });

            showAlert('success', `Showing complete path for ${flightId} (${pathData.length} tracking points)`);
        } else {
            showAlert('error', 'No tracking data found for this flight');
        }
    } catch (error) {
        showAlert('error', 'Failed to load flight path: ' + error.message);
    }
}

// Clear flight paths from map
function clearFlightPaths() {
    flightPaths.forEach(path => {
        if (map.hasLayer(path)) {
            map.removeLayer(path);
        }
    });
    flightPaths = [];
}

// Show all flight paths
async function showAllFlightPaths() {
    try {
        const response = await fetch(`${API_BASE_URL}/flights`);
        const flights = await response.json();

        if (flights.length === 0) {
            showAlert('info', 'No active flights to show paths for');
            return;
        }

        // Clear existing paths
        clearFlightPaths();

        let totalPaths = 0;
        const bounds = L.latLngBounds();

        // Show path for each flight
        for (const flight of flights) {
            try {
                const pathResponse = await fetch(`${API_BASE_URL}/flight/${flight.flight_id}/history`);
                const pathData = await pathResponse.json();

                if (pathData.length > 0) {
                    // Create path coordinates
                    const pathCoordinates = pathData.map(point => [point.latitude, point.longitude]);
                    
                    // Create polyline for the flight path
                    const flightPath = L.polyline(pathCoordinates, {
                        color: getStatusColor(flight.status),
                        weight: 3,
                        opacity: 0.7,
                        smoothFactor: 1
                    }).addTo(map);

                    // Add to bounds
                    pathCoordinates.forEach(coord => bounds.extend(coord));

                    // Store path for cleanup
                    flightPaths.push(flightPath);
                    totalPaths++;
                }
            } catch (error) {
                console.error(`Failed to load path for ${flight.flight_id}:`, error);
            }
        }

        // Fit map to show all paths
        if (totalPaths > 0) {
            map.fitBounds(bounds, { padding: [20, 20] });
            showAlert('success', `Showing paths for ${totalPaths} flights`);
        } else {
            showAlert('info', 'No flight paths found');
        }

    } catch (error) {
        showAlert('error', 'Failed to load flight paths: ' + error.message);
    }
}

// Load flight route and destination info
async function loadFlightRoute() {
    const flightId = document.getElementById('routeFlightId').value;
    if (!flightId) {
        showAlert('error', 'Please enter a flight ID');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/flight/${flightId}/route`);
        const routeData = await response.json();

        if (response.ok) {
            displayRouteInfo(routeData);
            showRouteOnMap(routeData);
        } else {
            showAlert('error', routeData.error || 'Route information not available');
        }
    } catch (error) {
        showAlert('error', 'Network error: ' + error.message);
    }
}

// Display route information
function displayRouteInfo(routeData) {
    const routeInfoDiv = document.getElementById('routeInfo');
    
    routeInfoDiv.innerHTML = `
        <div class="route-details">
            <h4>✈️ ${routeData.flight_id}</h4>
            <div class="route-info-item">
                <strong>From:</strong> ${routeData.source.name} (${routeData.source.code})
            </div>
            <div class="route-info-item">
                <strong>To:</strong> ${routeData.destination.name} (${routeData.destination.code})
            </div>
            <div class="route-info-item">
                <strong>Progress:</strong> ${routeData.current_progress}%
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${routeData.current_progress}%"></div>
            </div>
            <div class="route-info-item">
                <strong>Current Position:</strong> 
                ${routeData.current_position.lat.toFixed(4)}, ${routeData.current_position.lon.toFixed(4)}
            </div>
        </div>
    `;
}

// Show route on map
function showRouteOnMap(routeData) {
    // Clear existing route
    clearRouteFromMap();
    
    // Add source marker
    const sourceMarker = new mapboxgl.Marker({
        color: '#48bb78',
        scale: 1.2
    })
    .setLngLat([routeData.source.coordinates.lon, routeData.source.coordinates.lat])
    .setPopup(new mapboxgl.Popup().setHTML(`
        <div>
            <h3>🛫 ${routeData.source.code}</h3>
            <p><strong>${routeData.source.name}</strong></p>
            <p>Departure Airport</p>
        </div>
    `))
    .addTo(map);

    // Add destination marker
    const destMarker = new mapboxgl.Marker({
        color: '#e53e3e',
        scale: 1.2
    })
    .setLngLat([routeData.destination.coordinates.lon, routeData.destination.coordinates.lat])
    .setPopup(new mapboxgl.Popup().setHTML(`
        <div>
            <h3>🛬 ${routeData.destination.code}</h3>
            <p><strong>${routeData.destination.name}</strong></p>
            <p>Arrival Airport</p>
        </div>
    `))
    .addTo(map);

    // Add route line
    if (routeData.waypoints && routeData.waypoints.length > 0) {
        const routeCoordinates = routeData.waypoints.map(point => [point.lon, point.lat]);
        
        map.addSource('route', {
            type: 'geojson',
            data: {
                type: 'Feature',
                properties: {},
                geometry: {
                    type: 'LineString',
                    coordinates: routeCoordinates
                }
            }
        });

        map.addLayer({
            id: 'route',
            type: 'line',
            source: 'route',
            layout: {
                'line-join': 'round',
                'line-cap': 'round'
            },
            paint: {
                'line-color': '#667eea',
                'line-width': 3,
                'line-opacity': 0.8
            }
        });
    }

    // Fit map to show the entire route
    const bounds = new mapboxgl.LngLatBounds();
    bounds.extend([routeData.source.coordinates.lon, routeData.source.coordinates.lat]);
    bounds.extend([routeData.destination.coordinates.lon, routeData.destination.coordinates.lat]);
    map.fitBounds(bounds, { padding: 50 });
}

// Clear route from map
function clearRouteFromMap() {
    if (map.getSource('route')) {
        map.removeLayer('route');
        map.removeSource('route');
    }
}

// Load flight progress for live tracking
async function loadFlightProgress() {
    try {
        const response = await fetch(`${API_BASE_URL}/flights`);
        const flights = await response.json();
        
        const progressDiv = document.getElementById('flightProgress');
        
        if (flights.length === 0) {
            progressDiv.innerHTML = '<p>No active flights</p>';
            return;
        }
        
        progressDiv.innerHTML = flights.map(flight => {
            const progress = flight.route_progress || 0;
            const source = flight.source || 'Unknown';
            const destination = flight.destination || 'Unknown';
            
            // Calculate flight duration if we have timestamps
            let durationText = '';
            if (flight.received_at) {
                const receivedTime = new Date(flight.received_at);
                const now = new Date();
                const durationMinutes = Math.floor((now - receivedTime) / (1000 * 60));
                durationText = ` (${durationMinutes} min)`;
            }
            
            return `
                <div class="flight-progress-item">
                    <div class="flight-progress-header">
                        <h4>✈️ ${flight.flight_id}</h4>
                        <span class="progress-percentage">${progress}%</span>
                    </div>
                    <div class="flight-progress-route">
                        <span class="source">${source}</span>
                        <span class="arrow">→</span>
                        <span class="destination">${destination}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progress}%"></div>
                    </div>
                    <div class="flight-progress-details">
                        <span>Status: ${flight.status}</span>
                        <span>Altitude: ${flight.altitude}ft</span>
                        <span>Speed: ${flight.speed}kts</span>
                        <span>Duration: ${durationText}</span>
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Failed to load flight progress:', error);
    }
}

// Enhanced flight display with destination info
function displayFlightInfo(flightData) {
    const flightInfo = document.getElementById('flightInfo');
    
    if (flightData.location) {
        // Time-based query result
        flightInfo.innerHTML = `
            <h4>✈️ ${flightData.flight_id} <span class="historical-indicator">📅 HISTORICAL</span></h4>
            <p><strong>Requested Time:</strong> ${new Date(flightData.requested_time).toLocaleString()}</p>
            <p><strong>Actual Time:</strong> ${new Date(flightData.actual_time).toLocaleString()}</p>
            <p><strong>Location:</strong> ${flightData.location.latitude.toFixed(6)}, ${flightData.location.longitude.toFixed(6)}</p>
            <p><strong>Altitude:</strong> ${flightData.location.altitude} ft</p>
            <p><strong>Speed:</strong> ${flightData.location.speed} knots</p>
            <p><strong>Heading:</strong> ${flightData.location.heading}°</p>
            <p><strong>Status:</strong> <span class="status ${flightData.location.status}">${flightData.location.status}</span></p>
        `;
    } else {
        // Current flight data with live tracking option
        const isLiveTracking = trackedFlights.has(flightData.flight_id);
        const source = flightData.source || 'Unknown';
        const destination = flightData.destination || 'Unknown';
        const progress = flightData.route_progress || 0;
        
        flightInfo.innerHTML = `
            <h4>✈️ ${flightData.flight_id} ${isLiveTracking ? '<span class="live-indicator">🔴 LIVE</span>' : ''}</h4>
            <p><strong>Route:</strong> ${source} → ${destination}</p>
            <p><strong>Progress:</strong> ${progress}%</p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${progress}%"></div>
            </div>
            <p><strong>Last Updated:</strong> ${new Date(flightData.last_updated).toLocaleString()}</p>
            <p><strong>Location:</strong> ${flightData.latitude.toFixed(6)}, ${flightData.longitude.toFixed(6)}</p>
            <p><strong>Altitude:</strong> ${flightData.altitude} ft</p>
            <p><strong>Speed:</strong> ${flightData.speed} knots</p>
            <p><strong>Heading:</strong> ${flightData.heading}°</p>
            <p><strong>Status:</strong> <span class="status ${flightData.status}">${flightData.status}</span></p>
            <div class="tracking-controls">
                ${!isLiveTracking ? 
                    `<button onclick="startLiveTracking('${flightData.flight_id}')" class="start-tracking-btn">🔴 Start Live Tracking</button>` :
                    `<button onclick="stopLiveTracking('${flightData.flight_id}')" class="stop-tracking-btn">⏹️ Stop Live Tracking</button>`
                }
                <button onclick="loadFlightRouteById('${flightData.flight_id}')" class="route-btn">🗺️ Show Route</button>
            </div>
        `;
    }
}

// Load route for specific flight
function loadFlightRouteById(flightId) {
    document.getElementById('routeFlightId').value = flightId;
    loadFlightRoute();
}

// Auto-refresh functions
setInterval(loadActiveFlights, 5000);
setInterval(loadSystemStats, 30000);
    setInterval(autoCompleteFlights, 15000);
setInterval(loadFlightProgress, 10000); // Update flight progress every 10 seconds