import os
import requests
import json
import time
from datetime import datetime

class OddsClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("ODDS_API_KEY")
        self.base_url = "https://api.the-odds-api.com/v4/sports"
        # If API key is missing OR is a placeholder, use mock
        self.mock_mode = not self.api_key or self.api_key == "TEST_KEY_IF_HAVE"

    def fetch_tournaments(self, sport="tennis_atp"):
        """
        Fetch active tournaments/events for a sport.
        """
        if self.mock_mode:
            return self._mock_tournaments()

        try:
            url = f"{self.base_url}/{sport}/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "eu,us",
                "markets": "h2h",
                "oddsFormat": "decimal"
            }
            res = requests.get(url, params=params)
            if res.status_code == 200:
                return res.json()
            else:
                print(f"[OddsAPI] Error {res.status_code}: {res.text}")
                return []
        except Exception as e:
            print(f"[OddsAPI] Exception: {e}")
            return []

    def _mock_tournaments(self):
        """
        Return simulated odds for testing without burning API credits.
        """
        # Return structure matches The-Odds-API format
        return [
            {
                "id": "mock_event_1",
                "sport_key": "tennis_atp",
                "sport_title": "ATP Australian Open",
                "commence_time": datetime.utcnow().isoformat() + "Z",
                "home_team": "Jannik Sinner",
                "away_team": "Carlos Alcaraz",
                "bookmakers": [
                    {
                        "key": "pinnacle",
                        "title": "Pinnacle",
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": "Jannik Sinner", "price": 1.85},
                                    {"name": "Carlos Alcaraz", "price": 1.95}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]

    async def fetch_and_save_odds(self, sport="tennis_atp"):
        """
        Fetch odds and save to DB. Async friendly if needed, but requests is sync.
        We stick to sync for now as it's a batch job.
        """
        print(f"[{datetime.now()}] Fetching odds for {sport}...")
        
        # 1. Fetch
        data = self.fetch_tournaments(sport)
        if not data:
            print("No odds data found.")
            return

        # 2. Connect DB
        # Lazy import to avoid circular dep if module loaded early
        from scrapers.db_client import get_db_client
        db = get_db_client()
        if not db:
            print("DB Connection failed.")
            return

        print(f"Processing {len(data)} events for odds...")
        count = 0
        
        for event in data:
            # event keys: id, home_team, away_team, bookmakers
            match_id_provider = event.get('id')
            p_home = event.get('home_team')
            p_away = event.get('away_team')
            
            # For mapping to our internal 'matches' table, we would need fuzzy matching 
            # or a separate 'pending_resolution' process.
            # For 'Value Alerts', we might just save the raw odds and match them at query time
            # or try to match now.
            # 
            # Strategy: Save RAW odds. The 'Value Engine' (CR-02) will join them.
            
            bookmakers = event.get('bookmakers', [])
            for bookie in bookmakers:
                bk_key = bookie.get('key')
                # Find h2h market
                h2h = next((m for m in bookie.get('markets', []) if m['key'] == 'h2h'), None)
                if not h2h: continue
                
                # outcomes
                price_home = None
                price_away = None
                
                for outcome in h2h.get('outcomes', []):
                    if outcome['name'] == p_home:
                        price_home = outcome['price']
                    elif outcome['name'] == p_away:
                        price_away = outcome['price']
                
                if price_home and price_away:
                    # Persist
                    row = {
                        "provider_match_id": match_id_provider,
                        "bookmaker": bk_key,
                        "player_home": p_home,
                        "player_away": p_away,
                        "price_home": price_home,
                        "price_away": price_away,
                        "is_live": False, # Basic pre-match
                        "extracted_at": datetime.utcnow().isoformat()
                    }
                    
                    # Insert directly into market_odds
                    try:
                        # We use raw post because insert_match is specific to 'matches' table
                        # using REST client generic patch/post
                        endpoint = f"{db.url}/rest/v1/market_odds"
                        db._request_with_retry('post', endpoint, json=row)
                        count += 1
                    except Exception as e:
                        print(f"Error saving odds row: {e}")

        print(f"Saved {count} odds snapshots.")

if __name__ == "__main__":
    client = OddsClient()
    # Sync run
    import asyncio
    # Actually fetch_and_save is sync code but conceptually async compatible
    client.fetch_and_save_odds()
