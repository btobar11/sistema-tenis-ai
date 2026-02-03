import sys
import os
from datetime import datetime, timedelta
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scrapers.db_client import get_db_client

def normalize_name(name):
    """Normalize player name for robust matching (e.g., 'Nadal R.' -> 'nadal r')"""
    if not name: return ""
    return name.lower().replace('.', '').strip()

def get_player_id(db, name):
    """
    Find player ID by name using ILIKE for robustness.
    Returns UUID string or None.
    """
    # Try exact match first (normalized) ?
    # Using ilike as in match_scraper
    res = db.from_('players').select('id').ilike('name', name).limit(1).execute()
    if res.data:
        return res.data[0]['id']
    return None

def run_result_backfill():
    print(f"[{datetime.now()}] --- Starting Result Backfill ---")
    
    db = get_db_client()
    if not db:
        print("[ERR] No DB Connection")
        return

    # 1. Fetch Open Snapshots
    # Result IS NULL and Match Date < Now ( + buffer, e.g. 2 hours to specify it has started)
    # Actually, we need it to be likely finished. say Now - 4 hours? 
    # Or just check everything in past.
    
    now_utc = datetime.utcnow()
    check_cutoff = (now_utc - timedelta(hours=2)).isoformat()
    
    print(f"Checking for snapshots before (UTC): {check_cutoff}")
    
    # We filter by result IS NULL.
    # Note: 'is_' syntax might vary in client, usually .is_('result', 'null')
    res_snaps = db.from_('prediction_snapshots').select('*').is_('result', 'null').lt('match_date', check_cutoff).limit(100).execute()
    
    if res_snaps.error:
        print(f"[ERR] Failed to fetch snapshots: {res_snaps.error}")
        return
        
    snapshots = res_snaps.data
    print(f"Found {len(snapshots)} snapshots pending settlement.")
    
    if not snapshots:
        return

    settled_count = 0
    
    # Pre-fetch / Cache could go here, but doing row-by-row for safety in V1
    
    for snap in snapshots:
        sid = snap['id']
        p1_name = snap['player_1']
        p2_name = snap['player_2']
        m_date_str = snap['match_date']
        
        # 1. Resolve Player IDs
        p1_id = get_player_id(db, p1_name)
        p2_id = get_player_id(db, p2_name)
        
        if not p1_id or not p2_id:
            # print(f"[WARN] Could not resolve IDs for {p1_name} vs {p2_name}. Skipping.")
            continue
            
        # 2. Find Completed Match
        # Search window: Match Date +/- 1 day (Timezones can be tricky)
        # Parse match_date (could be partial or ISO)
        try:
            # Assuming ISO format from DB
            m_date_obj = datetime.fromisoformat(m_date_str.replace('Z', '+00:00'))
        except:
            # Fallback for simple date
            # m_date_str might be YYYY-MM-DD
            try:
                m_date_obj = datetime.strptime(m_date_str[:10], "%Y-%m-%d")
            except:
                print(f"[ERR] Bad date format: {m_date_str}")
                continue
        
        start_win = (m_date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
        end_win = (m_date_obj + timedelta(days=2)).strftime("%Y-%m-%d")
        
        # Query matches table
        # We need (p1=id1 AND p2=id2) OR (p1=id2 AND p2=id1) AND date in range
        # PostgREST complex OR filter:
        # or=(and(player1_id.eq.ID1,player2_id.eq.ID2),and(player1_id.eq.ID2,player2_id.eq.ID1))
        
        # Constructing filter string for .or_()
        or_filter = f"and(player1_id.eq.{p1_id},player2_id.eq.{p2_id}),and(player1_id.eq.{p2_id},player2_id.eq.{p1_id})"
        
        res_match = db.from_('matches').select('*').gte('date', start_win).lte('date', end_win).or_(or_filter).limit(1).execute()
        
        if res_match.error:
            # print(f"[ERR] Match query error: {res_match.error}")
            continue
            
        if not res_match.data:
            # Match not found (not scraped yet?)
            continue
            
        finished_match = res_match.data[0]
        
        # 3. Determine Outcome
        
        # Check VOID (Walkover / Retirement)
        score = finished_match.get('score_full', '').lower()
        is_void = False
        if 'w/o' in score or 'ret' in score or 'walkover' in score:
            is_void = True
            
        side_taken = snap.get('side_taken')
        
        result = None
        
        if is_void:
            result = 'VOID'
        elif not side_taken:
            # No bet taken. 
            # We strictly set result to NULL according to User?
            # User said: "if snapshot.side_taken is None: continue # no bet, no result"
            # BUT, cleaning up the queue might be good.
            # However, if we populate 'result', validation_report will pick it up.
            # If side_taken is NULL, validation_report ignores it (df_bets filters side_taken notna).
            # So it's safe to mark 'NO_BET' or just leave NULL?
            # Leaving NULL means it will appear in "pending settlement" list forever.
            # Better to mark 'NO_BET' or 'SKIP'?
            # DB 'result' column usually limited to WIN/LOSS/VOID.
            # Let's leave it NULL for now as per user instruction "continue".
            continue
        else:
            # Determine Winner
            winner_id = finished_match.get('winner_id')
            
            # Map Winner ID to P1 or P2 (Snapshot perspective)
            p1_won = (winner_id == p1_id)
            p2_won = (winner_id == p2_id)
            
            if not p1_won and not p2_won:
                # Winner ID matches neither? (Maybe data corruption or sub-in)
                print(f"[WARN] Winner ID {winner_id} matches neither {p1_id} nor {p2_id}")
                continue
                
            if side_taken == 'P1':
                result = 'WIN' if p1_won else 'LOSS'
            elif side_taken == 'P2':
                result = 'WIN' if p2_won else 'LOSS'
        
        # 4. Update Snapshot
        if result:
            upd = db.from_('prediction_snapshots').update({'result': result}).eq('id', sid).execute()
            if not upd.error:
                print(f"[SETTLED] {p1_name} vs {p2_name} | Bet: {side_taken} | Result: {result}")
                settled_count += 1
            else:
                print(f"[ERR] Update failed: {upd.error}")
                
    print(f"Backfill Complete. Settled {settled_count} snapshots.")

if __name__ == "__main__":
    run_result_backfill()
