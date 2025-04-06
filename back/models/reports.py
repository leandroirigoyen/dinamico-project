from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from models.base_model import BaseModel
from models.profile import Profile

class Report(BaseModel):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profile.id"))
    reported_by_user_id = Column(Integer, ForeignKey("users.id"))
    unfinished_work = Column(Boolean, default=False)
    missed_completion_time = Column(Boolean, default=False)
    low_work_quality = Column(Boolean, default=False)
    delayed_responses = Column(Boolean, default=False)
    incorrect_profile_info = Column(Boolean, default=False)
    unauthorized_images = Column(Boolean, default=False)
    message = Column(String(255))
    
    profile = relationship("Profile", back_populates="reports")
    reported_by_user = relationship("User", foreign_keys=[reported_by_user_id])