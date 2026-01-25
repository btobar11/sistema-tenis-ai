from fastapi import APIRouter
from api.services.inference_service import InferenceService
from pydantic import BaseModel

router = APIRouter(prefix="/inference", tags=["AI Inference"])
service = InferenceService()

class PredictRequest(BaseModel):
    player1_id: str
    player2_id: str

@router.post("/predict")
def predict_matchup(req: PredictRequest):
    return service.predict_matchup(req.player1_id, req.player2_id)
