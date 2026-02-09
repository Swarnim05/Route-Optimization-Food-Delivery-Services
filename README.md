**ERoute**: **Route Optimization System :** 

A lightweight web-based delivery route optimization system that calculates the shortest and most efficient delivery paths using classical graph algorithms and displays them on an interactive Google Maps interface.

->**Features:**

1) Shortest Path Optimization:
 Uses Dijkstra’s algorithm to compute the minimum-distance route for single delivery paths.

2) Multi-Stop Route Planning:
 Uses Kruskal’s Minimum Spanning Tree (MST) to optimize routes for multiple delivery locations.

3) Interactive Map Interface:
 Delivery points are entered through a Google Maps powered UI with autocomplete location search.

4) Real-Time Visualization:
 Optimized routes are drawn dynamically on the map after computation.

5) Predefined Store Nodes: 
 Routes originate from local delivery stores in Dehradun.

6) Simple Web Architecture:
 Frontend built with HTML, JavaScript, Google Maps API
Backend powered by Python Flask.

**Architecture:**

1) User enters delivery locations in the web interface.

2) Frontend sends coordinates to the Flask backend.

3) Backend runs:

      3.1) Dijkstra → for shortest path
   
      3.2) Kruskal MST → for multi-delivery optimization
   
      3.3) Backend returns optimized coordinates.
   
      3.4) Frontend renders the final route on Google Maps.
