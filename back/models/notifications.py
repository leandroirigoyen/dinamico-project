from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from models.base_model import BaseModel

# Modelo de notificaciones
class Notification(BaseModel):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    content = Column(String(255))
    comment_id = Column(Integer, ForeignKey("comments.id"))  # Agregar esta línea
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_notifications")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_notifications")
    comment = relationship("Comment", foreign_keys=[comment_id])