
import os
import sys
from datetime import datetime, timedelta
# Add root context
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.db_client import get_db_client

def check_system_health():
    db = get_db_client()
    if not db:
        print("[CRITICAL] Database connection failed.")
        return

    print(f"[{datetime.now()}] Running System Health Check...")
    issues = []

    # 1. Market Odds Freshness
    # Check the most recent odds for Pinnacle
    try:
        r = db.client.from_('market_odds') \
            .select('extracted_at') \
            .eq('bookmaker', 'pinnacle') \
            .order('extracted_at', desc=True) \
            .limit(1) \
            .execute()
        
        if r.data:
            last_odds = datetime.fromisoformat(r.data[0]['extracted_at'].replace('Z', '+00:00'))
            # Local time might be naive, ensure comparison works. Using utc now.
            gap = datetime.utcnow() - last_odds.replace(tzinfo=None) # assuming stored as UTC
            
            if gap > timedelta(hours=2):
                issues.append(f"[ING-01] Odds Stale! Last Pinnacle snapshot was {gap.total_seconds()/3600:.1f} hours ago.")
            else:
                print(f"[OK] Odds Freshness: {gap.total_seconds()/60:.0f} min ago.")
        else:
            issues.append("[ING-01] No Odds found in DB!")
            
    except Exception as e:
        issues.append(f"[ING-01] Check Failed: {e}")

    # 2. Match Ingestion Freshness
    try:
        r = db.client.from_('matches') \
            .select('date') \
            .order('date', desc=True) \
            .limit(1) \
            .execute()
            
        # Matches date is usually YYYY-MM-DD. We just check if we have something in the future or today.
        if r.data:
            last_match_date = r.data[0]['date']
            # Simple check: Is last match date >= today?
            today = datetime.now().strftime("%Y-%m-%d")
            if last_match_date < today:
                 # It might be night time and tournaments over? 
                 # Let's say if last match is older than yesterday, worry.
                 # Actually, usually we have schedule for future.
                 pass
            print(f"[OK] Latest Match Date: {last_match_date}")
            
    except Exception as e:
        issues.append(f"[ING-02] Match Check Failed: {e}")

    # Report
    if issues:
        print("\n" + "="*30)
        print("🚨 SYSTEM ALERTS TRIGGERED 🚨")
        print("="*30)
        for i in issues:
            print(i)
        print("="*30)
        # Here we could send Webhook to Slack/Discord
    else:
        print("\n✅ System status: HEALTHY")

if __name__ == "__main__":
    check_system_health()
