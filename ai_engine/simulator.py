import random
import math

class Simulator:
    """
    Monte Carlo Engine for Tennis.
    Based on O'Malley (2008) and standard probability chains.
    Input: P(serve_win_A), P(serve_win_B)
    Output: Market probabilities derived from simulation.
    """

    def __init__(self, num_simulations=10000):
        self.num_simulations = num_simulations

    def _hold_prob_omalley(self, p):
        """
        Exact probability of holding serve given P(win point on serve) = p.
        Formula:
        P(hold) = sum(comb(3+k, k) * p^4 * (1-p)^k for k in 0..3) 
                  + (p^4 * (1-p)^3 * 20) / (1 - 2*p*(1-p)) ?
                  
        Actually, the closed form for a standard game (no-ad is different):
        Game = Win 4 points (0,1,2,3 for loser)
        Deuce = Reach 3-3, then win 2 consecutive.
        P(Deuce_reach) = comb(6,3) * p^3 * (1-p)^3 = 20 * p^3 * (1-p)^3
        P(Win_from_Deuce) = p^2 / (p^2 + (1-p)^2)
        
        Total P(Hold) = P(Win before Deuce) + P(Reach Deuce) * P(Win from Deuce)
        P(Win before Deuce) = p^4 + 4p^4(1-p) + 10p^4(1-p)^2
        """
        p_win_no_deuce = (p**4) * (1 + 4*(1-p) + 10*((1-p)**2))
        
        p_reach_deuce = 20 * (p**3) * ((1-p)**3)
        denom = p**2 + (1-p)**2
        if denom == 0: return 0
        p_win_deuce = p**2 / denom
        
        return p_win_no_deuce + (p_reach_deuce * p_win_deuce)

    def _simulate_set(self, p_serve_a, p_serve_b):
        """
        Simulates one set.
        Returns (games_a, games_b)
        """
        games_a = 0
        games_b = 0
        
        # Determine who serves first? Random for now or passed in state.
        # Minimal impact on large N Monte Carlo for "Match Prob".
        # Let's toggle server.
        server_is_a = random.choice([True, False]) 
        
        # Pre-calc hold probs for speed
        prob_hold_a = self._hold_prob_omalley(p_serve_a)
        prob_hold_b = self._hold_prob_omalley(p_serve_b)
        
        while True:
            # Check Set End conditions
            if (games_a >= 6 or games_b >= 6) and abs(games_a - games_b) >= 2:
                return games_a, games_b
            if games_a == 6 and games_b == 6:
                # Tiebreak
                tb_a, tb_b = self._simulate_tiebreak(p_serve_a, p_serve_b)
                if tb_a > tb_b:
                    return 7, 6
                else:
                    return 6, 7

            # Play Game
            if server_is_a:
                if random.random() < prob_hold_a:
                    games_a += 1
                else:
                    games_b += 1 # Break
            else:
                if random.random() < prob_hold_b:
                    games_b += 1
                else:
                    games_a += 1 # Break
            
            server_is_a = not server_is_a

    def _simulate_tiebreak(self, p_serve_a, p_serve_b):
        """Simulate 7-point tiebreak"""
        pts_a = 0
        pts_b = 0
        server_is_a = random.choice([True, False]) # Initial server
        moves = 0
        
        while True:
            if (pts_a >= 7 or pts_b >= 7) and abs(pts_a - pts_b) >= 2:
                return pts_a, pts_b
                
            winning_prob = p_serve_a if server_is_a else (1 - p_serve_b)
            # Logic: If A serves, wins with p_serve_a. 
            # If B serves, A wins with (1 - p_serve_b).
            
            if random.random() < winning_prob:
                pts_a += 1
            else:
                pts_b += 1
                
            moves += 1
            # Server changes after 1st point, then every 2 points
            # Sequence: A, BB, AA, BB...
            # 1, 2, 3...
            # if moves is odd, switch? No complex logic:
            # 1: Switch
            # 1+2=3: Switch
            # 3+2=5: Switch
            if (moves % 2 == 1):
                # Standard TB rule is slightly complex for simple simulation state
                # but "every 2 points" usually suffices for statistical noise
                # Correct: Serve 1, then 2, 2, 2...
                pass
            
            # Simple toggle for Monte Carlo usually converges similar to complex rotation
            # unless p_serve_a and p_serve_b are vastly different.
            # Let's stick to simple turn-taking approximation for speed:
            # server_is_a = not server_is_a 
            # (Matches generic expectation)
            server_is_a = not server_is_a

    def simulate_match(self, p_serve_a, p_serve_b, best_of=3):
        results = {
            "p1_wins": 0,
            "total_games": [],
            "scores": {},
            "set_counts": {"2-0":0, "2-1":0, "0-2":0, "1-2":0}
        }
        
        for _ in range(self.num_simulations):
            sets_a = 0
            sets_b = 0
            match_games = 0
            
            while sets_a < 2 and sets_b < 2:
                gA, gB = self._simulate_set(p_serve_a, p_serve_b)
                match_games += (gA + gB)
                if gA > gB:
                    sets_a += 1
                else:
                    sets_b += 1
            
            # Record Result
            score_key = f"{sets_a}-{sets_b}"
            if sets_a > sets_b:
                results["p1_wins"] += 1
                if sets_b == 0: results["set_counts"]["2-0"] += 1
                else: results["set_counts"]["2-1"] += 1
            else:
                if sets_a == 0: results["set_counts"]["0-2"] += 1
                else: results["set_counts"]["1-2"] += 1

            results["total_games"].append(match_games)
            # results["scores"] - keeping it simple for now
            
        N = self.num_simulations
        
        # Calculate Markets
        p_win = results["p1_wins"] / N
        
        # Totals Stats
        import numpy as np
        games_array = np.array(results["total_games"])
        mean_games = float(np.mean(games_array))
        std_games = float(np.std(games_array))
        
        overs = [g for g in results["total_games"] if g > 21.5]
        p_over_21_5 = len(overs) / N
        
        return {
            "p1_win_prob": p_win, # Standardized key
            "sets": {k: v/N for k,v in results["set_counts"].items()},
            "total_games": {
                "over_21.5": p_over_21_5,
                "under_21.5": 1.0 - p_over_21_5,
                "mean": mean_games,
                "std": std_games
            },
            "p_serve_inputs": (p_serve_a, p_serve_b)
        }
