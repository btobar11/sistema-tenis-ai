
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from api.services.auth_service import AuthService
from api.services.usage_service import usage_service

class EnterpriseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process Request
        response = await call_next(request)
        
        # Post-Process: Billing
        # Only bill if X-API-Key was present and valid?
        # Or bill matched routes?
        # Actually, if the request was unauthorized (401/403), we might verify key first?
        # But Auth is handled by Dependency Injection in routes.
        # So here we just look for identifying info in request state if we put it there?
        # The dependency `get_current_enterprise_user` returns the user.
        # But middleware runs OUTSIDE the dependency scope.
        
        # Strategy: Inspect Header manually for billing purposes, 
        # OR rely on request.state if we had an auth middleware (not dependency).
        # Simple extraction:
        
        api_key = request.headers.get("X-API-Key")
        if api_key and api_key.startswith("sk_live_"):
            # We don't want to re-validate full hash here (expensive), 
            # just log that *someone* using this prefix made a request.
            # Ideally, we trust the Auth Dependency to have blocked it if invalid.
            # But if 401, we still might want to log "Attempt".
            
            # Let's extract prefix
            prefix = api_key[:12]
            
            # We need Organization ID. 
            # Paradox: We need to validate to know the Org.
            # Solution: For MVP, we do a quick lookup cache or re-validate.
            # AuthService has caching? No.
            # Let's implement a LRU cache in AuthService later.
            
            # Implementation:
            # We successfully logged a request if it has a key.
            # We will try to resolve Org ID.
            
            process_time = (time.time() - start_time) * 1000
            
            # Async task to not block response
            # In FastAPI, BackgroundTasks are better, but Middleware is lower level.
            # We'll run it purely async if event loop allows, or blocking for safety now.
            
            auth = AuthService()
            user = auth.validate_key(api_key) # Cached lookup ideally
            
            if user:
                org_id = user['organization_id']
                await usage_service.log_request(
                    org_id=org_id,
                    key_prefix=prefix,
                    endpoint=request.url.path,
                    method=request.method,
                    status=response.status_code,
                    duration_ms=process_time
                )
                
        return response
