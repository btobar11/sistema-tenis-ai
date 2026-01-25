
import hashlib
import secrets
import os
from datetime import datetime
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from scrapers.db_client import get_db_client

# Header expected: "X-API-Key: sk_live_..."
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

class AuthService:
    def __init__(self):
        self.db = get_db_client()

    def generate_api_key(self, org_id="default"):
        """
        Generate a new secure API key.
        Format: sk_live_<24_chars_random>
        Returns: (raw_key, key_hash, prefix)
        """
        raw_key = f"sk_live_{secrets.token_urlsafe(24)}"
        prefix = raw_key[:12] # sk_live_xxxx
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        return raw_key, key_hash, prefix, org_id

    def create_key_record(self, org_id, scopes=["read:matches"]):
        raw, key_hash, prefix, _ = self.generate_api_key(org_id)
        
        record = {
            "organization_id": org_id,
            "key_hash": key_hash,
            "prefix": prefix,
            "scopes": scopes,
            "is_active": True
        }
        
        # Insert
        try:
            self.db.table('api_keys').insert(record).execute()
            return raw # Return raw only once!
        except Exception as e:
            print(f"Key creation error: {e}")
            return None

    def validate_key(self, raw_key: str):
        if not raw_key or not raw_key.startswith("sk_live_"):
            return None
            
        input_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        prefix = raw_key[:12]
        
        # 1. Lookup by prefix (Optimization to avoid scanning all hashes)
        # Assuming prefix is unique enough or we filter results
        try:
            r = self.db.table('api_keys') \
                .select('*') \
                .eq('prefix', prefix) \
                .eq('is_active', True) \
                .execute()
            
            candidates = r.data
            for key_record in candidates:
                # 2. Verify complete hash
                # Constant time comparison ideally, but basic eq is fine for MVP
                if key_record['key_hash'] == input_hash:
                    # 3. Check expiration if exists
                    if key_record.get('expires_at'):
                       # Convert & Compare Logic
                       pass
                       
                    # 4. Valid! Update last_used (Fire & Forget in prod, sync here)
                    # We might skip update on every request for performance, or put in Redis queue
                    # For MVP, we update efficiently? No, updates are slow.
                    # We'll skip update for now or do it 1/100 times.
                    return key_record
                    
        except Exception as e:
            print(f"Auth Error: {e}")
            
        return None

auth_service = AuthService()

async def get_current_enterprise_user(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=403, detail="Missing API Key")
        
    user = auth_service.validate_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API Key")
        
    return user

# B2C Auth Dependency
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Validates the Supabase JWT token and returns the user ID.
    PROD: Calls Supabase Auth API to verify token integrity and expiration.
    """
    token = credentials.credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY") # Anon key is fine for this check usually, or use Service Role if needed

    if not supabase_url or not supabase_key:
        # Fallback for local dev if keys missing, but warn!
        print("[Auth] WARN: Missing specific keys, allowing mock if in dev?")
        # raise HTTPException(status_code=500, detail="Auth Confiuration Error")
    
    # Verify with Supabase Auth
    # GET /auth/v1/user with Authorization: Bearer <token>
    try:
        url = f"{supabase_url}/auth/v1/user"
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Authentication Token")
            
        user_data = response.json()
        return user_data['id'] # The UUID of the user
        
    except Exception as e:
        print(f"[Auth] Error validating token: {e}")
        raise HTTPException(status_code=401, detail="Authentication Failed")
