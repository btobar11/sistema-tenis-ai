
import sys
import os

# Add root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.services.inference_service import InferenceService
from scrapers.db_client import get_db_client, get_or_create_player

def test_inference():
    print("--- Starting Inference Test ---")
    db = get_db_client()
    
    # 1. Ensure Setup Players
    p1_name = "Novak Djokovic"
    p2_name = "Rafael Nadal"
    
    print(f"Resolving players: {p1_name}, {p2_name}...")
    p1_id = get_or_create_player(db, p1_name)
    p2_id = get_or_create_player(db, p2_name)
    
    print(f" IDs: {p1_id} vs {p2_id}")
    
    if not p1_id or not p2_id:
        print("Failed to resolve players. Check DB connection.")
        return

    # 2. Init Service
    service = InferenceService()
    
    # 3. Predict
    print("\nRunning Prediction...")
    result = service.predict_matchup(p1_id, p2_id)
    
    print("\n--- Prediction Result ---")
    print(f"Winner: {result.get('winner_id')} (Conf: {result.get('confidence')})")
    print("Reasoning:", result.get('reasoning'))
    print("Metrics:", result.get('metrics'))
    print("-------------------------\n")

if __name__ == "__main__":
    test_inference()
