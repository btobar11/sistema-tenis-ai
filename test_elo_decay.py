from metrics.elo import EloEngine
from datetime import datetime, timedelta

def test_elo_logic():
    engine = EloEngine()
    
    print("--- Test 1: Dynamic K-Factor ---")
    # Low matches -> High K
    # High matches -> Low K
    # Assuming simulate matches count
    
    # New Player (K=40) vs Vet (K=24)
    # Both 1500 rating
    # New Player wins
    new_r1, new_r2 = engine.calculate_new_ratings(1500, 1500, 1, matches_a=5, matches_b=150)
    print(f"New Player Wins: {1500} -> {new_r1} (Should be +20 if K=40 * 0.5)")
    print(f"Vet Loses: {1500} -> {new_r2} (Should be -12 if K=24 * 0.5)")
    
    assert new_r1 == 1520
    assert new_r2 == 1488
    print("✅ K-Factor Logic PASS")

    print("\n--- Test 2: Inactivity Decay ---")
    # 1600 rating, inactive 3 months
    last_update = (datetime.now() - timedelta(days=100)).isoformat()
    decayed = engine.apply_decay("P1", 1600, last_update, "HARD")
    
    # 3 months * 2% = 6% decay towards 1500
    # Diff = 100
    # Decay = 6
    # New = 1594
    print(f"1600 Inactive 100 days -> {decayed}")
    # Calculation: 100 // 30 = 3 months. Factor 0.06. 
    # 1600 + (1500-1600)*0.06 = 1600 - 6 = 1594.
    
    assert decayed == 1594
    print("✅ Decay Logic PASS")

if __name__ == "__main__":
    test_elo_logic()
