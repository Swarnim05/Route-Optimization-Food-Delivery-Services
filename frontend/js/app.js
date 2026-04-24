let map;
let heatmap;
let directionsRenderers = [];
let markers = [];
let deliveryCounter = 0;
let dehradunBounds = {
    north: 30.40,
    south: 30.25,
    east: 78.10,
    west: 77.95
};
// Vibrant colors for agents
const agentColors = ['#00d2ff', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

document.addEventListener("DOMContentLoaded", () => {
    bootstrap();

    document.getElementById("addDeliveryBtn").addEventListener("click", () => addDeliveryBox());
    document.getElementById("clearBtn").addEventListener("click", () => clearAll());
    document.getElementById("heatmapToggle").addEventListener("change", toggleHeatmap);
    document.getElementById("optimizeBtn").addEventListener("click", optimizeRoutes);
});

async function bootstrap() {
    try {
        const res = await fetch("http://127.0.0.1:5000/get-api-key");
        const data = await res.json();
        
        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=${data.apiKey}&libraries=places,visualization&callback=initMap`;
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);
    } catch (e) {
        console.error("Failed to fetch API key or load map", e);
        alert("Failed to connect to backend. Please ensure Flask is running.");
    }
}

window.initMap = function() {
    var dehradun = { lat: 30.3165, lng: 78.0322 };
    
    // Custom dark styling for the map
    const darkMapStyle = [
        { elementType: "geometry", stylers: [{ color: "#242f3e" }] },
        { elementType: "labels.text.stroke", stylers: [{ color: "#242f3e" }] },
        { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] },
        {
            featureType: "administrative.locality",
            elementType: "labels.text.fill",
            stylers: [{ color: "#d59563" }],
        },
        {
            featureType: "road",
            elementType: "geometry",
            stylers: [{ color: "#38414e" }],
        },
        {
            featureType: "road",
            elementType: "geometry.stroke",
            stylers: [{ color: "#212a37" }],
        },
        {
            featureType: "water",
            elementType: "geometry",
            stylers: [{ color: "#17263c" }],
        }
    ];

    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 13,
        center: dehradun,
        styles: darkMapStyle,
        disableDefaultUI: true, // cleaner look
        zoomControl: true,
        restriction: {
            latLngBounds: dehradunBounds,
            strictBounds: true
        }
    });

    // Initialize Heatmap logic
    heatmap = new google.maps.visualization.HeatmapLayer({
        data: [],
        map: null,
        radius: 45,
        maxIntensity: 25,
        opacity: 0.8,
        gradient: [
            "rgba(0, 255, 255, 0)",
            "rgba(0, 255, 255, 0.2)",
            "rgba(0, 191, 255, 0.4)",
            "rgba(0, 127, 255, 0.6)",
            "rgba(0, 63, 255, 0.8)",
            "rgba(0, 0, 255, 1)",
            "rgba(0, 0, 223, 1)",
            "rgba(0, 0, 191, 1)",
            "rgba(0, 0, 159, 1)",
            "rgba(0, 0, 127, 1)",
            "rgba(63, 0, 91, 1)",
            "rgba(127, 0, 63, 1)",
            "rgba(191, 0, 31, 1)",
            "rgba(255, 0, 0, 1)"
        ]
    });

    // Safe to add first box now that library is loaded
    addDeliveryBox();
}

function addDeliveryBox() {
    deliveryCounter++;
    const id = `delivery-${deliveryCounter}`;
    
    const div = document.createElement("div");
    div.className = "delivery-item";
    div.id = id;
    div.innerHTML = `
        <input type="text" id="input-${id}" class="glass-input" placeholder="Enter destination in Dehradun">
        <button class="remove-btn" onclick="removeDeliveryBox('${id}')">&times;</button>
    `;
    
    document.getElementById("deliveryPointsList").appendChild(div);
    
    // Slight delay to ensure element is in DOM before attaching autocomplete
    setTimeout(() => {
        const inputElement = document.getElementById(`input-${id}`);
        if(window.google && window.google.maps) {
            new google.maps.places.Autocomplete(inputElement, {
                bounds: new google.maps.LatLngBounds(
                    new google.maps.LatLng(dehradunBounds.south, dehradunBounds.west),
                    new google.maps.LatLng(dehradunBounds.north, dehradunBounds.east)
                ),
                strictBounds: true,
                componentRestrictions: { country: "IN" },
                fields: ["geometry", "name"]
            });
        }
    }, 100);
}

window.removeDeliveryBox = function(id) {
    document.getElementById(id).remove();
}

function clearAll() {
    document.getElementById("deliveryPointsList").innerHTML = "";
    deliveryCounter = 0;
    addDeliveryBox();
    clearMapRenderings();
}

function clearMapRenderings() {
    markers.forEach(m => m.setMap(null));
    markers = [];
    directionsRenderers.forEach(dr => dr.setMap(null));
    directionsRenderers = [];
}

async function toggleHeatmap() {
    const isChecked = document.getElementById("heatmapToggle").checked;
    
    if (isChecked) {
        document.getElementById("loader").classList.remove("hidden");
        try {
            const res = await fetch("http://127.0.0.1:5000/predict-demand");
            const json = await res.json();
            const points = json.data.map(p => {
                return {
                    location: new google.maps.LatLng(p.lat, p.lng),
                    weight: p.weight * 15 // smooth blend
                }
            });
            heatmap.setData(points);
            heatmap.setMap(map);
        } catch(e) {
            console.error("Heatmap fetch error", e);
        }
        document.getElementById("loader").classList.add("hidden");
    } else {
        heatmap.setMap(null);
    }
}

async function optimizeRoutes() {
    clearMapRenderings();
    document.getElementById("loader").classList.remove("hidden");
    
    const inputs = document.querySelectorAll(".delivery-item input");
    const locations = Array.from(inputs).map(inp => inp.value).filter(val => val.trim().length > 0);
    
    if(locations.length === 0) {
        alert("Please enter at least one delivery destination.");
        document.getElementById("loader").classList.add("hidden");
        return;
    }

    const numAgents = parseInt(document.getElementById("numAgents").value) || 1;
    const useTraffic = document.getElementById("trafficToggle").checked;

    try {
        const res = await fetch("http://127.0.0.1:5000/optimize-route", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ locations, agents: numAgents, use_traffic: useTraffic })
        });
        
        const data = await res.json();
        
        if (data.routes && data.routes.length > 0) {
            drawRoutes(data.routes);
        }
    } catch(e) {
        console.error("Optimization failed", e);
        alert("Optimization request failed.");
    }
    
    document.getElementById("loader").classList.add("hidden");
}

function drawRoutes(routes) {
    const directionsService = new google.maps.DirectionsService();

    routes.forEach((route, index) => {
        if(route.length < 2) return;
        
        let strokeColor = agentColors[index % agentColors.length];
        
        const directionsRenderer = new google.maps.DirectionsRenderer({ 
            map: map,
            polylineOptions: { 
                strokeColor: strokeColor,
                strokeWeight: 5,
                strokeOpacity: 0.8
            },
            suppressMarkers: true
        });
        
        directionsRenderers.push(directionsRenderer);
        
        const waypoints = route.map(loc => ({
            location: new google.maps.LatLng(loc.lat, loc.lng),
            stopover: true
        }));
        
        // Add markers visually
        route.forEach((loc, i) => {
            let label = i === 0 ? "S" : `${i}`; // Start is S
            let marker = new google.maps.Marker({
                position: {lat: loc.lat, lng: loc.lng},
                map: map,
                label: {
                    text: label,
                    color: i === 0 ? "white" : strokeColor,
                    fontWeight: "bold"
                },
                icon: i === 0 ? undefined : {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 10,
                    fillColor: "#161921",
                    fillOpacity: 1,
                    strokeColor: strokeColor,
                    strokeWeight: 3
                },
                title: loc.name || `Stop ${i}`
            });
            markers.push(marker);
        });

        const start = waypoints[0].location;
        const end = waypoints[waypoints.length - 1].location;
        
        const request = {
            origin: start,
            destination: end,
            waypoints: waypoints.slice(1, waypoints.length - 1),
            travelMode: google.maps.TravelMode.DRIVING
        };

        if (document.getElementById("trafficToggle").checked) {
            request.drivingOptions = {
                departureTime: new Date(Date.now() + 1000),  // required for traffic
                trafficModel: 'bestguess'
            };
        }

        directionsService.route(request, (result, status) => {
            if (status === google.maps.DirectionsStatus.OK) {
                directionsRenderer.setDirections(result);
            } else {
                console.warn(`Directions request failed: ${status}`);
            }
        });
    });
}
