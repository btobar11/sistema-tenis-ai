import time
import random
import requests
from datetime import datetime, timedelta
from bulk_history_scraper import scrape_today_results, get_or_create_player, SUPABASE_URL, HEADERS

def slow_scrape(days_back=365):
    """
    Scrapes 1 year of data very slowly to avoid detection.
    Speed: ~1 day of matches every 10-20 seconds.
    Est. Time for 1 year: ~1.5 hours.
    """
    print(f"[{datetime.now()}] Starting STEALTH SCRAPE for last {days_back} days...")
    
    total_saved = 0
    start_date = datetime.now()
    
    for i in range(days_back):
        target_date = start_date - timedelta(days=i)
        date_str = target_date.strftime('%Y-%m-%d')
        
        print(f"[{i+1}/{days_back}] Processing {date_str}...", end=" ", flush=True)
        
        try:
            # 1. Scrape
            matches = scrape_today_results(target_date)
            
            if not matches:
                print("No matches.")
            else:
                # 2. Process & Save
                saved_count = 0
                for m in matches:
                    p1_name = m['winner'].strip()
                    p2_name = m['loser'].strip()
                    
                    # Resolve Players (with cache from bulk_scraper)
                    p1_id = get_or_create_player(p1_name)
                    p2_id = get_or_create_player(p2_name)
                    
                    if not p1_id or not p2_id: continue
                    
                    # Surface Heuristic
                    t_lower = m['tournament'].lower()
                    surface = 'Hard'
                    if 'clay' in t_lower or 'garros' in t_lower or 'rome' in t_lower: surface = 'Clay'
                    elif 'grass' in t_lower or 'wimbledon' in t_lower: surface = 'Grass'
                    
                    db_match = {
                        "tournament_name": m['tournament'],
                        "date": m['date'],
                        "surface": surface,
                        "player1_id": p1_id,
                        "player2_id": p2_id,
                        "winner_id": p1_id, # Scraper returns winner first
                        "score_full": m['score'],
                        "stats_json": {}
                    }
                    
                    # Insert (Silent)
                    try:
                        r = requests.post(f"{SUPABASE_URL}/rest/v1/matches", headers=HEADERS, json=db_match)
                        if r.status_code == 201: saved_count += 1
                    except: pass
                    
                total_saved += saved_count
                print(f"Saved {saved_count}/{len(matches)} matches.")

        except Exception as e:
            print(f"Error: {e}")

        # 3. Random Sleep (Stealth Mode)
        # Sleep between 5 and 15 seconds
        sleep_time = random.uniform(5.0, 15.0)
        # print(f"Sleeping {sleep_time:.1f}s...")
        time.sleep(sleep_time)

    print(f"Stealth Scrape Finished. Total matches saved: {total_saved}")

if __name__ == "__main__":
    # Run for 1 year
    slow_scrape(365)
