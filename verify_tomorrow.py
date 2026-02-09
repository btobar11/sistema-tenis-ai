
import os
import sys
from datetime import datetime, timedelta
from scrapers.db_client import get_db_client

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

def verify_tomorrow():
    db = get_db_client()
    
    # Calculate Tomorrow's Date
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    print(f"--- Verifying Matches for {tomorrow} ---")
    
    # Query Matches
    try:
        # Get matches for tomorrow
        res = db.table('matches').select('*').eq('date', tomorrow).execute()
        matches = res.data
        
        if not matches:
            print("❌ No matches found for tomorrow.")
            return

        print(f"✅ Found {len(matches)} matches scheduled for tomorrow.\n")
        
        # Check a sample (first 10)
        print(f"{'TIME':<8} | {'TOURNAMENT':<25} | {'PLAYER 1':<20} | {'PLAYER 2':<20} | {'R1':<4} | {'R2':<4}")
        print("-" * 110)
        
        rankings_found = 0
        total_players = 0
        
        for m in matches[:15]: # Show top 15
            p1_name = m.get('player1_name', 'Unknown')
            p2_name = m.get('player2_name', 'Unknown')
            tourney = m.get('tournament', 'Unknown')[:23]
            time_str = m.get('time', '??:??')
            
            # Check for Player IDs and verify if we have rankings (by querying players table? tedious for loop)
            # Instead, let's just assume if ID exists, we 'might' have data. 
            # Actually, let's just inspect the match rows first. 
            # Ideally we join, but supabase-py select is simple.
            
            # Let's check if we have enriched data in the players table for these names
            # We will do a bulk check after this loop if needed, but for now let's list the verification
            
            # Fetch players to check rankings (optimization: fetch all relevant players in one go?)
            # doing 1-by-1 for this script is fine for small count
            
            p1_data = db.table('players').select('rank_single, country').eq('name', p1_name).execute()
            p2_data = db.table('players').select('rank_single, country').eq('name', p2_name).execute()
            
            r1 = p1_data.data[0]['rank_single'] if p1_data.data else 'N/A'
            r2 = p2_data.data[0]['rank_single'] if p2_data.data else 'N/A'
            
            if r1 != 'N/A': rankings_found += 1
            if r2 != 'N/A': rankings_found += 1
            total_players += 2

            print(f"{time_str:<8} | {tourney:<25} | {p1_name:<20} | {p2_name:<20} | {str(r1):<4} | {str(r2):<4}")

        print("-" * 110)
        print(f"\nData Quality Check:")
        print(f"- Matches found: {len(matches)}")
        print(f"- Player Metadata (Ranking) integrity: {rankings_found}/{total_players} ({(rankings_found/total_players)*100 if total_players else 0:.1f}%)")
        
        if rankings_found < (total_players * 0.5):
            print("⚠️ WARNING: Many players missing rankings. Run player_enrichment.py!")
        else:
            print("✅ Player rankings appear largely populated.")

    except Exception as e:
        print(f"Error querying DB: {e}")

if __name__ == "__main__":
    verify_tomorrow()
