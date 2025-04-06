from sqlalchemy import Column, String, Integer, Date, ForeignKey, JSON, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from models.base_model import BaseModel
from datetime import datetime

class Profile(BaseModel):
    __tablename__ = "profile"
    profile_image_path = Column(String(255))
    rating = Column(String(255), nullable=False, default="")
    phone = Column(String(255),nullable=False, default="")
    description = Column(String(255),nullable=False, default="")
    service_type = Column(String(255), nullable=False, default="")
    location = Column(String(255), nullable=False, default="")
    schedule_work = Column(String(50), nullable=False, default="")
    folders = Column(JSON, nullable=False, default={})
    
    

    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    user = relationship("User", back_populates="profile", foreign_keys=[user_id])
    comments = relationship("Comment", back_populates="profile")
    reports = relationship("Report", back_populates="profile")
    certificates = relationship("Certificate", back_populates="profile")
    past_works = relationship("PastWork", back_populates="profile")
    reports = relationship("Report", back_populates="profile")

########## Comment #########

class Comment(BaseModel):
     __tablename__ = "comments"
     content = Column(String(255))
     timestamp = Column(DateTime, default=datetime.now)
     approved = Column(Boolean, default=False)
     notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=True)
     notification = relationship("Notification", foreign_keys=[notification_id])


     user_id = Column(Integer, ForeignKey("users.id"))
     user = relationship("User", back_populates="comments")
     profile_id = Column(Integer, ForeignKey("profile.id"))
     profile = relationship("Profile", back_populates="comments")

     __table_args__ = (UniqueConstraint('user_id', 'profile_id'),)

############ Certificate ############

class Certificate(BaseModel):
    __tablename__ = "certificates"

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="certificates")
    profile_id = Column(Integer, ForeignKey("profile.id"))
    
    folder_name = Column(String(255), index=True)
    
    
    # Agrega una relación one-to-many para las imágenes de certificados
    images = relationship("CertificateImage", back_populates="certificate")
    profile = relationship("Profile", back_populates="certificates")

class CertificateImage(BaseModel):
    __tablename__ = "certificate_images"
    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(Integer, ForeignKey("certificates.id"))
    image_path = Column(String(255))
    
    certificate = relationship("Certificate", back_populates="images")

############## PastWork #################

class PastWork(BaseModel):
    __tablename__ = "past_works"

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="past_works")
    profile_id = Column(Integer, ForeignKey("profile.id"))
    
    folder_name = Column(String(255), index=True)
    
    
    # Agrega una relación one-to-many para las imágenes de certificados
    images = relationship("PastWorkImage", back_populates="past_work")
    profile = relationship("Profile", back_populates="past_works")

class PastWorkImage(BaseModel):
    __tablename__ = "past_work_images"
    id = Column(Integer, primary_key=True, index=True)
    past_work_id = Column(Integer, ForeignKey("past_works.id"))
    image_path = Column(String(255))
    
    past_work = relationship("PastWork", back_populates="images")



    
