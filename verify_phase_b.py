import sys
import os
sys.path.append(os.getcwd())

from ai_engine.ml_engine import XGBoostEngine
from ai_engine.simulator import Simulator

def verify_integration():
    print("=== Phase B: Integration Verification ===\n")
    
    # 1. Load Engine
    print("1. Initializing XGBoostEngine...")
    engine = XGBoostEngine()
    
    if not engine.is_ready():
        print("[FAIL] Model not loaded.")
        return
    print("[PASS] Model loaded.")
    
    # 2. Test Prediction Cases
    cases = [
        # (Name, Surface, R1, R2)
        ("Nadal (Clay)", "CLAY", 5, 50),
        ("Djokovic (Hard)", "HARD", 1, 10),
        ("Isner (Hard - Servebot)", "HARD", 50, 50), # Simulate high serve
        ("Balanced Match", "HARD", 20, 20)
    ]
    
    sim = Simulator(num_simulations=500)
    
    for name, surf, r1, r2 in cases:
        print(f"\n--- Case: {name} ---")
        match_data = {
            'surface': surf,
            'rank_p1': r1,
            'rank_p2': r2,
            # Elo still optional in this version
            'elo_p1': 1500, 
            'elo_p2': 1500 
        }
        
        # Predict P(Serve)
        try:
            p1, p2 = engine.predict_params(match_data)
        except Exception as e:
            print(f"[FAIL] Prediction Error: {e}")
            continue
            
        print(f"Pred: P1={p1:.3f}, P2={p2:.3f}")
        
        # Check constraints
        if not (0.52 <= p1 <= 0.75): print(f"[WARN] P1 Out of bounds: {p1}")
        if not (0.52 <= p2 <= 0.75): print(f"[WARN] P2 Out of bounds: {p2}")
        
        # Run Simulation
        print("  Running Simulation...")
        stats = sim.simulate_match(p1, p2)
        
        print(f"  Win% P1: {stats['p_win']:.1%}")
        print(f"  Sets Dist: {stats['sets']}")
        print(f"  Total Games: {stats['total_games']}")
        
        # Basic sanity checks on simulation based on P_serve
        if p1 > p2 + 0.05:
            if stats['p_win'] < 0.60:
                print("  [WARN] Favored player P1 has low win probability?")
        
if __name__ == "__main__":
    verify_integration()
