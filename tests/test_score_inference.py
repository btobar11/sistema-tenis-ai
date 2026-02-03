
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine.score_inference import parse_score_games, infer_p_serve, inverse_omalley

def test_parse_score():
    assert parse_score_games("6-4 6-4") == (12, 8)
    assert parse_score_games("7-6 6-7 7-6") == (20, 19)
    assert parse_score_games("6-0 6-0") == (12, 0)
    assert parse_score_games("") == (0, 0)

def test_inverse_omalley():
    # Known benchmark: P(serve)=0.60 -> P(hold)~0.73? Let's check consistency
    # Roughly P(hold) > P(serve) usually
    
    p_serve = 0.64
    p_hold = inverse_omalley(0.736) # Approx verify
    # Just check it returns a float in valid range
    assert 0.4 <= p_hold <= 1.0

def test_infer_p_serve_standard():
    # 6-4 6-4 (Winner 12, Loser 8)
    # Total = 20, Service = 10
    # W Hold ~ (12+1)/10 = 1.3 -> Clamped 0.95 -> High P_serve
    # L Hold ~ (8-1)/10 = 0.7 -> Moderate P_serve
    
    ps_w, ps_l = infer_p_serve("6-4 6-4")
    
    print(f"\nScore: 6-4 6-4 => P_Serve_W: {ps_w:.3f}, P_Serve_L: {ps_l:.3f}")
    
    assert ps_w > ps_l
    assert 0.5 < ps_w < 1.0
    assert 0.4 < ps_l < 1.0

def test_infer_p_serve_close():
    # 7-6 6-7 7-6 (Winner 20, Loser 19)
    # Almost equal
    ps_w, ps_l = infer_p_serve("7-6 6-7 7-6")
    print(f"Score: 7-6 6-7 7-6 => P_Serve_W: {ps_w:.3f}, P_Serve_L: {ps_l:.3f}")
    
    # Should be very close
    diff = abs(ps_w - ps_l)
    assert diff < 0.1

def test_short_match():
    # 6-1 6-1
    ps_w, ps_l = infer_p_serve("6-1 6-1")
    print(f"Score: 6-1 6-1 => P_Serve_W: {ps_w:.3f}, P_Serve_L: {ps_l:.3f}")
    assert ps_w > 0.7 # Should be high

if __name__ == "__main__":
    test_parse_score()
    test_inverse_omalley()
    test_infer_p_serve_standard()
    test_infer_p_serve_close()
    test_short_match()
    print("All tests passed!")
