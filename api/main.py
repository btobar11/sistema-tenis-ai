from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.middleware.enterprise import EnterpriseMiddleware

app = FastAPI(
    title="Tennis Intelligence API",
    description="Professional Tennis Analytics Engine",
    version="2.1.0"
)

# Middleware Order Matters: Enterprise (Outer) -> CORS -> ..
app.add_middleware(EnterpriseMiddleware)

# CORS (Allow Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Tighten this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "online", "system": "Tennis Intelligence v2.1", "mode": "Professional"}

from api.routers import matches, players, inference, alerts, performance, payments, daily_edge, fatigue
app.include_router(matches.router)
app.include_router(players.router)
app.include_router(inference.router)
app.include_router(alerts.router)
app.include_router(performance.router)
app.include_router(payments.router)
app.include_router(daily_edge.router)
app.include_router(fatigue.router)
