import os
import sys
import pandas as pd
import numpy as np
import joblib
import random
from sklearn.model_selection import train_test_split

# Add root to system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.train_pipeline import MLPipeline

MODEL_PATH = "ml/models/xgb_v1.joblib"

def run_backtest():
    print("--- Financial Backtest Simulation ---")
    
    # 1. Load Data & Model
    model = joblib.load(MODEL_PATH)
    pipeline = MLPipeline()
    raw_df = pipeline.fetch_data()
    df = pipeline.feature_engineering(raw_df)
    
    # Split (Must match training split to simulate "Out of Sample" bets)
    X = df.drop(columns=['target'])
    y = df['target']
    
    # Stratified or Random Split 80/20
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Re-attach target to test set for evaluation
    test_set = X_test.copy()
    test_set['actual_winner_is_p1'] = y_test
    
    print(f"   Backtesting on {len(test_set)} unseen matches...")
    
    # 2. Simulate Betting
    bankroll = 1000.0
    history = []
    initial_bankroll = bankroll
    
    bets_placed = 0
    wins = 0
    
    for idx, row in test_set.iterrows():
        # Prepare feature vector (drop metadata info if any added, strict X only)
        # We need to drop 'actual_winner_is_p1' before prediction
        features = row.drop('actual_winner_is_p1').to_frame().T
        
        # Get AI Probability
        prob_p1 = model.predict_proba(features)[0][1]
        
        # Simulate Market Odds
        # Assume Market is efficient but has margin (vig)
        # True prob +/- random noise (inefficiency)
        # e.g. Market Prob = True_Prob + N(0, 0.05)
        # Implied Odds = 1 / Market Prob
        
        # Ground Truth "True Prob" is unknown, proxy is model prob or actual result?
        # Let's simulate Market Odds based on a slightly weaker model (heuristic) noise
        # This simulates "beating the market" if our model is better.
        
        noise = np.random.normal(0, 0.08) # 8% standard deviation in market accuracy
        market_prob_p1 = prob_p1 + noise 
        market_prob_p1 = max(0.05, min(0.95, market_prob_p1)) # Clamp
        
        # Add Margin (5%)
        market_prob_p1_vig = market_prob_p1 * 1.05
        odds_p1 = 1 / market_prob_p1_vig
        
        # Strategy: Value Bet
        # If AI Prob > Implied Prob of Odds
        implied_prob = 1 / odds_p1
        
        edge = prob_p1 - implied_prob
        
        if edge > 0.02: # 2% Edge threshold
            bets_placed += 1
            # Flat Stake or Kelly?
            # Kelly = (bp - q) / b
            # Let's use 2% Flat Stake for stability
            stake = 20.0 
            
            won = (row['actual_winner_is_p1'] == 1)
            
            if won:
                profit = stake * (odds_p1 - 1)
                bankroll += profit
                wins += 1
                res = "WIN"
            else:
                bankroll -= stake
                res = "LOSS"
                
            history.append(bankroll)
            # print(f"Match: AI {prob_p1:.2f} vs Odds {odds_p1:.2f} (Edge {edge:.2f}) -> {res}")

    # 3. Metrics
    roi = ((bankroll - initial_bankroll) / initial_bankroll) * 100
    win_rate = (wins / bets_placed) if bets_placed > 0 else 0
    
    print("\n--- Results ---")
    print(f"Total Bets: {bets_placed} / {len(test_set)}")
    print(f"Win Rate: {win_rate*100:.1f}%")
    print(f"Final Bankroll: ${bankroll:.2f} (Start $1000)")
    print(f"ROI: {roi:.2f}%")
    
    # Drawdown?
    
if __name__ == "__main__":
    run_backtest()
