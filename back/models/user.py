from sqlalchemy import Column, String, Boolean, Date
from sqlalchemy.orm import relationship
from models.base_model import BaseModel
from models.profile import Profile
from models.profile import Comment
from models.profile import Certificate
from models.profile import PastWork
from models.notifications import Notification


class User(BaseModel):
    __tablename__ = "users"
    name = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    is_paid = Column(Boolean, default=False)
    expiration_date = Column(Date, nullable=True)
    access_token = Column(String(255))
    status = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(255))
    

    profile = relationship("Profile", uselist=False, back_populates="user")
    posts = relationship("Post", back_populates="user")  # Nueva relación con Post
    comments = relationship("Comment", back_populates="user")
    sent_notifications = relationship("Notification", foreign_keys=[Notification.sender_id], back_populates="sender")
    received_notifications = relationship("Notification", foreign_keys=[Notification.receiver_id], back_populates="receiver")
    certificates = relationship("Certificate", back_populates="user")
    past_works = relationship("PastWork", back_populates="user")
    

