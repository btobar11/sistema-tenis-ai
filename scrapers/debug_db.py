from scrapers.db_client import get_db_client

def test():
    print("Initializing DB...")
    db = get_db_client()
    if not db:
        print("Failed to init DB.")
        return

    print("Querying table...")
    try:
        # Simple count or limited select
        r = db.table('players').select('id').limit(1).execute()
        print(f"Success! Data: {r.data}")
    except Exception as e:
        print(f"Query Failed: {e}")

if __name__ == "__main__":
    test()
