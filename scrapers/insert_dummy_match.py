from db_client import get_db_client, get_or_create_player
from datetime import datetime

def insert_dummy():
    db = get_db_client()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Create dummy players
    p1_id = get_or_create_player(db, "Test Player A")
    p2_id = get_or_create_player(db, "Test Player B")
    
    dummy_match = {
        "date": f"{today_str}T12:00:00",
        "tournament_name": "Test Tournament 2026",
        "surface": "hard",
        "player1_id": p1_id,
        "player2_id": p2_id,
        "status": "scheduled",
        "round": "Final"
    }
    
    # Use raw insert to bypass logic
    res = db.from_('matches').insert(dummy_match).execute()
    if res.error:
        print(f"Error inserting: {res.error}")
    else:
        print(f"Inserted dummy match for {today_str} successfully.")

if __name__ == "__main__":
    insert_dummy()
