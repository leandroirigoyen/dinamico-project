from pydantic import BaseModel
from typing import List, Union
from datetime import time

class ProfileSchema(BaseModel):
    id: int
    name: str
    description: str = ""
    service_type: List[str]
    location: List[str]
    phone: str = ""
    schedule_work: str = ""

class ServiceTypeSchema(BaseModel):
    id: int
    name: str
    service_type: str

class LocationSchema(BaseModel):
    id: int
    name: str
    location: str

class ScheduleWork(BaseModel):
    is_24_hours: bool
    start_time: str = None
    end_time: str = None