from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from pathlib import Path
from route_optimizer import optimize_multi_agent
from ml_model import predictor
from datetime import datetime

# Load env variables
env_path = Path(__file__).resolve().parent.parent / '.env'
if "GOOGLE_MAPS_API_KEY" in os.environ:
    del os.environ["GOOGLE_MAPS_API_KEY"]
load_dotenv(dotenv_path=env_path, override=True)

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

app = Flask(__name__)
CORS(app) 

@app.route("/optimize-route", methods=["POST"])
def api_optimize_route():
    data = request.json
    delivery_points = data.get("locations", [])
    num_agents = int(data.get("agents", 1))
    use_traffic = data.get("use_traffic", False)
    
    if not delivery_points:
        return jsonify({"routes": []})

    routes = optimize_multi_agent(delivery_points, num_agents, use_traffic)
    return jsonify({"routes": routes})

@app.route("/predict-demand", methods=["GET"])
def api_predict_demand():
    # Heatmap based on either given args or current time
    hour = request.args.get('hour', default=datetime.now().hour, type=int)
    day = request.args.get('day', default=datetime.now().weekday(), type=int)
    
    heatmap_data = predictor.predict_heat(hour, day)
    return jsonify({"data": heatmap_data})

@app.route("/get-api-key")
def get_api_key():
    return jsonify({"apiKey": API_KEY})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
