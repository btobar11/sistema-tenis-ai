from scrapers.match_scraper import scrape_today_results
from scrapers.db_client import get_db_client

def test_ingestion():
    print("Running DB Ingestion Test...")
    
    # 1. Scrape matches
    print("Scraping matches...")
    matches = scrape_today_results()
    print(f"Scraped {len(matches)} matches.")
    
    if not matches:
        print("No matches to ingest.")
        return

    # 2. Connect to DB
    print("Connecting to DB...")
    db = get_db_client()
    if not db:
        print("Could not connect to DB. Check .env")
        return

    # 3. Ingest first 5 matches
    print("Ingesting first 5 matches...")
    count = 0
    for m in matches[:5]:
        # Get IDs
        p1_id = db.get_or_create_player(m['winner']) # Winner is usually p1 or p2 logic mapped
        # Wait, scrape_today_results returns 'winner' name and 'loser' name directly.
        
        # Let's check keys
        # keys: winner, loser, score, date, tournament...
        
        w_name = m['winner']
        l_name = m['loser']
        
        w_id = db.get_or_create_player(w_name)
        l_id = db.get_or_create_player(l_name)
        
        if not w_id or not l_id:
            print(f"Failed to resolve IDs for {w_name} vs {l_name}")
            continue
            
        # Map to DB schema
        # We need to decide who is p1 vs p2 in DB TABLE. 
        # Usually alphabetical or arbitrary. 
        # match_scraper returns 'winner' and 'loser' names.
        
        db_match = {
            "date": m['date'],
            "tournament_name": m['tournament'],
            "player1_id": w_id, # Let's just put winner as p1 for now
            "player2_id": l_id,
            "winner_id": w_id,
            "score_full": m['score'],
            "stats_json": {} # No detailed stats for this test
        }
        
        if db.insert_match(db_match):
            print(f"  [SAVED] {w_name} d. {l_name}")
            count += 1
        else:
            print(f"  [SKIP/FAIL] {w_name} d. {l_name}")
            
    print(f"Test finished. Ingested {count} matches.")

if __name__ == "__main__":
    test_ingestion()
