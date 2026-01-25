import re
import time
from datetime import datetime
from curl_cffi import requests
from bs4 import BeautifulSoup
import json

# Headers for impersonation
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

def clean_text(text):
    if not text:
        return ""
    return text.strip().replace('\xa0', ' ')

def parse_score(score_str):
    """
    Parses score string like "6-4 6-4" into sets won/lost/played.
    Returns: (sets_played, is_straight_sets, outcome_json)
    """
    # Simple heuristic
    parts = score_str.split(' ')
    valid_parts = [p for p in parts if '-' in p]
    sets_played = len(valid_parts)
    # This is a simplification. Real parsing would check who won each set.
    # For now we assume the winner won > loser.
    is_straight_sets = False
    
    # We can refine this logic if we have the winner context
    return sets_played, is_straight_sets

def scrape_match_details(match_url):
    """
    Fetches detailed stats for a match if available.
    Returns a dict of stats.
    """
    stats = {}
    try:
        # print(f"Fetching details: {match_url}")
        # Retry logic
        for attempt in range(3):
            try:
                response = requests.get(match_url, impersonate="chrome110", headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    break
            except Exception as e:
                if attempt == 2: raise e
                time.sleep(2)
        
        if response.status_code != 200:
            return stats
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Metadata
        # (Could extract weather, duration if needed)

        # 2. Detailed Stats Table
        # Often a table with class 'center'
        center_tables = soup.find_all('table', class_='center')
        for tbl in center_tables:
            text = tbl.get_text()
            if "1st Serve" in text or "Winning %" in text:
                # Parse rows
                rows = tbl.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        label = clean_text(cols[1].get_text())
                        # P1 value = cols[0], P2 value = cols[2]
                        # We need to map this to "winner" vs "loser" which is tricky without context.
                        # Usually P1 is left, P2 is right.
                        # We'll store it as 'raw_p1', 'raw_p2' for now or mapped by name if possible.
                        # store raw mapping
                        stats[label] = {
                            "p1": clean_text(cols[0].get_text()),
                            "p2": clean_text(cols[2].get_text())
                        }
        
    except Exception as e:
        print(f"Error scraping details: {e}")
        
    return stats

def scrape_today_results(target_date=None):
    """
    Scrapes results from TennisExplorer.
    target_date: datetime object or None (defaults to today)
    Returns a list of match dicts.
    """
    if target_date is None:
        target_date = datetime.now()
        
    today_str = target_date.strftime("%Y-%m-%d")
    year, month, day = today_str.split('-')
    url = f"https://www.tennisexplorer.com/results/?type=all&year={year}&month={month}&day={day}"
    print(f"Scraping URL: {url}")
    
    matches = []
    
    # Retry logic for main page
    response = None
    for attempt in range(3):
        try:
            response = requests.get(url, impersonate="chrome110", headers=HEADERS, timeout=15)
            if response.status_code == 200:
                break
        except Exception as e:
            print(f"Connection error (attempt {attempt+1}): {e}")
            if attempt == 2: raise e
            time.sleep(3)
            
    if not response:
        return []

    print(f"Status Code: {response.status_code}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Debug: Check title
    print(f"Page Title: {soup.title.text if soup.title else 'No Title'}")
    
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables.")
    
    table = soup.find('table', class_='result')
    if not table:
        print("[ERROR] 'result' table not found.")
        return []
        
    current_tournament = "Unknown"
    
    rows = table.find_all('tr')
    print(f"Found {len(rows)} rows in result table.")
    
    pending_match = None
    
    for row in rows:
        try:
            # Check for Tournament Header
            if 'head' in row.get('class', []):
                links = row.find_all('a')
                if links:
                    current_tournament = clean_text(links[0].text)
                pending_match = None
                continue
                
            cols = row.find_all('td')
            if len(cols) < 2: continue 
            
            col_texts = [c.get_text().strip() for c in cols]
            
            # Check for "info" link (Row 1 indicator)
            info_links = row.find_all('a', href=True)
            detail_url = None
            for l in info_links:
                if "match-detail" in l['href']:
                    detail_url = "https://www.tennisexplorer.com" + l['href']
                    break
            
            # Determine Row 1 vs Row 2
            is_row_1 = False
            if detail_url:
                is_row_1 = True
            elif pending_match is None and ":" in col_texts[0]:
                is_row_1 = True
                
            if is_row_1:
                # Row 1 Processing
                p_idx = 0
                if ":" in col_texts[0]:
                    p_idx = 1
                
                if len(col_texts) > p_idx and '/' in col_texts[p_idx]:
                    pending_match = None
                    continue

                p1_cell = cols[p_idx]
                p1_name = p1_cell.get_text().strip()
                
                p1_is_winner = bool(p1_cell.find('b') or p1_cell.find('strong'))
                
                scores_1 = []
                # Scores start after sets col (col 2 or 3)
                start_score = p_idx + 2
                for x in col_texts[start_score:]:
                    if not x: continue
                    if '.' in x: break
                    scores_1.append(x)
                
                pending_match = {
                    "p1_name": p1_name,
                    "p1_winner": p1_is_winner,
                    "scores_1": scores_1,
                    "detail_url": detail_url,
                    "tournament": current_tournament,
                    "date": today_str
                }
                
            else:
                # Row 2 Processing
                if not pending_match:
                    continue
                
                p_idx = 0
                # Sanity check: doubles or empty
                if '/' in col_texts[p_idx] or not col_texts[p_idx]:
                    pending_match = None
                    continue

                p2_cell = cols[p_idx]
                p2_name = p2_cell.get_text().strip()
                
                p2_is_winner = bool(p2_cell.find('b') or p2_cell.find('strong'))
                
                scores_2 = []
                start_score = p_idx + 2
                for x in col_texts[start_score:]:
                    if not x: continue
                    if '.' in x: break
                    scores_2.append(x)
                
                # Resolve match
                winner = pending_match['p1_name']
                loser = p2_name
                if p2_is_winner:
                    winner = p2_name
                    loser = pending_match['p1_name']
                
                # Combine scores
                row1_scores = pending_match['scores_1']
                final_scores = []
                for s1, s2 in zip(row1_scores, scores_2):
                     final_scores.append(f"{s1}-{s2}")
                
                score_str = " ".join(final_scores)
                
                match_data = {
                    "date": pending_match['date'],
                    "tournament": pending_match['tournament'],
                    "winner": winner, 
                    "loser": loser,
                    "score": score_str,
                    "detail_url": pending_match['detail_url'],
                    "raw_text": f"{pending_match['p1_name']} vs {p2_name}" 
                }
                matches.append(match_data)
                pending_match = None

        except Exception as e:
            # print(f"Row error: {e}")
            pending_match = None
            continue
            
    return matches

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    from db_client import get_db_client, get_or_create_player
    
    print("Testing extraction...")
    res = scrape_today_results()
    print(f"Found {len(res)} matches today.")
    
    if not res:
        print("No matches to save.")
    else:
        db = get_db_client()
        saved = 0
        
        for m in res:
            try:
                # Resolve player IDs
                winner_id = get_or_create_player(db, m['winner'])
                loser_id = get_or_create_player(db, m['loser'])
                
                if not winner_id or not loser_id:
                    print(f"  [SKIP] Could not resolve players: {m['winner']} vs {m['loser']}")
                    continue
                
                # Insert or update match
                match_record = {
                    "date": m['date'] + "T00:00:00+00:00",
                    "tournament_name": m['tournament'],
                    "player1_id": winner_id,
                    "player2_id": loser_id,
                    "winner_id": winner_id,
                    "score_full": m['score'],
                    "surface": None  # Could extract from tournament if needed
                }
                
                # Check if match exists (by date + players combo)
                existing = db.from_('matches').select('id').eq('date', match_record['date']).eq('player1_id', winner_id).eq('player2_id', loser_id).limit(1).execute()
                
                if existing.data:
                    # Update
                    db.from_('matches').update({
                        "winner_id": winner_id,
                        "score_full": m['score']
                    }).eq('id', existing.data[0]['id']).execute()
                    print(f"  [UPD] {m['winner']} d. {m['loser']} {m['score']}")
                else:
                    # Insert
                    db.from_('matches').insert(match_record).execute()
                    print(f"  [NEW] {m['winner']} d. {m['loser']} {m['score']}")
                
                saved += 1
            except Exception as e:
                print(f"  [ERR] {m.get('raw_text', 'Unknown')}: {e}")
        
        print(f"\nSaved/Updated {saved} matches.")

