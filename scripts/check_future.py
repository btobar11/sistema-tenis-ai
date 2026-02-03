
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scrapers.db_client import get_db_client
from datetime import datetime

def check_future_matches():
    db = get_db_client()
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"Checking for matches after: {today}")
    
    # Check matches with predictions
    r = db.table('matches').select('id,date,tournament_name,prediction').gte('date', today).limit(10).execute()
    
    if r.data:
        print(f"Found {len(r.data)} upcoming/today matches:")
        for m in r.data:
            has_pred = "YES" if m.get('prediction') else "NO"
            print(f" - {m['date']}: {m['tournament_name']} (AI Prediction: {has_pred})")
    else:
        print("No matches found for today or future.")

if __name__ == "__main__":
    check_future_matches()
