import sys
import os
from pprint import pprint

# Add root to sys.path
sys.path.append(os.getcwd())

from api.services.inference_service import InferenceService

def test_inference():
    print("Initializing Inference Service...")
    service = InferenceService()
    
    # Needs real player IDs. Let's fetch 2 from DB.
    try:
        from scrapers.db_client import get_db_client
        db = get_db_client()
        r = db.from_('players').select('id,name').limit(2).execute()
        if not r.data or len(r.data) < 2:
            print("Not enough players in DB to test.")
            return # Use dummies?
            
        p1 = r.data[0]
        p2 = r.data[1]
        
        print(f"Testing Prediction: {p1['name']} vs {p2['name']}")
        
        result = service.predict_matchup(p1['id'], p2['id'])
        
        print("\n--- Result ---")
        pprint(result)
        
        print("\n--- Validation ---")
        assert "winner_id" in result
        assert "markets" in result
        assert "simulated_p_win" in result["metrics"]
        print("✅ Structure Valid")
        
        probs = result['markets']['sets']
        total_prob = sum(probs.values())
        print(f"Set Probs Sum: {total_prob} (Should be ~1.0)")
        assert abs(total_prob - 1.0) < 0.05
        print("✅ Probabilities Valid")

    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_inference()
