from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

app = Flask(__name__)
CORS(app) 

# Local store locations (starting points)
store_locations = [
    "Clock Tower, Dehradun",
    "ISBT Dehradun",
    "Rajpur Road, Dehradun",
    "Doon University, Dehradun"
]

def get_distance(origin, destination):
    """Function to get distance between two locations."""
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&key={API_KEY}"
    response = requests.get(url).json()
    
    if response['status'] == 'OK':
        distance_info = response['rows'][0]['elements'][0]
        if distance_info['status'] == 'OK':
            return distance_info['distance']['value']  # in meters
    return float('inf')

def get_coordinates(place):
    """Function to get coordinates of a place."""
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={place}&key={API_KEY}"
    response = requests.get(url).json()
    if response['status'] == 'OK':
        location = response['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    return None, None

def build_adjacency_matrix(locations):
    """Function to build an adjacency matrix with distances."""
    size = len(locations)
    graph = [[0]*size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            if i != j:
                graph[i][j] = get_distance(locations[i], locations[j])
    return graph

def dijkstra(graph, start, end):
    """Dijkstra's algorithm to find shortest path."""
    INF = float('inf')
    n = len(graph)
    dist = [INF]*n
    parent = [-1]*n
    visited = [False]*n

    dist[start] = 0

    for _ in range(n):
        u = min((i for i in range(n) if not visited[i]), key=lambda x: dist[x], default=-1)
        if u == -1: break
        visited[u] = True
        for v in range(n):
            if graph[u][v] and not visited[v] and dist[u] + graph[u][v] < dist[v]:
                dist[v] = dist[u] + graph[u][v]
                parent[v] = u

    path = []
    node = end
    while node != -1:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path

def find(parent, i):
    """Find function for Kruskal's algorithm."""
    if parent[i] != i:
        parent[i] = find(parent, parent[i])
    return parent[i]

def union(parent, rank, u, v):
    """Union function for Kruskal's algorithm."""
    root_u, root_v = find(parent, u), find(parent, v)
    if root_u != root_v:
        if rank[root_u] < rank[root_v]:
            parent[root_u] = root_v
        elif rank[root_u] > rank[root_v]:
            parent[root_v] = root_u
        else:
            parent[root_v] = root_u
            rank[root_u] += 1

def kruskal(graph):
    """Kruskal's algorithm to find minimal spanning tree."""
    n = len(graph)
    edges = []
    for i in range(n):
        for j in range(i+1, n):
            if graph[i][j] != float('inf'):
                edges.append((graph[i][j], i, j))
    edges.sort()
    parent = list(range(n))
    rank = [0]*n
    mst = []
    for weight, u, v in edges:
        if find(parent, u) != find(parent, v):
            union(parent, rank, u, v)
            mst.append((u, v))
    return mst

@app.route("/optimize-route", methods=["POST"])
def optimize_route():
    """Optimize delivery route."""
    data = request.json
    delivery_points = data["locations"]
    
    # Combine store locations with delivery points
    all_locations = store_locations + delivery_points
    
    # Build adjacency matrix for all locations
    graph = build_adjacency_matrix(all_locations)

    # Get coordinates of all locations
    coordinates = []
    for loc in all_locations:
        lat, lng = get_coordinates(loc)
        coordinates.append({"lat": lat, "lng": lng})

    # Find the closest store to the first delivery location
    closest_store_index = None
    closest_distance = float('inf')
    
    # The first delivery location will be the one nearest to a store
    first_delivery_location = delivery_points[0]
    for i, store in enumerate(store_locations):
        distance = get_distance(store, first_delivery_location)
        if distance < closest_distance:
            closest_distance = distance
            closest_store_index = i

    # The path should always start from the closest store and end at the last delivery point
    path = [closest_store_index]  # Start path with the closest store
    visited = [False] * len(all_locations)
    visited[closest_store_index] = True

    # Find the shortest path from the first store to each delivery point using Dijkstra
    for i in range(1, len(delivery_points) + 1):
        # Use Dijkstra to find the closest unvisited delivery point
        current_location_index = path[-1]
        closest_delivery_index = None
        closest_delivery_distance = float('inf')
        
        for j in range(len(store_locations), len(all_locations)):
            if not visited[j]:
                distance = get_distance(all_locations[current_location_index], all_locations[j])
                if distance < closest_delivery_distance:
                    closest_delivery_distance = distance
                    closest_delivery_index = j
        
        visited[closest_delivery_index] = True
        path.append(closest_delivery_index)
    
    # Now return the coordinates for the optimized path
    result = [coordinates[i] for i in path]
    
    return jsonify(result)


@app.route("/get-api-key")
def get_api_key():
    """Endpoint to securely get the API key (optional)."""
    return jsonify({"apiKey": API_KEY})

if __name__ == "__main__":
    app.run(debug=True)
