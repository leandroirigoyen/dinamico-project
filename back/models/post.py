from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship
from models.base_model import BaseModel
from models.user import User

class Post(BaseModel):
    __tablename__ = "posts"
    title = Column(String(255))
    description = Column(String(255))
    service_type = Column(String(255))
    location = Column(String(255))
    schedule_work = Column(String(255))
    urgent = Column(Boolean, default=False)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="posts")
    images = relationship("PostImage", back_populates="post")  # Debe coincidir con el nombre en el modelo PostImage

class PostImage(BaseModel):
    __tablename__ = "post_images"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    image_path = Column(String(255))
    
    post = relationship("Post", back_populates="images")  # Debe coincidir con el nombre en el modelo Post
    