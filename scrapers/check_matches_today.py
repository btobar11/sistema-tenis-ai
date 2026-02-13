from db_client import get_db_client
from datetime import datetime, timedelta

def check_today():
    db = get_db_client()
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"Checking matches for: {today}")
    
    # Query for today's matches
    # Note: timestamps in DB are typically ISO 8601 with time
    day_start = f"{today}T00:00:00"
    day_end = f"{today}T23:59:59"
    
    try:
        res = db.table("matches").select("*").gte("date", day_start).lte("date", day_end).execute()
        matches = res.data
        print(f"Found {len(matches)} matches in DB.")
        for m in matches[:5]:
            print(f" - {m['winner_name']} vs {m['loser_name']} ({m['score_full']}) [Status: {m['status']}]")
            
    except Exception as e:
        print(f"Error querying DB: {e}")

if __name__ == "__main__":
    check_today()
