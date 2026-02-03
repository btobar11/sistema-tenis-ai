import math
import numpy as np

# Constants from "The Math"
BETA_CONSTANT = 1.0  # Asymmetry factor for winner vs loser hold rate
MIN_P_HOLD = 0.45
MAX_P_HOLD = 0.95

def parse_score_games(score_str):
    """
    Parses a score string "6-4 6-3" into (winner_games, loser_games).
    Handling tiebreaks: "7-6" -> 7 games to 6 games.
    """
    if not score_str:
        return 0, 0
    
    winner_games = 0
    loser_games = 0
    
    # Remove superscripts/metadata often found in raw scraping if any remain, 
    # but our DB usually has straightforward "6-4 6-4"
    # Basic split by space
    sets = score_str.strip().split(' ')
    
    for s in sets:
        # Expected format "6-4" or "7-6(4)"
        # We just need the main numbers
        parts = s.split('-')
        if len(parts) < 2:
            continue
            
        try:
            # Handle "7(7)-6(5)" or "6-4"
            # Extract digits before any parenthesis
            w_part = parts[0].split('(')[0]
            l_part = parts[1].split('(')[0]
            
            w_g = int(w_part)
            l_g = int(l_part)
            
            winner_games += w_g
            loser_games += l_g
        except ValueError:
            continue
            
    return winner_games, loser_games

def omalley_hold_prob(p_serve):
    """
    Calculates P(Hold) given P(Serve_Point) using O'Malley formula.
    P(Hold) = p^4 (1 + 4q + 10q^2) where q = 1-p
    Assumption: No Deuce advantage difference (Standard Game)
    """
    p = p_serve
    q = 1 - p
    # p^4
    p4 = p**4
    # (1 + 4q + 10q^2)
    term = 1 + 4*q + 10*(q**2)
    
    # Simple approx for standard game:
    # return p4 * term / (p4 * term + q4 * ...) NO, specific formula:
    # O'Malley 2008 eq for game win prob:
    # P_game = p^4 (1 + 4q + 10q^2) + ... [Deuce logic usually implies ~ p^2/(p^2+q^2)]
    #
    # Standard approximation often used:
    # P(Hold) = p^4 * (15 - 34p + 28p^2 - 8p^3) / ... complex
    # Let's use the standard "Newton's" expansion form provided in the request:
    # P(hold) ≈ p^4 * (1 + 4q + 10q^2) is valid for winning to 0, 15, or 30.
    # It misses the deuce cases slightly but is a very close proxy.
    
    # Let's use the explicit exact formula for a standard game:
    # P_hold = p^4 * (1 + 4(1-p) + 10(1-p)^2) + 20*p^3*(1-p)^3 * p^2 / (p^2 + (1-p)^2)
    
    # Deuce probability: 20 * p^3 * q^3
    # Win from Deuce: p^2 / (p^2 + q^2)
    
    p_deuce_reach = 20 * (p**3) * (q**3)
    p_win_from_deuce = (p**2) / (p**2 + q**2)
    
    # Win before deuce (4-0, 4-1, 4-2)
    # 4-0: p^4
    # 4-1: 4 * p^4 * q
    # 4-2: 10 * p^4 * q^2
    p_win_clean = (p**4) * (1 + 4*q + 10*(q**2))
    
    return p_win_clean + p_deuce_reach * p_win_from_deuce

def inverse_omalley(target_p_hold):
    """
    Finds p_serve that produces target_p_hold.
    Uses linear search on lookup table for robustness (vectorized).
    """
    # Create lookup table once (or per call, it's cheap)
    p_values = np.linspace(0.40, 0.95, 1000)
    
    # Vectorized calculation
    q_values = 1 - p_values
    
    p_deuce_reach = 20 * (p_values**3) * (q_values**3)
    p_win_from_deuce = (p_values**2) / (p_values**2 + q_values**2)
    p_win_clean = (p_values**4) * (1 + 4*q_values + 10*(q_values**2))
    
    hold_probs = p_win_clean + p_deuce_reach * p_win_from_deuce
    
    # Find closest
    idx = (np.abs(hold_probs - target_p_hold)).argmin()
    return p_values[idx]

def infer_p_serve(score_str):
    """
    Infers (p_serve_winner, p_serve_loser) from a score string.
    """
    gw, gl = parse_score_games(score_str)
    total_games = gw + gl
    
    if total_games < 4:
        # Too few games to infer anything useful
        return None, None
        
    s_games = math.ceil(total_games / 2.0)
    
    # Estimate raw hold rates with Beta asymmetry
    # Winner usually holds more
    raw_hold_w = (gw + BETA_CONSTANT) / s_games
    raw_hold_l = (gl - BETA_CONSTANT) / s_games
    
    # Clamp to realistic bounds
    # ATP Average hold is ~80%. Range 50% to 99%.
    # 0.55 to 0.95 is a safe "operating window" for inference
    p_hold_w = max(0.55, min(0.95, raw_hold_w))
    p_hold_l = max(0.45, min(0.90, raw_hold_l))
    
    # Invert to get p_serve
    p_serve_p1 = inverse_omalley(p_hold_w)
    p_serve_p2 = inverse_omalley(p_hold_l)
    
    return p_serve_p1, p_serve_p2
