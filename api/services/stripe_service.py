
import os
import stripe
from fastapi import HTTPException
from scrapers.db_client import get_db_client

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder") 

class StripeService:
    def __init__(self):
        self.db = get_db_client()
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    async def create_checkout_session(self, user_id: str, plan_type: str):
        """
        Creates a Stripe Checkout Session for subscription.
        """
        # Map plan to Price ID (Configured in Stripe Dashboard)
        # For Demo, we use placeholders or mock if key is invalid
        price_map = {
            "pro": "price_pro_monthly_123",
            "elite": "price_elite_monthly_456"
        }
        price_id = price_map.get(plan_type)
        if not price_id:
            raise HTTPException(status_code=400, detail="Invalid Plan Type")
            
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{self.frontend_url}/#success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{self.frontend_url}/#cancel",
                client_reference_id=user_id,
                metadata={"user_id": user_id, "plan": plan_type}
            )
            return {"checkout_url": session.url}
            
        except Exception as e:
            # Fallback for Demo without real Stripe Key
            print(f"[Stripe] Error: {e}. Returning MOCK URL.")
            return {"checkout_url": f"{self.frontend_url}/#mock_success_pro"}
    
    def get_user_subscription(self, user_id: str):
        """
        Check if user has active premium access.
        """
        try:
            # We assume user_id is passed from Auth 
            # In Supabase Auth, we can query the 'subscriptions' table
            r = self.db.table('subscriptions').select('plan_id, status').eq('user_id', user_id).execute()
            if r.data:
                sub = r.data[0]
                return {
                    "is_premium": sub['plan_id'] in ['pro_monthly', 'elite_monthly', 'creator_lifetime'] and sub['status'] == 'active',
                    "plan": sub['plan_id']
                }
            return {"is_premium": False, "plan": "free"}
        except Exception as e:
            print(f"Sub check error: {e}")
            return {"is_premium": False, "plan": "free"}

    async def handle_webhook(self, payload: bytes, sig_header: str):
        """
        Process Stripe Webhooks securely.
        """
        endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            # Invalid payload
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            await self._fulfill_checkout(session)
            
        return {"status": "success"}

    async def _fulfill_checkout(self, session):
        user_id = session.get("client_reference_id")
        # Or from metadata if set
        # user_id = session['metadata']['user_id']
        plan_id = session['metadata'].get('plan', 'pro_monthly')
        
        if not user_id:
            print("[Stripe] Error: No user_id in session")
            return

        print(f"[Stripe] Fulfilling sub for user {user_id} - Plan: {plan_id}")
        
        # Upsert subscription
        try:
            # expires_at calculation could be done here or in DB trigger
            self.db.table('subscriptions').upsert({
                "user_id": user_id,
                "plan_id": plan_id,
                "status": "active",
                "stripe_customer_id": session.get('customer'),
                "updated_at": "now()" 
            }).execute()
        except Exception as e:
            print(f"[Stripe] DB Error: {e}")

stripe_service = StripeService()
