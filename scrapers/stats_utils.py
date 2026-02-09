import re
import time
from curl_cffi import requests
from bs4 import BeautifulSoup

# Headers for impersonation - shared
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

def parse_fraction(text):
    """
    Parses strings like "35/50 (70%)" or "35/50" into (numerator, denominator).
    Returns (None, None) if failed.
    """
    if not text:
        return None, None
    
    # Remove parenthesis part if exists
    clean = re.sub(r'\(.*?\)', '', text).strip()
    
    if '/' in clean:
        try:
            num, den = clean.split('/')
            return int(num), int(den)
        except:
            pass
    return None, None

def scrape_detailed_stats(match_url):
    """
    Scrapes detailed stats from match page.
    Returns: dict with 'p1_stats' and 'p2_stats'.
    """
    p1_stats = {}
    p2_stats = {}
    
    stats_map = {
        "Aces": "aces",
        "Double Faults": "double_faults",
        "1st Serve %": "first_serve_in", # Fraction
        "1st Serve Points Won": "first_serve_points_won", # Fraction
        "2nd Serve Points Won": "second_serve_points_won", # Fraction
        "Break Points Saved": "break_points_saved", # Fraction (Saved / Faced)
        "Service Games Played": "service_games_played", # Int
        "Return Points Won": "return_points_won", # Fraction
        "Total Points Won": "total_points_won" # Fraction
    }
    
    try:
        # Fetch
        r = None
        for attempt in range(3):
            try:
                r = requests.get(match_url, impersonate="chrome110", headers=HEADERS, timeout=10)
                if r.status_code == 200: break
            except:
                time.sleep(2)
        
        if not r or r.status_code != 200:
            return None
            
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Locate Center Table
        # TennisExplorer usually puts stats in a table.center or similar
        # We look for "Winning %" or specific rows
        
        stats_table = None
        
        # The stats table is often NOT class='result', it's class='center' or nested
        # Let's search by content
        for tbl in soup.find_all('table'):
            txt = tbl.get_text()
            if "1st Serve %" in txt or "Aces" in txt:
                stats_table = tbl
                break
                
        if not stats_table:
            # print("Stats table not found")
            return None
            
        rows = stats_table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 3: continue
            
            label_raw = cols[1].get_text(strip=True).replace(':', '')
            
            # Match label to our schema
            # TennisExplorer labels might vary slightly
            key = None
            for k, v in stats_map.items():
                if k in label_raw:
                    key = v
                    break
            
            if not key:
                continue
                
            val1 = cols[0].get_text(strip=True)
            val2 = cols[2].get_text(strip=True)
            
            # Helper to assign
            def assign_val(stats_dict, k, raw_v):
                if k in ["aces", "double_faults", "service_games_played"]:
                    try:
                        stats_dict[k] = int(raw_v)
                    except:
                        pass
                else:
                    # Fractions
                    num, den = parse_fraction(raw_v)
                    if num is not None:
                        if k == "first_serve_in":
                            stats_dict["first_serves_in"] = num
                            stats_dict["first_serves_total"] = den
                        elif k == "first_serve_points_won":
                            stats_dict["first_serve_points_won"] = num
                            stats_dict["first_serve_points_played"] = den
                        elif k == "second_serve_points_won":
                            stats_dict["second_serve_points_won"] = num
                            stats_dict["second_serve_points_played"] = den
                        elif k == "break_points_saved":
                            stats_dict["break_points_saved"] = num
                            stats_dict["break_points_faced"] = den # Denom of Saved is Faced
                        elif k == "return_points_won":
                            stats_dict["return_points_won"] = num
                            stats_dict["return_points_played"] = den
            
            assign_val(p1_stats, key, val1)
            assign_val(p2_stats, key, val2)
            
        return {"p1": p1_stats, "p2": p2_stats}

    except Exception as e:
        print(f"Stats scrape error: {e}")
        return None


# Validations
def validate_stats(stats):
    """Sanity checks for stats dictionary"""
    # Check 1: Won <= Played
    pairs = [
        ("first_serve_points_won", "first_serve_points_played"),
        ("second_serve_points_won", "second_serve_points_played"),
        ("return_points_won", "return_points_played"),
        ("first_serves_in", "first_serves_total")
    ]
    for num_key, den_key in pairs:
        if num_key in stats and den_key in stats:
            if stats[num_key] > stats[den_key]:
                return False, f"Invalid: {num_key} > {den_key}"
                
    return True, "OK"

def save_stats(db, match_id, player_id, s):
    # Validation
    is_valid, msg = validate_stats(s)
    if not is_valid:
        print(f"      [SKIP] Validation Failed: {msg}")
        return

    # Prepare payload
    payload = {
        "match_id": match_id,
        "player_id": player_id,
        "source": "tennis_explorer_backfill"
    }
    payload.update(s)
    
    try:
        # Idempotency via ON CONFLICT (ignoring duplicates silently)
        # Note: Supabase/PostgREST uses `on_conflict` param or `merge-duplicates` header
        endpoint = f"{db.url}/rest/v1/match_stats?on_conflict=match_id,player_id"
        headers = {"Prefer": "resolution=ignore-duplicates"} 
        
        # We need to use internal _request or construct raw call if client helper doesn't expose headers well
        # Our db_client's `from_().insert()` might not expose headers easily without modifying client.
        # Fallback: Try insert, catch error.
        
        db.from_('match_stats').insert(payload).execute()
        # print("      [Saved] Stats inserted.")
    except Exception as e:
        if "unique constraint" in str(e) or "duplicate key" in str(e):
             pass # Ignore duplicates as per idempotency
        else:
             print(f"      [DB Error] {e}")
