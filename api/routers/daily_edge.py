from fastapi import APIRouter, HTTPException, Depends
from scrapers.db_client import get_db_client
from api.services.auth_service import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/daily-edge", tags=["Daily Edge"])
db = get_db_client()

@router.get("/picks")
def get_daily_edge_picks(
    min_ev: float = 3.0,
    user_id: str = Depends(get_current_user)
):
    """
    Get today's edge picks from the Validation Core (prediction_snapshots).
    Premium users only.
    """
    # Lazy import to avoid circular dependency
    from api.services.stripe_service import stripe_service
    
    sub = stripe_service.get_user_subscription(user_id)
    if not sub['is_premium']:
        raise HTTPException(status_code=402, detail="Premium Subscription Required")

    try:
        # Fetch active snapshots
        # Filter by recent (last 72h) to imply 'Daily'
        three_days_ago = (datetime.utcnow() - timedelta(days=3)).isoformat()
        
        # Query Snapshot Table
        # Using None instead of 'null' string for safety
        r = db.from_('prediction_snapshots') \
            .select('*') \
            .not_.is_('side_taken', 'null') \
            .gte('created_at', three_days_ago) \
            .order('created_at', desc=True) \
            .limit(50) \
            .execute()
        
        raw_picks = r.data or []
        
        # 1. Deduplicate by upcoming_match_id (Keep latest)
        latest_by_match = {}
        for p in raw_picks:
            mid = p.get("upcoming_match_id")
            # If no ID, use player names as key? Fallback only.
            key = mid if mid else f"{p.get('player_1')}_{p.get('player_2')}"
            
            if key not in latest_by_match:
                latest_by_match[key] = p
            else:
                # Assuming query ordered by created_at desc, first one is latest
                # But to be safe:
                if p.get('created_at') > latest_by_match[key].get('created_at'):
                    latest_by_match[key] = p
        
        unique_picks = list(latest_by_match.values())

        # 2. Filter & Format
        valid_picks = []
        for p in unique_picks:
            edge_dec = float(p.get('edge') or 0)
            ev_pct = edge_dec * 100
            
            if ev_pct < min_ev:
                continue
                
            side = p.get('side_taken')
            is_p1 = (side == 'P1')
            
            # Extract values based on side
            selection_name = p.get('player_1') if is_p1 else p.get('player_2')
            prob = float(p.get('p_match_p1') if is_p1 else p.get('p_match_p2') or 0)
            odds = float(p.get('odds_p1') if is_p1 else p.get('odds_p2') or 0)
            trust = float(p.get('trust_score') or 0)
            
            # Kelly Criterion Calculation (Simple Fraction)
            bankroll_fraction = 0.0
            if odds > 1:
                b = odds - 1
                q = 1.0 - prob
                bankroll_fraction = (b * prob - q) / b
            
            # Conservative Kelly (Quarter Kelly)
            kelly_pct = max(0, bankroll_fraction * 0.25 * 100)
            
            # 3. Institutional Cap (Max 2% - Hard Limit)
            kelly_pct = min(kelly_pct, 2.0)
            
            # 4. Trust Labels
            trust_label = "Low"
            if trust >= 0.8:
                trust_label = "High"
            elif trust >= 0.65:
                trust_label = "Medium"
                
            # Compound Score for Sorting
            compound_score = edge_dec * trust
            
            valid_picks.append({
                "id": p.get("id"),
                "selection": selection_name,
                "ev_percentage": round(ev_pct, 2),
                "kelly_stake": round(kelly_pct, 2),
                "market_price": odds,
                "model_probability": round(prob, 3), # More precision for pros
                "bookmaker": "Market Consensus", 
                "player_home": p.get("player_1"),
                "player_away": p.get("player_2"),
                "confidence": {
                    "score": round(trust, 2),
                    "label": trust_label
                },
                "match": {
                    "id": p.get("upcoming_match_id"),
                    "tournament": p.get("tournament"),
                    "surface": p.get("surface"),
                    "date": p.get("match_date"),
                    "player_a_name": p.get("player_1"),
                    "player_b_name": p.get("player_2"),
                },
                "_sort_score": compound_score
            })
            
        # Sort by Compound Score (Edge * Trust)
        valid_picks.sort(key=lambda x: x["_sort_score"], reverse=True)
        
        # Remove internal sort key
        for vp in valid_picks:
            del vp["_sort_score"]
        
        return {
            "picks": valid_picks,
            "count": len(valid_picks),
            "min_ev_filter": min_ev,
            "source": "validation_core_v1",
            "disclaimer": "Quantitative signal based on probabilistic simulation. Not investment advice.",
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Daily Edge Error: {e}")
        return {"picks": [], "count": 0, "error": str(e)}


@router.get("/summary")
def get_daily_summary(user_id: str = Depends(get_current_user)):
    """
    Get summary statistics for today's edge opportunities from Snapshots.
    """
    from api.services.stripe_service import stripe_service
    
    sub = stripe_service.get_user_subscription(user_id)
    if not sub['is_premium']:
        raise HTTPException(status_code=402, detail="Premium Subscription Required")
    
    try:
        # 48h window for 'Daily' summary
        two_days_ago = (datetime.utcnow() - timedelta(hours=48)).isoformat()
        
        # Safe syntax for null check
        r = db.from_('prediction_snapshots') \
            .select('edge, side_taken, result, upcoming_match_id, created_at') \
            .not_.is_('side_taken', 'null') \
            .gte('created_at', two_days_ago) \
            .order('created_at', desc=True) \
            .execute()
        
        raw_snaps = r.data or []
        
        # Deduplicate Logic here too for accurate counts
        latest = {}
        for s in raw_snaps:
            mid = s.get('upcoming_match_id')
            if mid and mid not in latest:
                latest[mid] = s
        
        unique_snaps = list(latest.values())
        
        if not unique_snaps:
            return {
                "total_opportunities": 0,
                "avg_ev": 0,
                "max_ev": 0,
                "high_confidence_count": 0
            }
        
        edges = [float(s['edge'] or 0) * 100 for s in unique_snaps] # Convert to %
        
        return {
            "total_opportunities": len(unique_snaps),
            "avg_ev": round(sum(edges) / len(edges), 2) if edges else 0,
            "max_ev": round(max(edges), 2) if edges else 0,
            "high_confidence_count": len([e for e in edges if e > 10.0])
        }
        
    except Exception as e:
        return {"error": str(e)}
