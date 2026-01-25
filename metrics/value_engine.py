
import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# Add root context
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.db_client import get_db_client
from ai_engine.predict import StatsEngine

# Configuration
DEFAULT_MIN_EV_THRESHOLD = 3.0  # Minimum EV% to trigger alert
DEFAULT_MIN_KELLY = 0.5  # Minimum Kelly stake % for high confidence
SHARP_BOOKS = ['pinnacle', 'betfair']  # Sharp bookmakers for reference
SOFT_BOOKS = ['bet365', 'williamhill', 'unibet', '1xbet']  # Soft books for value

class ValueEngine:
    def __init__(self, min_ev=DEFAULT_MIN_EV_THRESHOLD, multi_book=True):
        self.db = get_db_client()
        self.ai = StatsEngine(self.db)
        self.min_ev = min_ev
        self.multi_book = multi_book

    def run_daily_scan(self, bookmakers=None):
        """
        Run value scan across specified bookmakers.
        
        Args:
            bookmakers: List of bookmakers to scan. If None, scans all available.
        """
        print(f"[{datetime.now()}] Starting Value Scan (Min EV: {self.min_ev}%)...")
        
        # 1. Get Fresh Odds (Assuming they were just scraped)
        # Filter for odds from last hour to ensure relevance
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        # Fetch from multiple bookmakers if enabled
        if bookmakers is None:
            bookmakers = SHARP_BOOKS + SOFT_BOOKS if self.multi_book else ['pinnacle']
        
        all_odds = []
        for book in bookmakers:
            try:
                query = self.db.client.from_('market_odds') \
                    .select('*') \
                    .gte('extracted_at', one_hour_ago) \
                    .eq('bookmaker', book)
                    
                r = query.execute()
                if r.data:
                    all_odds.extend(r.data)
            except Exception as e:
                print(f"  [WARN] Failed to fetch from {book}: {e}")
        
        if not all_odds:
            print("No recent odds found.")
            return []

        print(f"Found {len(all_odds)} active markets across {len(bookmakers)} bookmakers.")
        
        # Deduplicate by match (keep best odds per side)
        market_map = {}
        for odds in all_odds:
            key = f"{odds['player_home']}|{odds['player_away']}"
            if key not in market_map:
                market_map[key] = odds
            else:
                # Keep higher odds for each side
                existing = market_map[key]
                if float(odds.get('price_home', 0)) > float(existing.get('price_home', 0)):
                    market_map[key]['price_home'] = odds['price_home']
                    market_map[key]['bookmaker_home'] = odds['bookmaker']
                if float(odds.get('price_away', 0)) > float(existing.get('price_away', 0)):
                    market_map[key]['price_away'] = odds['price_away']
                    market_map[key]['bookmaker_away'] = odds['bookmaker']
        
        deduped_markets = list(market_map.values())
        print(f"Processing {len(deduped_markets)} unique matches...")
        
        alerts = []
        
        for market in deduped_markets:
            p_home = market['player_home']
            p_away = market['player_away']
            price_home = float(market['price_home'])
            price_away = float(market['price_away'])
            
            # 2. Get AI Prediction
            id_home = self.db.get_or_create_player(p_home)
            id_away = self.db.get_or_create_player(p_away)
            
            if not id_home or not id_away:
                print(f"Could not map players: {p_home} vs {p_away}")
                continue
                
            # Run Inference
            match_synth = {
                "player1_id": id_home,
                "player2_id": id_away,
                "id": "value_scan",
                "date": str(datetime.now())
            }
            
            try:
                pred = self.ai.predict_match(match_synth) 
                
                # 3. Calculate EV
                if pred['winner_id'] == id_home:
                    prob_home = pred['confidence']
                    prob_away = 1.0 - prob_home
                else:
                    prob_away = pred['confidence']
                    prob_home = 1.0 - prob_away
                
                # EV = (Prob * Odds) - 1
                ev_home = (prob_home * price_home) - 1
                ev_away = (prob_away * price_away) - 1
                
                # Convert to percentage
                ev_home_pct = ev_home * 100
                ev_away_pct = ev_away * 100
                
                # Apply minimum EV threshold
                found_value = False
                if ev_home_pct >= self.min_ev:
                    alert = self.create_alert(market, "Home", p_home, price_home, prob_home, ev_home)
                    if alert:
                        alerts.append(alert)
                    found_value = True
                    
                if ev_away_pct >= self.min_ev:
                    alert = self.create_alert(market, "Away", p_away, price_away, prob_away, ev_away)
                    if alert:
                        alerts.append(alert)
                    found_value = True
                    
                if found_value:
                    print(f"  [!!!] VALUE FOUND: {p_home} ({price_home}) vs {p_away} ({price_away}) | EV: {max(ev_home_pct, ev_away_pct):.1f}%")
            
            except Exception as e:
                print(f"Error analyzing {p_home} vs {p_away}: {e}")
                continue
        
        print(f"\n[COMPLETE] Generated {len(alerts)} value alerts.")
        return alerts

    def create_alert(self, market, side, selection_name, price, prob, ev):
        # Insert into value_alerts
        # Kelly Criterion: f* = (bp - q) / b
        # b = odds - 1
        # p = prob
        # q = 1 - p
        b = price - 1
        kelly = (b * prob - (1 - prob)) / b
        kelly_fraction = max(0, kelly * 0.5) # Half Kelly for safety
        
        alert = {
            "player_home": market['player_home'],
            "player_away": market['player_away'],
            "bookmaker": market['bookmaker'],
            "selection": selection_name,
            "market_price": price,
            "model_probability": round(prob, 4),
            "ev_percentage": round(ev * 100, 2),
            "kelly_stake": round(kelly_fraction * 100, 2),
            "status": "active"
        }
        
        try:
            self.db.client.from_('value_alerts').insert(alert).execute()
            
            # --- TR-01: Write to Prediction Ledger (Immutable) ---
            # We record this recommendation forever to track performance.
            ledger_entry = {
                "match_id": market.get('match_id'), # Might be null if raw mapping
                # If we don't have match_id linked yet, we store descriptive info or link later.
                # For Phase 4 MVP, we might skip foreign key constraint or rely on external_id if added.
                # Let's assume we rely on the created alert logic or parallel insert.
                # Simplified: Just log the components needed for TR-02 (Backtesting)
                "prediction_date": datetime.utcnow().isoformat(),
                "prob_p1": prob if side == "Home" else (1-prob),
                "prob_p2": (1-prob) if side == "Home" else prob,
                "model_version": "xgb_v2.1_calibrated",
                "bookmaker": market['bookmaker'],
                "home_odds": price if side == "Home" else 0, # Partial info in alert context
                "away_odds": price if side == "Away" else 0,
                "selected_pick": "player_a" if side == "Home" else "player_b",
                "ev_calculated": ev * 100,
                "stake_suggested": kelly_fraction * 100,
                "result_status": "pending"
            }
            # Note: A real ledger needs robust match_id linking. 
            # For now we insert best-effort to start building history.
            try:
                self.db.client.from_('prediction_ledger').insert(ledger_entry).execute()
            except Exception as le:
                print(f"Ledger Write Error: {le}")
                
        except Exception as e:
            print(f"Failed to save alert: {e}")

if __name__ == "__main__":
    engine = ValueEngine()
    engine.run_daily_scan()
