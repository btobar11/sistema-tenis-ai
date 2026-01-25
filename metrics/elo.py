import math
from datetime import datetime
from scrapers.db_client import get_db_client

class EloEngine:
    def __init__(self, db_client=None):
        self.db = db_client if db_client else get_db_client()
        self.k_factor = 32 # Standard K-factor, could be dynamic based on matches played

    def _get_expected_score(self, rating_a, rating_b):
        """
        Calculate expected score for player A against player B.
        Formula: 1 / (1 + 10^((Rb - Ra) / 400))
        """
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    # ... (init and db setup)

    def _get_k_factor(self, matches_played):
        """
        Dynamic K-Factor:
        - < 30 matches: K=40 (Placement phase, volatile)
        - > 30 matches: K=32 (Standard)
        - > 100 matches (Elite): K=24 (Stable)
        """
        if matches_played < 30:
            return 40
        elif matches_played > 100:
            return 24
        return 32

    def apply_decay(self, player_id, current_rating, last_update_str, surface):
        """
        Apply temporal decay if inactive.
        Rule: If inactive > 30 days, move 2% closer to 1500 per month of inactivity.
        """
        if not last_update_str:
            return current_rating
            
        try:
            last_date = datetime.fromisoformat(last_update_str)
            # Handle localized timestamps if present
            if last_date.tzinfo is not None:
                last_date = last_date.replace(tzinfo=None)
                
            days_inactive = (datetime.now() - last_date).days
            
            if days_inactive > 30:
                months = days_inactive // 30
                decay_factor = 0.02 * months # 2% per month
                # Decay towards 1500
                diff = 1500 - current_rating
                new_rating = current_rating + (diff * decay_factor)
                
                # print(f"  [ELO Decay] {player_id} ({surface}): {current_rating} -> {int(new_rating)} ({days_inactive}d inactive)")
                return int(new_rating)
        except Exception as e:
            print(f"  [ELO Decay] Error: {e}")
            
        return current_rating

    def calculate_new_ratings(self, rating_a, rating_b, actual_score_a, matches_a=0, matches_b=0):
        """
        Returns new ratings (new_a, new_b).
        """
        ka = self._get_k_factor(matches_a)
        kb = self._get_k_factor(matches_b)
        
        expected_a = self._get_expected_score(rating_a, rating_b)
        expected_b = self._get_expected_score(rating_b, rating_a)
        
        new_a = rating_a + ka * (actual_score_a - expected_a)
        # For loser B, score is (1-score_a)
        new_b = rating_b + kb * ((1 - actual_score_a) - expected_b)
        
        return round(new_a), round(new_b)

    def get_player_elo_data(self, player_id, surface="OVERALL"):
        """
        Fetch current ELO data (rating, matches, last_update) from DB.
        """
        try:
            endpoint = f"{self.db.url}/rest/v1/elo_ratings?player_id=eq.{player_id}&surface=eq.{surface}&select=rating,matches_played,last_update"
            r = self.db._request_with_retry('get', endpoint)
            if r and r.status_code == 200:
                data = r.json()
                if data:
                    return data[0]
        except Exception as e:
            print(f"  [ELO] Fetch error: {e}")
        return {"rating": 1500, "matches_played": 0, "last_update": None}

    def get_player_elo(self, player_id, surface="OVERALL"):
        # Helper for simplified calls
        d = self.get_player_elo_data(player_id, surface)
        return d['rating']

    def update_player_elo(self, player_id, surface, new_rating, matches_played):
        """
        Upsert ELO rating in DB.
        """
        try:
            endpoint = f"{self.db.url}/rest/v1/elo_ratings?on_conflict=player_id,surface"
            payload = {
                "player_id": player_id,
                "surface": surface,
                "rating": new_rating,
                "matches_played": matches_played,
                "last_update": datetime.now().isoformat()
            }
            headers = {"Prefer": "resolution=merge-duplicates"}
            
            r = self.db._request_with_retry('post', endpoint, json=payload, headers=headers)
            if not r or r.status_code not in [200, 201, 204]:
                 print(f"  [ELO] Update failed for {player_id}: {r.text if r else 'No resp'}")
        except Exception as e:
            print(f"  [ELO] Update error: {e}")

    def process_match(self, match):
        """
        Updates ELO for both players based on match result.
        """
        p1 = match.get('player1_id')
        p2 = match.get('player2_id')
        winner = match.get('winner_id')
        
        if not p1 or not p2 or not winner:
            return

        surfaces = ["OVERALL"]
        match_surface = match.get('surface', 'HARD').upper()
        if match_surface in ['HARD', 'CLAY', 'GRASS', 'INDOOR']:
             surfaces.append(match_surface)

        for s in surfaces:
            # 1. Fetch current data
            d1 = self.get_player_elo_data(p1, s)
            d2 = self.get_player_elo_data(p2, s)
            
            r1, r2 = d1['rating'], d2['rating']
            m1, m2 = d1.get('matches_played', 0), d2.get('matches_played', 0)
            
            # 2. Apply Decay (Pre-match processing)
            # Only apply decay if this is a live update or processing a stream, 
            # for historical backfill decay might need careful handling (vs date of match).
            # For simplicity in V2 MVP: Apply decay based on stored 'last_update' vs NOW is correct-ish if LIVE.
            # But if backfilling, last_update is the match date?
            # Let's simple apply decay logic: if database last_update is old, decay it before this match impact.
            
            r1 = self.apply_decay(p1, r1, d1['last_update'], s)
            r2 = self.apply_decay(p2, r2, d2['last_update'], s)
            
            # 3. Calculate New Ratings
            score_p1 = 1 if p1 == winner else 0
            new_r1, new_r2 = self.calculate_new_ratings(r1, r2, score_p1, m1, m2)
            
            # 4. Update DB
            self.update_player_elo(p1, s, new_r1, m1 + 1)
            self.update_player_elo(p2, s, new_r2, m2 + 1)

