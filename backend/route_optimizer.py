import requests
import os
from sklearn.cluster import KMeans

# Cache to avoid too many API calls during processing
coord_cache = {}

store_locations = [
    "Clock Tower, Dehradun",
    "ISBT Dehradun",
    "Rajpur Road, Dehradun",
    "Doon University, Dehradun"
]

def get_distance(origin, destination, use_traffic=False):
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if "GOOGLE_MAPS_API_KEY" in os.environ:
        del os.environ["GOOGLE_MAPS_API_KEY"]
    load_dotenv(dotenv_path=env_path, override=True)
    
    API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&key={API_KEY}"
    if use_traffic:
        url += "&departure_time=now"
    
    response = requests.get(url).json()
    if response['status'] == 'OK':
        distance_info = response['rows'][0]['elements'][0]
        if distance_info['status'] == 'OK':
            # Use duration in traffic to weigh the best route if use_traffic is active
            if use_traffic and 'duration_in_traffic' in distance_info:
                return distance_info['duration_in_traffic']['value']
            return distance_info['distance']['value']
    return float('inf')

def get_coordinates(place):
    if place in coord_cache:
        return coord_cache[place]
        
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if "GOOGLE_MAPS_API_KEY" in os.environ:
        del os.environ["GOOGLE_MAPS_API_KEY"]
    load_dotenv(dotenv_path=env_path, override=True)
    
    API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={place}&key={API_KEY}"
    response = requests.get(url).json()
    if response['status'] == 'OK':
        location = response['results'][0]['geometry']['location']
        coord_cache[place] = (location['lat'], location['lng'])
        return location['lat'], location['lng']
    return None, None

def partition_deliveries(delivery_points, labels):
    clusters = {}
    for i, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(delivery_points[i])
    return list(clusters.values())

def optimize_single_route(delivery_points, use_traffic=False):
    if not delivery_points:
        return []
        
    all_locations = store_locations + delivery_points
    
    coordinates = []
    coord_strings = []
    
    for loc in all_locations:
        lat, lng = get_coordinates(loc)
        coordinates.append({"lat": lat, "lng": lng, "name": loc})
        coord_strings.append(f"{lat},{lng}")
        
    closest_store_index = None
    closest_distance = float('inf')

    # Get the nearest store to the first delivery point
    first_delivery = coord_strings[len(store_locations)]
    
    for i in range(len(store_locations)):
        dist = get_distance(coord_strings[i], first_delivery, use_traffic)
        if dist < closest_distance:
            closest_distance = dist
            closest_store_index = i

    path = [closest_store_index]
    visited = [False] * len(all_locations)
    visited[closest_store_index] = True

    # Greedy approach finding best next node based on distance/traffic metric
    for _ in range(len(delivery_points)):
        current_idx = path[-1]
        closest_delivery_index = None
        closest_delivery_dist = float('inf')
        
        for j in range(len(store_locations), len(all_locations)):
            if not visited[j]:
                d = get_distance(coord_strings[current_idx], coord_strings[j], use_traffic)
                if d < closest_delivery_dist:
                    closest_delivery_dist = d
                    closest_delivery_index = j
                    
        visited[closest_delivery_index] = True
        path.append(closest_delivery_index)
        
    return [coordinates[i] for i in path]


def optimize_multi_agent(delivery_points, num_agents, use_traffic=False):
    if len(delivery_points) == 0:
        return []
        
    if len(delivery_points) <= num_agents:
        num_agents = len(delivery_points)

    if num_agents == 1:
        return [optimize_single_route(delivery_points, use_traffic)]

    # Get coordinates for clustering
    delivery_coords = []
    for dp in delivery_points:
        lat, lng = get_coordinates(dp)
        delivery_coords.append([lat, lng])
        
    # Cluster deliveries among agents into distinct regions
    kmeans = KMeans(n_clusters=num_agents, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(delivery_coords)
    
    agent_partitions = partition_deliveries(delivery_points, labels)
    
    routes = []
    for partition in agent_partitions:
        routes.append(optimize_single_route(partition, use_traffic))
        
    return routes
