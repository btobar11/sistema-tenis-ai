from scrapers.db_client import get_db_client

def check_count():
    db = get_db_client()
    try:
        # Matches count
        m = db.from_('matches').select('id').execute()
        m_count = len(m.data) if m.data else 0
        print(f"Matches Count: {m_count}")

        # Stats count
        r = db.from_('match_stats').select('id').execute()
        r_count = len(r.data) if r.data else 0
        print(f"Match Stats Count: {r_count}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_count()
