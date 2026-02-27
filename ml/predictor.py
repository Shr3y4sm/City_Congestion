"""
CityFlow AI - ML Congestion Predictor
Predicts traffic congestion levels 30 minutes into the future using XGBoost.
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from typing import Dict


class CongestionPredictor:
    """
    Machine learning model to predict future traffic congestion levels.
    """
    
    def __init__(self):
        """Initialize and train the XGBoost model with synthetic data."""
        self.model = None
        self.labels = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
        self._train_model()
    
    def _generate_synthetic_data(self, n_samples: int = 1000) -> tuple:
        """
        Generate synthetic training data for congestion prediction.
        
        Args:
            n_samples: Number of training samples to generate
            
        Returns:
            Tuple of (features_df, labels_array)
        """
        np.random.seed(42)
        
        # Generate random features
        hours = np.random.randint(0, 24, n_samples)
        weekdays = np.random.randint(0, 7, n_samples)
        current_congestion = np.random.uniform(0.8, 2.0, n_samples)
        distances = np.random.uniform(1, 20, n_samples)
        
        # Peak hour flag (8-10 AM or 5-8 PM)
        peak_flags = np.array([
            1 if (8 <= h < 10) or (17 <= h < 20) else 0 
            for h in hours
        ])
        
        # Calculate future congestion (30 min ahead)
        future_congestion = current_congestion.copy()
        
        for i in range(n_samples):
            # Increase congestion during peak hours
            if peak_flags[i] == 1:
                future_congestion[i] += np.random.uniform(0.1, 0.3)
            
            # Increase if already congested
            if current_congestion[i] > 1.3:
                future_congestion[i] += np.random.uniform(0.05, 0.15)
            
            # Weekend effect (less congestion)
            if weekdays[i] >= 5:
                future_congestion[i] -= np.random.uniform(0.1, 0.2)
            
            # Add random noise
            future_congestion[i] += np.random.uniform(-0.05, 0.05)
            
            # Ensure within bounds
            future_congestion[i] = max(0.5, min(2.5, future_congestion[i]))
        
        # Assign labels based on thresholds
        labels = np.zeros(n_samples, dtype=int)
        labels[future_congestion >= 1.2] = 1  # MEDIUM
        labels[future_congestion >= 1.5] = 2  # HIGH
        
        # Create feature dataframe
        features = pd.DataFrame({
            'hour': hours,
            'weekday': weekdays,
            'current_congestion_index': current_congestion,
            'distance_km': distances,
            'peak_hour_flag': peak_flags
        })
        
        return features, labels
    
    def _train_model(self):
        """Train the XGBoost classifier on synthetic data."""
        # Generate training data
        X_train, y_train = self._generate_synthetic_data(1000)
        
        # Train XGBoost classifier
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            eval_metric='mlogloss'
        )
        
        self.model.fit(X_train, y_train)
    
    def predict(self, hour: int, weekday: int, current_index: float, 
                distance_km: float) -> Dict:
        """
        Predict future congestion level based on current conditions.
        
        Args:
            hour: Current hour (0-23)
            weekday: Day of week (0=Monday, 6=Sunday)
            current_index: Current congestion index
            distance_km: Distance in kilometers
            
        Returns:
            Dictionary with prediction and confidence:
            {
                "future_congestion_level": str (LOW/MEDIUM/HIGH),
                "confidence": float
            }
        """
        # Calculate peak hour flag
        peak_hour_flag = 1 if (8 <= hour < 10) or (17 <= hour < 20) else 0
        
        # Create feature array
        features = pd.DataFrame({
            'hour': [hour],
            'weekday': [weekday],
            'current_congestion_index': [current_index],
            'distance_km': [distance_km],
            'peak_hour_flag': [peak_hour_flag]
        })
        
        # Get prediction and probabilities
        prediction = self.model.predict(features)[0]
        probabilities = self.model.predict_proba(features)[0]
        
        # Get confidence (probability of predicted class)
        confidence = round(float(probabilities[prediction]), 2)
        
        return {
            "future_congestion_level": self.labels[prediction],
            "confidence": confidence
        }


if __name__ == "__main__":
    """Test the CongestionPredictor with various scenarios."""
    
    print("🤖 CityFlow AI - ML Congestion Predictor\n")
    print("Training XGBoost model on synthetic data...")
    
    predictor = CongestionPredictor()
    print("✓ Model trained successfully\n")
    print("="*60)
    
    # Test scenarios
    scenarios = [
        {
            "name": "Morning Peak - High Current Congestion",
            "hour": 9,
            "weekday": 2,  # Wednesday
            "current_index": 1.6,
            "distance_km": 8.5
        },
        {
            "name": "Off-Peak - Low Current Congestion",
            "hour": 14,
            "weekday": 3,  # Thursday
            "current_index": 0.9,
            "distance_km": 5.2
        },
        {
            "name": "Evening Peak - Medium Congestion",
            "hour": 18,
            "weekday": 4,  # Friday
            "current_index": 1.3,
            "distance_km": 10.0
        },
        {
            "name": "Weekend - Low Congestion",
            "hour": 11,
            "weekday": 6,  # Sunday
            "current_index": 1.0,
            "distance_km": 7.0
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📊 Scenario: {scenario['name']}")
        print(f"   Time: Hour {scenario['hour']}, Weekday {scenario['weekday']}")
        print(f"   Current Congestion: {scenario['current_index']}")
        print(f"   Distance: {scenario['distance_km']} km")
        
        result = predictor.predict(
            scenario['hour'],
            scenario['weekday'],
            scenario['current_index'],
            scenario['distance_km']
        )
        
        print(f"\n   🔮 Prediction (30 min ahead):")
        print(f"      Congestion Level: {result['future_congestion_level']}")
        print(f"      Confidence: {result['confidence']*100:.0f}%")
        print("   " + "-"*56)
    
    print("\n" + "="*60)
    print("\n✅ Prediction engine ready for deployment!")
