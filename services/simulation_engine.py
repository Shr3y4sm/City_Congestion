"""
CityFlow AI - Simulation Engine
"What-if" scenario analysis for traffic interventions and urban planning decisions.
"""

from datetime import datetime
from typing import Dict
from copy import deepcopy


class SimulationEngine:
    """
    Simulation engine for analyzing traffic interventions and their impact
    on congestion metrics before real-world deployment.
    """
    
    # Speed constants (km/h) - must match CongestionEngine
    BASE_SPEED = 35
    PEAK_HOUR_SPEED = 25
    WEEKEND_SPEED = 40
    
    # Peak hour ranges
    MORNING_PEAK = (8, 10)
    EVENING_PEAK = (17, 20)
    
    # Scenario adjustment factors
    WIDEN_ROAD_FACTOR = 1.15  # 15% speed increase
    OPTIMIZE_SIGNALS_FACTOR = 0.90  # 10% duration reduction
    REPAIR_FACTOR = 0.80  # 20% speed reduction
    HEAVY_VEHICLE_RESTRICTION_FACTOR = 1.08  # 8% speed increase (peak only)
    
    # Congestion thresholds
    LOW_THRESHOLD = 1.2
    MEDIUM_THRESHOLD = 1.5
    
    def get_base_speed(self, hour: int = None) -> float:
        """
        Get base speed based on current time conditions.
        
        Args:
            hour: Optional hour override (0-23). If None, uses current time.
            
        Returns:
            Base speed in km/h
        """
        if hour is None:
            now = datetime.now()
            hour = now.hour
            is_weekend = now.weekday() >= 5
        else:
            is_weekend = datetime.now().weekday() >= 5
        
        if is_weekend:
            return self.WEEKEND_SPEED
        elif (self.MORNING_PEAK[0] <= hour < self.MORNING_PEAK[1] or 
              self.EVENING_PEAK[0] <= hour < self.EVENING_PEAK[1]):
            return self.PEAK_HOUR_SPEED
        else:
            return self.BASE_SPEED
    
    def assign_congestion_level(self, congestion_index: float) -> str:
        """
        Assign congestion level based on congestion index.
        
        Args:
            congestion_index: Congestion index value
            
        Returns:
            Congestion level: "LOW", "MEDIUM", or "HIGH"
        """
        if congestion_index < self.LOW_THRESHOLD:
            return "LOW"
        elif congestion_index < self.MEDIUM_THRESHOLD:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def calculate_risk_score(self, congestion_index: float) -> float:
        """
        Calculate risk score from congestion index.
        
        Args:
            congestion_index: Congestion index value
            
        Returns:
            Risk score clamped between 0 and 10
        """
        forecast_weight = 2 if congestion_index >= self.MEDIUM_THRESHOLD else 1
        risk_score = (congestion_index * 4) + forecast_weight
        risk_score = max(0, min(10, risk_score))  # Clamp 0-10
        return round(risk_score, 2)
    
    def recalculate_metrics(self, distance_km: float, actual_duration_min: float, 
                           adjusted_speed: float) -> Dict:
        """
        Recalculate congestion metrics based on adjusted speed.
        
        Args:
            distance_km: Distance in kilometers
            actual_duration_min: Actual travel time in minutes
            adjusted_speed: Speed after scenario adjustments (km/h)
            
        Returns:
            Dictionary with recalculated metrics
        """
        # Calculate new expected duration
        expected_duration_min = (distance_km / adjusted_speed) * 60
        expected_duration_min = round(expected_duration_min, 2)
        
        # Calculate new congestion index
        if expected_duration_min == 0:
            congestion_index = 1.0
        else:
            congestion_index = actual_duration_min / expected_duration_min
        congestion_index = round(congestion_index, 2)
        
        # Assign level and calculate risk score
        congestion_level = self.assign_congestion_level(congestion_index)
        risk_score = self.calculate_risk_score(congestion_index)
        
        return {
            "expected_duration_min": expected_duration_min,
            "congestion_index": congestion_index,
            "congestion_level": congestion_level,
            "risk_score": risk_score
        }
    
    def simulate(self, zone_data: Dict, scenario: str, hour: int = None) -> Dict:
        """
        Simulate a traffic intervention scenario and compare before/after metrics.
        
        Args:
            zone_data: Zone data dictionary with current metrics
            scenario: Scenario name (none, widen_road, optimize_signals, 
                     road_under_repair, heavy_vehicle_restriction)
            hour: Optional hour for peak hour calculation (0-23)
            
        Returns:
            Structured comparison with improvement metrics
        """
        # Validate scenario
        valid_scenarios = ["none", "widen_road", "optimize_signals", 
                          "road_under_repair", "heavy_vehicle_restriction"]
        if scenario not in valid_scenarios:
            raise ValueError(f"Invalid scenario: {scenario}. Valid: {valid_scenarios}")
        
        # Deep copy to avoid mutation
        data = deepcopy(zone_data)
        
        # Extract before metrics
        before_ci = data["congestion_index"]
        before_level = data["congestion_level"]
        before_risk = data["risk_score"]
        
        # Get base speed for calculations
        base_speed = self.get_base_speed(hour)
        distance_km = data["distance_km"]
        actual_duration_min = data["actual_duration_min"]
        
        # Apply scenario adjustments
        if scenario == "none":
            adjusted_speed = base_speed
            adjusted_duration = data["actual_duration_min"]
        
        elif scenario == "widen_road":
            adjusted_speed = base_speed * self.WIDEN_ROAD_FACTOR
            adjusted_duration = actual_duration_min
        
        elif scenario == "optimize_signals":
            adjusted_speed = base_speed
            adjusted_duration = actual_duration_min * self.OPTIMIZE_SIGNALS_FACTOR
        
        elif scenario == "road_under_repair":
            adjusted_speed = base_speed * self.REPAIR_FACTOR
            adjusted_duration = actual_duration_min
        
        elif scenario == "heavy_vehicle_restriction":
            # Only applies during peak hours
            is_peak = hour and ((self.MORNING_PEAK[0] <= hour < self.MORNING_PEAK[1] or 
                               self.EVENING_PEAK[0] <= hour < self.EVENING_PEAK[1]))
            if is_peak or (hour is None and (self.MORNING_PEAK[0] <= datetime.now().hour < self.MORNING_PEAK[1] or 
                                            self.EVENING_PEAK[0] <= datetime.now().hour < self.EVENING_PEAK[1])):
                adjusted_speed = base_speed * self.HEAVY_VEHICLE_RESTRICTION_FACTOR
            else:
                adjusted_speed = base_speed
            adjusted_duration = actual_duration_min
        
        # Recalculate metrics
        after_metrics = self.recalculate_metrics(distance_km, adjusted_duration, adjusted_speed)
        
        after_ci = after_metrics["congestion_index"]
        after_level = after_metrics["congestion_level"]
        after_risk = after_metrics["risk_score"]
        
        # Calculate improvement percentage
        if before_ci == 0:
            improvement_percent = 0.0
        else:
            improvement_percent = round(((before_ci - after_ci) / before_ci) * 100, 2)
        
        return {
            "zone_name": data.get("zone_name", "Unknown"),
            "scenario": scenario,
            "before": {
                "ci": before_ci,
                "level": before_level,
                "risk_score": before_risk
            },
            "after": {
                "ci": after_ci,
                "level": after_level,
                "risk_score": after_risk
            },
            "improvement_percent": improvement_percent
        }


def _format_result(result: Dict) -> None:
    """Pretty print simulation result."""
    print(f"\nZone: {result['zone_name']} | Scenario: {result['scenario'].upper()}")
    print("-" * 70)
    print(f"{'Metric':<30} {'Before':<15} {'After':<15} {'Change':<10}")
    print("-" * 70)
    
    before_ci = result["before"]["ci"]
    after_ci = result["after"]["ci"]
    ci_change = after_ci - before_ci
    
    before_risk = result["before"]["risk_score"]
    after_risk = result["after"]["risk_score"]
    risk_change = after_risk - before_risk
    
    print(f"{'Congestion Index':<30} {before_ci:<15.2f} {after_ci:<15.2f} {ci_change:+.2f}")
    print(f"{'Congestion Level':<30} {result['before']['level']:<15} {result['after']['level']:<15}")
    print(f"{'Risk Score':<30} {before_risk:<15.2f} {after_risk:<15.2f} {risk_change:+.2f}")
    print("-" * 70)
    print(f"Overall Improvement: {result['improvement_percent']:+.2f}%")
    
    if result["improvement_percent"] > 0:
        print("Positive impact detected")
    elif result["improvement_percent"] < 0:
        print("Negative impact detected")
    else:
        print("No impact")


if __name__ == "__main__":
    """Test the SimulationEngine with mock zone data."""
    
    print("\n" + "="*70)
    print("CityFlow AI - Simulation Engine")
    print("Traffic Intervention Impact Analysis")
    print("="*70)
    
    # Mock zone data
    zone_mg_road = {
        "zone_name": "MG Road",
        "distance_km": 5.0,
        "actual_duration_min": 12.0,
        "expected_duration_min": 8.5,
        "congestion_index": 1.41,
        "congestion_level": "MEDIUM",
        "risk_score": 6.2
    }
    
    engine = SimulationEngine()
    
    # Test scenarios
    scenarios = ["widen_road", "optimize_signals", "road_under_repair"]
    
    for scenario in scenarios:
        result = engine.simulate(zone_mg_road, scenario, hour=9)
        _format_result(result)
    
    print("\n" + "="*70)
    print("✅ Simulation engine ready for deployment!")
    print("="*70 + "\n")
