from scrapers.db_client import get_db_client

class PlayerService:
    def __init__(self):
        self.db = get_db_client()

    def get_player_elo_history(self, player_id: str, surface: str = "OVERALL"):
        # Since we only store *current* ELO in 'elo_ratings' table with 'last_update',
        # we might not have a full timeseries table unless we implemented one.
        # Checking `metrics/elo.py`: it updates `elo_ratings` in place.
        # To show history, we typically need a `elo_history` log table.
        # IF we don't have it, we have to mock it or derive it from matches.
        #
        # "Reconstruct" ELO from matches? Expensive.
        # PROPOSAL: For this MVP phase, we will return the current ELO and simulated history 
        # based on recent match results (wins = up, losses = down) OR check if we have history.
        #
        # Let's check `metrics/elo.py` again. It just upserts `elo_ratings`.
        # So we don't have history storage yet. 
        #
        # ACTION: I will update this service to return the CURRENT ELO and 
        # a "Trend" constructed from the last 10 matches relative to current ELO.
        # This is a valid estimation if we don't have a history log table.
        
        try:
            # Get Current ELO
            query_elo = self.db.client.from_('elo_ratings').select('*').eq('player_id', player_id).eq('surface', surface).single()
            current_elo_data = query_elo.execute().data
            current_elo = current_elo_data['rating'] if current_elo_data else 1500
            
            # Get Match History to estimate previous points
            query_matches = self.db.client.from_('matches') \
                .select('date, winner_id') \
                .or_(f"player1_id.eq.{player_id},player2_id.eq.{player_id}") \
                .order('date', desc=True) \
                .limit(20)
            matches = query_matches.execute().data
            
            # Reconstruct backwards
            history = []
            temp_elo = current_elo
            
            # This is a reverse walk. 
            # If match i (latest), output ELO was temp_elo.
            # Before match i, ELO was ??
            # Rough heuristic: +15 for win, -15 for loss (Avg K=30)
            
            for m in matches:
                history.append({
                    "date": m['date'],
                    "elo": temp_elo
                })
                
                # Reverse the effect to get previous
                if m['winner_id'] == player_id:
                    temp_elo -= 15
                else:
                    temp_elo += 15
                    
            return list(reversed(history))
            
        except Exception as e:
            print(f"[PlayerService] Error: {e}")
            return []

    def get_player_stats(self, player_id: str):
        # reuse logic from api.ts calculatePlayerMetrics if possible, or reimplement in python
        # Python is better for heavy lifting.
        # ... implementation ...
        pass
