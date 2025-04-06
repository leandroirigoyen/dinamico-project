from pydantic import BaseModel

class RecommendationCreate(BaseModel):
    recommendation_text: str
