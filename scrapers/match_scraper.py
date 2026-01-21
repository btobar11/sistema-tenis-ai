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
        response = requests.get(match_url, impersonate="chrome110", headers=HEADERS)
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
    # Use explicit date to avoid timezone ambiguity or default page variations
    if target_date is None:
        target_date = datetime.now()
        
    today_str = target_date.strftime("%Y-%m-%d")
    year, month, day = today_str.split('-')
    url = f"https://www.tennisexplorer.com/results/?type=all&year={year}&month={month}&day={day}"
    print(f"Scraping URL: {url}")
    
    matches = []
    
    try:
        response = requests.get(url, impersonate="chrome110", headers=HEADERS)
        print(f"Status Code: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Debug: Check title
        print(f"Page Title: {soup.title.text if soup.title else 'No Title'}")
        
        # Main table usually has class 'result'
        # table = soup.find('table', class_='result')
        # Debug: Print all table classes
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables.")
        for t in tables[:3]:
            print(f"Table classes: {t.get('class')}")
            
        table = soup.find('table', class_='result')
        if not table:
            print("[ERROR] 'result' table not found.")
            return []
            
        current_tournament = "Unknown"
        
        rows = table.find_all('tr')
        print(f"Found {len(rows)} rows in result table.")
        
        for row in rows:
            # Check for Tournament Header (e.g., class 'head flags')
            if 'head' in row.get('class', []):
                links = row.find_all('a')
                if links:
                    current_tournament = clean_text(links[0].text)
                continue
                
            # Match Row
            cols = row.find_all('td')
            if len(cols) < 4: continue
            
            # Text check
            col_texts = [c.get_text().strip() for c in cols]
            
            # Filter Doubles (contains /)
            if '/' in col_texts[1]: # Assuming Col 1 is players
                continue
            
            # Debug: Singles Match Found?
            # print(f"Singles Row: {col_texts}")
            
            # Heuristic for columns:
            # Col 0: Time
            # Col 1: Players (e.g. "Player A - Player B")
            # Col last or near last: Score?
            
            # Check if Col 0 is time (##:##)
            if ":" not in col_texts[0]: 
                 # Maybe date row or something else
                 continue
                 
            players_cell = cols[1]
            p_text = players_cell.get_text().strip()
            if "-" not in p_text:
                continue
                
            p1_name = p_text.split('-')[0].strip()
            p2_name = p_text.split('-')[1].strip()
            
            # Winner logic:
            # TennisExplorer bolds the winner in the Results table.
            winner = p1_name # default
            loser = p2_name
            
            # Check for bold tag <b> or <strong>
            p1_bold = players_cell.find('b') or players_cell.find('strong')
            # But wait, if text is "Name - Name", bold might be partial.
            # Actually, TE usually bolds the winner's name string.
            
            # Score is often spread across columns? 
            # Or in one column?
            # From debug: ['0', '3', '6', '7'] -> These look like set scores in separate TDs.
            # So we need to join cols 2 onwards?
            score_parts = col_texts[2:-1] # Exclude last "info" col?
            # Let's verify 'info' col logic
            
            detail_url = ""
            info_links = row.find_all('a', href=True)
            for l in info_links:
                if "match-detail" in l['href']:
                    detail_url = "https://www.tennisexplorer.com" + l['href']
                    break
            
            # Parse Score vs Odds
            # Heuristic: Score usually consists of integers 0-7. Odds have dots (1.23).
            # Also TE puts scores before odds.
            
            cleaned_score_parts = []
            for part in col_texts[2:-1]: # Check middle columns
                if not part: continue
                if "." in part: # Odds detected
                    break
                if part.isdigit() or "-" in part: # "6" or "7-6"
                    cleaned_score_parts.append(part)
            
            score_text = " ".join(cleaned_score_parts)
            
            match_data = {
                "date": today_str,
                "tournament": current_tournament,
                "winner": winner, 
                "loser": loser,
                "score": score_text,
                "detail_url": detail_url,
                "raw_text": str(col_texts[:8]) # Truncate for log
            }
            matches.append(match_data)
            
    except Exception as e:
        print(f"Error scraping today results: {e}")
        
    return matches

if __name__ == "__main__":
    # Test
    print("Testing extraction...")
    res = scrape_today_results()
    print(f"Found {len(res)} matches today.")
    for m in res[:3]:
        print(m)
        if m['detail_url']:
            print("  Fetching details...")
            d = scrape_match_details(m['detail_url'])
            print("  Details found keys:", d.keys())
