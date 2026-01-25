from scrapers.db_client import get_db_client
import pandas as pd

class PerformanceService:
    def __init__(self):
        self.db = get_db_client()

    def get_performance_summary(self):
        """
        Calculate aggregate metrics from prediction_ledger.
        """
        try:
            # Fetch settled bets
            # In a real scenario, we'd filter result_status in ('won', 'lost')
            # For MVP demo, we fetch all and calculate potential or mock results
            
            query = self.db.client.from_('prediction_ledger').select('*').in_('result_status', ['won', 'lost'])
            data = query.execute().data
            
            if not data:
                return {
                    "roi": 0,
                    "yield": 0,
                    "total_profit": 0,
                    "total_bets": 0,
                    "win_rate": 0,
                    "chart_data": []
                }
            
            df = pd.DataFrame(data)
            
            total_bets = len(df)
            wins = len(df[df['result_status'] == 'won'])
            win_rate = (wins / total_bets) * 100
            
            # Profit logic: 
            # If WON: (stake * odds) - stake  OR just (stake * (odds-1))
            # If LOST: -stake
            # In ledger we store 'profit_loss' which should be pre-calculated by the Oracle (Result Resolution Engine)
            # Assuming 'profit_loss' is populated.
            
            total_profit = df['profit_loss'].sum()
            total_staked = df['stake_suggested'].sum() # Assuming stake unit is 1 or %? 
            # If stake_suggested is %, we assume fixed bankroll for ROI calc or sum absolute units.
            # Let's assume standard unit = 100 USD.
            
            # Simplified:
            roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
            
            # Chart Data (Cumulative)
            df['date'] = pd.to_datetime(df['prediction_date'])
            df = df.sort_values('date')
            df['cumulative_profit'] = df['profit_loss'].cumsum()
            
            chart_data = df[['date', 'cumulative_profit']].to_dict(orient='records')
            
            return {
                "roi": round(roi, 2),
                "yield": round(roi, 2), # Synonym for Yield in betting usually
                "total_profit": round(total_profit, 2),
                "total_bets": total_bets,
                "win_rate": round(win_rate, 1),
                "chart_data": chart_data
            }
            
        except Exception as e:
            print(f"Performance calc error: {e}")
            return None
