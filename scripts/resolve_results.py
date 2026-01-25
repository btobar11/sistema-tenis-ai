"""
Result Resolution Oracle
Resolves pending predictions in the ledger by checking match results.
Should run as a scheduled job after matches complete.
"""

import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.db_client import get_db_client

class ResultOracle:
    def __init__(self):
        self.db = get_db_client()
    
    def resolve_pending_predictions(self):
        """
        Process all pending predictions and update their status based on match results.
        """
        print(f"[{datetime.now()}] Starting Result Resolution...")
        
        # Get pending predictions
        try:
            pending = self.db.client.from_('prediction_ledger') \
                .select('*, match:matches(id, winner_id, player_a_id, player_b_id, status)') \
                .eq('result_status', 'pending') \
                .execute()
            
            predictions = pending.data or []
            print(f"Found {len(predictions)} pending predictions.")
            
            resolved_count = 0
            
            for pred in predictions:
                match = pred.get('match')
                if not match:
                    print(f"  [SKIP] Prediction {pred['id']}: No linked match")
                    continue
                
                # Check if match is completed
                if match.get('status') != 'completed' and not match.get('winner_id'):
                    continue  # Match not finished yet
                
                winner_id = match.get('winner_id')
                if not winner_id:
                    continue
                
                # Determine result
                selected_pick = pred.get('selected_pick')
                player_a_id = match.get('player_a_id')
                player_b_id = match.get('player_b_id')
                
                predicted_player_id = player_a_id if selected_pick == 'player_a' else player_b_id
                
                is_won = (str(winner_id) == str(predicted_player_id))
                
                # Calculate P/L
                # If WON: (stake * odds) - stake = stake * (odds - 1)
                # If LOST: -stake
                stake = pred.get('stake_suggested', 1.0)
                odds = pred.get('home_odds') if selected_pick == 'player_a' else pred.get('away_odds')
                
                if is_won and odds:
                    profit_loss = stake * (float(odds) - 1)
                else:
                    profit_loss = -stake
                
                # Update ledger
                try:
                    self.db.client.from_('prediction_ledger') \
                        .update({
                            'result_status': 'won' if is_won else 'lost',
                            'profit_loss': round(profit_loss, 2)
                        }) \
                        .eq('id', pred['id']) \
                        .execute()
                    
                    resolved_count += 1
                    status_str = "✓ WON" if is_won else "✗ LOST"
                    print(f"  [{status_str}] Pred {pred['id'][:8]}... P/L: {profit_loss:+.2f}")
                    
                except Exception as e:
                    print(f"  [ERROR] Failed to update {pred['id']}: {e}")
            
            print(f"\n[COMPLETE] Resolved {resolved_count}/{len(predictions)} predictions.")
            return resolved_count
            
        except Exception as e:
            print(f"[ERROR] Result resolution failed: {e}")
            return 0


def main():
    oracle = ResultOracle()
    oracle.resolve_pending_predictions()


if __name__ == "__main__":
    main()
