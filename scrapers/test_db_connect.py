from db_client import get_db_client

try:
    print("Initializing client...")
    db = get_db_client()
    print("Client initialized.")
    if db:
        print("Testing get_or_create_player...")
        pid = db.get_or_create_player("Nakashima B.")
        print(f"Player ID: {pid}")
    else:
        print("DB Client is None")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error: {e}")
