from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class SeverityEnum(str, Enum):
    CONVENTION = "Convention"
    REFACTOR = "Refactor"
    WARNING = "Warning"
    SECURITY = "Security"

class DiagnosticItem(BaseModel):
    rule_code: str
    line: int
    column: int
    message: str
    severity: SeverityEnum

class SubmissionResponse(BaseModel):
    id: str
    student_id: str
    assignment_id: str
    filename: str
    language: str
    status: str
    quality_score: Optional[float] = None
    report_json: Optional[List[DiagnosticItem]] = None

    class Config:
        from_attributes = True

class FixedCodeResponse(BaseModel):
    filename: str
    original_code: str
    fixed_code: str
    changed: bool