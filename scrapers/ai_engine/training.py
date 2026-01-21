import os
import sys
import pandas as pd
import numpy as np
import joblib
import requests
from datetime import datetime
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase credentials not found.")
    sys.exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'tennis_model.pkl')
ENCODER_PATH = os.path.join(os.path.dirname(__file__), 'encoders.pkl')

def fetch_historical_data_rest():
    print("Fetching historical match data via REST API...")
    url = f"{SUPABASE_URL}/rest/v1/matches?select=*&limit=3000&order=date.desc"
    
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Error fetching data: {response.text}")
            return pd.DataFrame()
            
        data = response.json()
        if not data:
            print("No data found in DB.")
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        print(f"Error requesting data: {e}")
        return pd.DataFrame()

def feature_engineering(df):
    print("Engineering features...")
    
    # 1. Basic Cleaning
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df = df.sort_values('date')
    
    processed_rows = []
    
    # Simple In-Memory History
    player_history = {} # {player: [matches]}
    
    for idx, row in df.iterrows():
        p1 = row.get('player1_id')
        p2 = row.get('player2_id')
        winner_id = row.get('winner_id')
        
        if not p1 or not p2: continue
        
        surface = row.get('surface', 'Hard')
        date = row['date']
        
        # --- Helper to calculate stats ---
        def get_stats(player, opponent):
            history = player_history.get(player, [])
            if not history:
                return {'wr': 0.5, 'form': 0.5, 'h2h': 0.5, 'count': 0}
            
            # Surface WR
            surf_matches = [m for m in history if m['surface'] == surface]
            wins = len([m for m in surf_matches if m['winner'] == player])
            wr = wins / len(surf_matches) if surf_matches else 0.5
            
            # Form (Last 10)
            recent = history[-10:]
            wins_recent = len([m for m in recent if m['winner'] == player])
            form = wins_recent / len(recent) if recent else 0.5
            
            # H2H - Match where opponent was involved
            # In history dict, 'opponent' field stores the opponent ID
            h2h_matches = [m for m in history if m['opponent'] == opponent]
            h2h_wins = len([m for m in h2h_matches if m['winner'] == player])
            h2h = h2h_wins / len(h2h_matches) if h2h_matches else 0.5
            
            return {'wr': wr, 'form': form, 'h2h': h2h, 'count': len(history)}
            
        # --- Randomize target for training ---
        # p1 and p2 are IDs. We need to know who won.
        # Check if p1 == winner_id
        p1_won = (p1 == winner_id)
        
        if np.random.random() > 0.5:
            player_a, player_b = p2, p1
            target = 0 if p1_won else 1 # If p2 is A, and p1 won, then A lost (0). If p1 lost, A won (1)? 
            # Wait. If p1_won is True. Random swap -> A=p2, B=p1. Did A win? No. p1 won. So A lost. Target=0.
            # If p1_won is False (p2 won). Random swap -> A=p2, B=p1. Did A win? Yes. Target=1.
        else:
            player_a, player_b = p1, p2
            target = 1 if p1_won else 0
            
        stats_a = get_stats(player_a, player_b)
        stats_b = get_stats(player_b, player_a)
        
        # --- Update History (Post-Match) ---
        winner = winner_id
        
        if p1 not in player_history: player_history[p1] = []
        player_history[p1].append({'date': date, 'surface': surface, 'opponent': p2, 'winner': winner})
        
        if p2 not in player_history: player_history[p2] = []
        player_history[p2].append({'date': date, 'surface': surface, 'opponent': p1, 'winner': winner})
        
        # Skip training if not enough history
        # Relax constraint for synthetic demo to ensure SOME training happens even with low history at start
        if stats_a['count'] < 1 and stats_b['count'] < 1:
            continue
            
        processed_rows.append({
            'wr_diff': stats_a['wr'] - stats_b['wr'],
            'form_diff': stats_a['form'] - stats_b['form'],
            'h2h': stats_a['h2h'],
            'surface': surface,
            'target': target
        })
        
    return pd.DataFrame(processed_rows)

def train():
    df = fetch_historical_data_rest()
    if df.empty:
        print("Dataset empty. Aborting.")
        return

    print(f"Data fetched: {len(df)} raw matches.")
    
    data = feature_engineering(df)
    print(f"Engineered data for training: {len(data)} samples.")
    
    if data.empty:
        print("Not enough data to train (need matches with history).")
        return

    # Categorical Encoding
    le_surface = LabelEncoder()
    # Ensure all possible surfaces are known or handle unknown
    # Simple fix: force common surfaces
    data['surface'] = data['surface'].fillna('Hard')
    data['surface_encoded'] = le_surface.fit_transform(data['surface'].astype(str))
    
    features = ['wr_diff', 'form_diff', 'h2h', 'surface_encoded']
    X = data[features]
    y = data['target']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)
    
    # Evaluate
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"Model Accuracy: {acc:.2f}")
    print(classification_report(y_test, preds))
    
    # Save
    joblib.dump({
        'model': model,
        'surface_encoder': le_surface,
        'features': features
    }, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train()
