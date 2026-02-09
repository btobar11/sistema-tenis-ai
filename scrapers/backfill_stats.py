import os
import re
import time
from datetime import datetime, timedelta
from curl_cffi import requests
from bs4 import BeautifulSoup
from db_client import get_db_client

# Headers for impersonation
from stats_utils import scrape_detailed_stats, save_stats



def run_backfill(days_lookback=30):
    print(f"[{datetime.now()}] Starting Stats Backfill (Last {days_lookback} days)...")
    db = get_db_client()
    
    total_processed = 0
    total_saved = 0
    
    start_date = (datetime.now() - timedelta(days=days_lookback)).strftime("%Y-%m-%d")
    print("Strategy: Re-traversing daily results to find Detail URLs...")
    
    from match_scraper import scrape_today_results
    
    current_date = datetime.now()
    
    for i in range(days_lookback):
        target_date = current_date - timedelta(days=i)
        date_str = target_date.strftime("%Y-%m-%d")
        print(f"\nProcessing {date_str}...")
        
        matches_found = 0
        try:
            daily_matches = scrape_today_results(target_date)
            matches_found = len(daily_matches)
        except Exception as e:
            print(f"  [Error] Failed to scrape day {date_str}: {e}")
            continue
            
        print(f"  Found {matches_found} matches.")
        
        for m in daily_matches:
            url = m.get('detail_url')
            if not url: continue
            
            total_processed += 1
            
            # Resolve Players (with safety check?)
            # The get_or_create logic in db_client is basic.
            # User warned about ambiguity. For now, we rely on existing logic but log warnings if names look generic?
            # Assuming get_or_create handles it reasonably well for ATP level.
            from db_client import get_or_create_player
            w_id = get_or_create_player(db, m['winner'])
            l_id = get_or_create_player(db, m['loser'])
            
            if not w_id or not l_id: 
                print(f"    [SKIP] Unresolved players: {m['winner']} / {m['loser']}")
                continue
            
            # Find Match ID using robust logic
            # We explicitly look for the match on that date with these two players
            day_start = m['date'] + "T00:00:00"
            day_end = m['date'] + "T23:59:59"
            
            # Use the same robust query syntax as in db_client
            res = db.from_('matches')\
                .select('id, player1_id, player2_id')\
                .gte('date', day_start)\
                .lte('date', day_end)\
                .or_(f"player1_id.eq.{w_id},player2_id.eq.{w_id}")\
                .execute()
                
            match_uuid = None
            if res.data:
                for rm in res.data:
                    if (rm['player1_id'] == w_id and rm['player2_id'] == l_id) or \
                       (rm['player1_id'] == l_id and rm['player2_id'] == w_id):
                        match_uuid = rm['id']
                        break
            
            if not match_uuid:
                # Match missing in main DB -> INSERT IT
                # We need to insert the match first to link stats to it.
                print(f"    [INFO] Match not found in DB. Inserting: {m['winner']} vs {m['loser']}")
                
                new_match = {
                    "date": m['date'] + "T00:00:00+00:00",
                    "tournament_name": m['tournament'],
                    "player1_id": w_id,
                    "player2_id": l_id,
                    "winner_id": w_id, # Scraper structure implies p1/p2 resolution logic, here assuming p1=winner for simplicity or using m['winner']
                    "score_full": m['score'],
                    "surface": None 
                }
                
                # Careful with winner/loser logic from scraper.
                # m['winner'] is the name. w_id is its ID.
                # We assume w_id won.
                
                try:
                    ins_res = db.from_('matches').insert(new_match).execute()
                    if ins_res.data:
                        match_uuid = ins_res.data[0]['id']
                    else:
                        print("    [ERR] Failed to insert match.")
                        continue
                except Exception as e:
                     print(f"    [ERR] Insert Match Error: {e}")
                     continue
                
            # Check if stats already exist? (Optimization)
            # ...
            
            print(f"    Scraping stats for {m['winner']} vs {m['loser']}...")
            stats = scrape_detailed_stats(url)
            
            if stats:
                # Determine who is who
                left_name = m['raw_text'].split(' vs ')[0]
                right_name = m['raw_text'].split(' vs ')[1]
                
                left_id = get_or_create_player(db, left_name)
                right_id = get_or_create_player(db, right_name)
                
                saved_count = 0
                if left_id and stats.get('p1'):
                    save_stats(db, match_uuid, left_id, stats['p1'])
                    saved_count += 1
                
                if right_id and stats.get('p2'):
                    save_stats(db, match_uuid, right_id, stats['p2'])
                    saved_count += 1
                    
                if saved_count > 0:
                    total_saved += 1
                    
            time.sleep(0.5) 
            
    print(f"\nBackfill Complete. Processed {total_processed} matches. With Stats: {total_saved}.")

if __name__ == "__main__":
    run_backfill(days_lookback=3)
