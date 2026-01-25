from datetime import datetime, timedelta
from typing import List, Optional
from scrapers.db_client import get_db_client

class MatchService:
    def __init__(self):
        self.db = get_db_client()

    def get_matches(self, date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 100):
        """
        Gets matches for dashboard. By default:
        - Yesterday's finished matches (for recency)
        - Today's matches (live, finished, scheduled)
        - Tomorrow's matches (for pre-analysis)
        """
        try:
            # Default: yesterday through tomorrow
            if not date_from:
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                date_from = yesterday
            if not date_to:
                tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                date_to = tomorrow + "T23:59:59"
            
            # Base query
            query = self.db.from_('matches').select('*, player_a:player1_id(name,rank_single), player_b:player2_id(name,rank_single)')
            
            # Apply Date Filters
            query = query.gte('date', date_from)
            query = query.lte('date', date_to)
                
            # Formatting and Limit
            query = query.order('date', desc=False).limit(limit)
            
            response = query.execute()
            data = response.data if response.data else []
            
            # Today's date for status detection
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Transform for Frontend (Normalize)
            results = []
            for m in data:
                match_date = m['date'][:10] if m.get('date') else ''
                has_winner = bool(m.get('winner_id'))
                is_live = m.get('status') == 'live'  # From DB if scraped
                
                # Determine status
                if is_live:
                    status = "live"
                elif has_winner:
                    status = "finished"
                else:
                    status = "scheduled"
                
                results.append({
                    "id": m['id'],
                    "tournament": m.get('tournament_name', 'Unknown'),
                    "surface": (m.get('surface') or 'Hard').capitalize(),
                    "date": m['date'],
                    "match_date": match_date,
                    "round": m.get('round', ''),
                    "status": status,
                    "score": m.get('score_full', ''),
                    "winner_name": None,  # Could populate if needed
                    "player_a": {
                        "id": m['player1_id'],
                        "name": m['player_a']['name'] if m.get('player_a') else 'Unknown',
                        "ranking": m['player_a'].get('rank_single', 999) if m.get('player_a') else 999
                    },
                    "player_b": {
                        "id": m['player2_id'],
                        "name": m['player_b']['name'] if m.get('player_b') else 'Unknown',
                        "ranking": m['player_b'].get('rank_single', 999) if m.get('player_b') else 999
                    },
                    "winner_id": m.get('winner_id'),
                    "prediction": m.get('prediction')
                })
                
            return results
        except Exception as e:
            print(f"[API Error] get_matches: {e}")
            return []


    def get_match_details(self, match_id: str):
        try:
            query = self.db.from_('matches') \
                .select('*, player_a:player1_id(*), player_b:player2_id(*)') \
                .eq('id', match_id) \
                .single()
            
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"[API Error] get_match_details: {e}")
            return None
