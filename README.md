**Route Optimization System** 

A lightweight web-based delivery route optimization system that calculates the shortest and most efficient delivery paths using classical graph algorithms and displays them on an interactive Google Maps interface.

Features

Shortest Path Optimization
Uses Dijkstra’s algorithm to compute the minimum-distance route for single delivery paths.

Multi-Stop Route Planning
Uses Kruskal’s Minimum Spanning Tree (MST) to optimize routes for multiple delivery locations.

Interactive Map Interface
Delivery points are entered through a Google Maps powered UI with autocomplete location search.

Real-Time Visualization
Optimized routes are drawn dynamically on the map after computation.

Predefined Store Nodes
Routes originate from local delivery stores in Dehradun.

Simple Web Architecture
Frontend built with HTML, JavaScript, Google Maps API
Backend powered by Python Flask.

Architecture
System Flow

User enters delivery locations in the web interface.

Frontend sends coordinates to the Flask backend.

Backend runs:

Dijkstra → for shortest path

Kruskal MST → for multi-delivery optimization

Backend returns optimized coordinates.

Frontend renders the final route on Google Maps.
