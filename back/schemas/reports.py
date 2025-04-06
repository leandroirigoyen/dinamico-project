from pydantic import BaseModel
from typing import List

class ReportCreate(BaseModel):
    unfinished_work: bool
    missed_completion_time: bool
    low_work_quality: bool
    delayed_responses: bool
    incorrect_profile_info: bool
    unauthorized_images: bool
    message: str

class ReportBase(BaseModel):
    id: int
    profile_id: int
    reported_by_user_id: int
    unfinished_work: bool
    missed_completion_time: bool
    low_work_quality: bool
    delayed_responses: bool
    incorrect_profile_info: bool
    unauthorized_images: bool
    message: str

class ReportList(BaseModel):
    reports: List[ReportBase]