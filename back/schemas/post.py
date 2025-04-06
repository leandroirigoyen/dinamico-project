from pydantic import BaseModel
from fastapi import UploadFile
from typing import List

class PostSchemaCreation(BaseModel):
    title: str = ""
    description: str = ""
    service_type: str = ""
    location: str = ""
    urgent: bool
    expected_work_date: str = ""
    images: List[UploadFile] = []

