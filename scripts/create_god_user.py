import os
import secrets
import argparse
from dotenv import load_dotenv
from scrapers.db_client import get_db_client

load_dotenv()
db = get_db_client()

def create_god_user(user_id=None, org_name="Founder"):
    print("⚡ Provisioning CREATOR Access ⚡")
    print("--------------------------------")

    # 1. B2C Access (The Dashboard)
    print("\n[1] B2C Dashboard Access")
    if not user_id:
        print("Skipping B2C setup (No UUID provided). pass --uuid to provision.")
    else:
        try:
            data = {
                "user_id": user_id,
                "plan_id": "creator_lifetime",
                "status": "active",
                "stripe_customer_id": "cust_creator_godmode",
                "updated_at": "now()"
            }
            db.table('subscriptions').upsert(data).execute()
            print(f"✅ User {user_id} is now a CREATOR (Lifetime Access).")
        except Exception as e:
            print(f"❌ Error DB: {e}")

    # 2. B2B Access (The API)
    print("\n[2] B2B Master Key")
    
    import hashlib
    raw_key = f"sk_live_{secrets.token_urlsafe(24)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    prefix = raw_key[:12]
    
    try:
        db.table('api_keys').insert({
            "organization_id": org_name,
            "key_hash": key_hash,
            "prefix": prefix,
            "scopes": ["read:matches", "read:odds", "read:insight", "admin:all"], # God scopes
            "is_active": True
        }).execute()
        
        import time
        time.sleep(1) # Float buffer
        print("\n" * 5)
        print("=" * 60)
        print(f"MASTER_KEY={raw_key}")
        print("=" * 60)
        print("\n")

        with open("master_key.txt", "w") as f:
            f.write(raw_key)
        
    except Exception as e:
        print(f"❌ Error generating Key: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--uuid", help="Supabase User UUID for B2C Access")
    parser.add_argument("--org", default="Founder", help="Organization Name for B2B API Key")
    args = parser.parse_args()
    
    create_god_user(args.uuid, args.org)
