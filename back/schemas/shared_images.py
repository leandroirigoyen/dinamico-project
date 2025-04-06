from pydantic import BaseModel
from typing import List
from fastapi import UploadFile

class CertificateCreate(BaseModel):
    folder_name: str  # El nombre de la carpeta
    images: List[UploadFile] = []
    
class CertificateImageResponse(BaseModel):
    id: int
    image_path: str

class CertificateResponse(BaseModel):
    id: int
    user_id: int
    folder_name: str
    images: List[CertificateImageResponse] = []

class CertificateUpdate(BaseModel):
    folder_name: str

class EmptyCertificateImageResponse(BaseModel):
    id: int = None
    image_path: str = None

######### PAST wORK ###########

class PastWorkCreate(BaseModel):
    folder_name: str  # El nombre de la carpeta
    images: List[UploadFile] = []
    
class PastWorkImageResponse(BaseModel):
    id: int
    image_path: str

class PastWorkResponse(BaseModel):
    id: int
    user_id: int
    folder_name: str
    images: List[PastWorkImageResponse] = []

class PastWorkUpdate(BaseModel):
    folder_name: str

class EmptyPastWorkImageResponse(BaseModel):
    id: int = None
    image_path: str = None