import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

class DemandPredictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.train_synthetic_model()

    def train_synthetic_model(self):
        # Generate fake data inside Dehradun bounding box
        # Lat: 30.25 to 30.40, Lng: 77.95 to 78.10
        np.random.seed(42)
        samples = 2000
        lats = np.random.uniform(30.25, 30.40, samples)
        lngs = np.random.uniform(77.95, 78.10, samples)
        hours = np.random.randint(0, 24, samples)
        days = np.random.randint(0, 7, samples)
        
        # Artificial hotspots logic
        # Center: ~30.3165, 78.0322
        demand = []
        for i in range(samples):
            dist_to_center = np.sqrt((lats[i] - 30.3165)**2 + (lngs[i] - 78.0322)**2)
            intensity = 10
            
            # Evening dinner spike in city center
            if 18 <= hours[i] <= 22:
                if dist_to_center < 0.04:
                    intensity += 60
            
            # Lunch spike
            if 12 <= hours[i] <= 15:
                if dist_to_center < 0.06:
                    intensity += 40

            # Morning spike near outer edges
            if 8 <= hours[i] <= 10:
                if dist_to_center > 0.05:
                    intensity += 30

            # Weekend generalized increase
            if days[i] in [5, 6]:
                intensity *= 1.3

            intensity += np.random.normal(0, 5) # add some noise
            demand.append(max(0, intensity))
            
        X = pd.DataFrame({'lat': lats, 'lng': lngs, 'hour': hours, 'day': days})
        y = np.array(demand)
        self.model.fit(X, y)

    def predict_heat(self, hour, day):
        # Predict on a tighter grid for smooth heatmap
        grid_lats = np.linspace(30.25, 30.40, 30)
        grid_lngs = np.linspace(77.95, 78.10, 30)
        
        test_data = []
        for lat in grid_lats:
            for lng in grid_lngs:
                test_data.append([lat, lng, hour, day])
                
        df = pd.DataFrame(test_data, columns=['lat', 'lng', 'hour', 'day'])
        preds = self.model.predict(df)
        
        median_p = np.median(preds)
        max_p = max(preds)
        range_p = max(max_p - median_p, 20.0) # Prevent noise amplification
        
        results = []
        for i, val in enumerate(preds):
            if val > median_p:
                weight = (val - median_p) / range_p
                if weight > 0.1: 
                    results.append({
                        "lat": float(test_data[i][0]),
                        "lng": float(test_data[i][1]),
                        "weight": float(weight)
                    })
        return results

# Singleton instance
predictor = DemandPredictor()
