from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from models.base_model import BaseModel

class Recommendation(BaseModel):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    user_name = Column(String(255), nullable=False)
    recommendation_text = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
