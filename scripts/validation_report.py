import sys
import os
from datetime import datetime
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scrapers.db_client import get_db_client

def run_validation_report():
    print(f"[{datetime.now()}] --- Generating Validation Report ---")
    
    db = get_db_client()
    if not db:
        print("[ERR] No DB Connection")
        return

    # 1. Fetch Settled Snapshots
    # Result must be NOT NULL (WIN, LOSS, VOID)
    res = db.from_('prediction_snapshots').select('*').not_.is_('result', 'null').execute()
    
    if res.error:
        print(f"[ERR] Fetch Error: {res.error}")
        return
        
    data = res.data
    if not data:
        print("[INFO] No settled snapshots found. Validation requires 'result' field to be WIN/LOSS.")
        print("Wait for matches to finish and run 'result_backfill.py' first.")
        return

    df = pd.DataFrame(data)
    
    # Ensure numeric types
    numeric_cols = ['edge', 'trust_score', 'odds_p1', 'odds_p2', 'p_match_p1', 'p_match_p2']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 2. Filter: Only Active Bets
    df_bets = df[df['side_taken'].notna()].copy()
    
    total_snapshots = len(df)
    total_bets = len(df_bets)
    
    print(f"\n--- General Overview ---")
    print(f"Total Snapshots: {total_snapshots}")
    print(f"Active Bets (Triggered): {total_bets} ({total_bets/total_snapshots:.1%})")
    
    if total_bets == 0:
        print("No active bets to analyze.")
        return

    # 3. Calculate P&L
    # Assuming Stake = 1 unit for all (or use 'stake_unit' column)
    df_bets['profit'] = 0.0
    
    def calc_profit(row):
        side = row['side_taken']
        res = row['result']
        odds = row['odds_p1'] if side == 'P1' else row['odds_p2']
        
        if res == 'VOID': return 0.0
        
        # Assuming result assumes P1 perspective (WIN means P1 won?)
        # Need strict definition. Usually 'result' column stores 'WIN' if the BET won.
        # Implies result_backfill calculates correctness.
        # Let's assume result is 'WIN' or 'LOSS' relative to the bet.
        
        if res == 'WIN':
            return (odds - 1.0)
        elif res == 'LOSS':
            return -1.0
        return 0.0

    df_bets['profit'] = df_bets.apply(calc_profit, axis=1)
    
    total_profit = df_bets['profit'].sum()
    total_roi = (total_profit / total_bets) * 100
    
    print(f"\n--- Performance (Flat Stake) ---")
    print(f"Total P&L: {total_profit:+.2f} units")
    print(f"ROI: {total_roi:+.2f}%")
    
    # 4. Analysis by Buckets
    print("\n--- ROI by Trust Score ---")
    # Buckets: 0-50, 50-60, 60-70, 70-80, 80+
    bins = [0, 0.5, 0.6, 0.7, 0.8, 1.0]
    labels = ['<50%', '50-60%', '60-70%', '70-80%', '>80%']
    
    df_bets['trust_bucket'] = pd.cut(df_bets['trust_score'], bins=bins, labels=labels)
    grouped = df_bets.groupby('trust_bucket', observed=False)['profit'].agg(['count', 'sum', 'mean'])
    grouped['roi'] = grouped['mean'] * 100
    print(grouped[['count', 'sum', 'roi']].rename(columns={'sum':'p&l', 'mean':'avg_u'}))

    print("\n--- ROI by Edge ---")
    # Buckets: 0-5%, 5-10%, 10-20%, 20%+
    e_bins = [0, 0.05, 0.10, 0.20, 10.0]
    e_labels = ['0-5%', '5-10%', '10-20%', '>20%']
    
    df_bets['edge_bucket'] = pd.cut(df_bets['edge'], bins=e_bins, labels=e_labels)
    e_grouped = df_bets.groupby('edge_bucket', observed=False)['profit'].agg(['count', 'sum', 'mean'])
    e_grouped['roi'] = e_grouped['mean'] * 100
    print(e_grouped[['count', 'sum', 'roi']].rename(columns={'sum':'p&l', 'mean':'avg_u'}))
    
if __name__ == "__main__":
    run_validation_report()
