from fastapi import APIRouter
from pydantic import BaseModel
from app.models.tutor_response import TutorResponse
from app.services.tutor_service import TutorService

class TutorAskRequest(BaseModel):
    question: str

def setup_tutor_routes(tutor_service: TutorService):
    router = APIRouter()

    @router.post("/tutor/ask", response_model=TutorResponse)
    def ask(request: TutorAskRequest):
        return tutor_service.ask(request.question)

    return router
