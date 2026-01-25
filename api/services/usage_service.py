
from datetime import datetime
from scrapers.db_client import get_db_client
import asyncio

class UsageService:
    def __init__(self):
        self.db = get_db_client()

    async def log_request(self, org_id: str, key_prefix: str, endpoint: str, 
                          method: str, status: int, duration_ms: int):
        
        # --- PRICING ENGINE ---
        # Driven by b2b_specs.md
        PRICING = {
            "default": 0.001,      # Base API Request
            "inference": 0.03,     # AI Model Execution
            "enrichment": 0.10,    # Heavy Data (Future)
            "history": 0.0005      # Bulk History
        }

        # Determine Event Type & Cost
        event_type = "api_request"
        unit_price = PRICING["default"]

        if "predict" in endpoint or "alerts" in endpoint:
            event_type = "inference"
            unit_price = PRICING["inference"]
        elif "performance" in endpoint:
            # Maybe standard, or slightly higher? Stick to standard for now.
            pass
            
        # Calculate Total Cost for this event (Single unit usually per request)
        units = 1
        total_cost = units * unit_price
            
        record = {
            "organization_id": org_id,
            "api_key_prefix": key_prefix,
            "endpoint": endpoint,
            "method": method,
            "status_code": status,
            "cost_units": units,
            "event_type": event_type,
            "cost_usd": total_cost,
            "processing_time_ms": int(duration_ms),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Fire & Forget insert
        try:
            # Using table().insert().execute() via the fluent client or official
            self.db.table('usage_logs').insert(record).execute()
        except Exception as e:
            print(f"[Billing] Failed to log usage: {e}")

usage_service = UsageService()
