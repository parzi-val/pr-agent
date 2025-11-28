from pydantic import BaseModel
from enum import Enum

class IssueType(Enum):
    LOGIC = "Logic"
    SECURITY = "Security"
    PERFORMANCE = "Performance"
    READABILITY = "Readability"

class Severity(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class CodeIssue(BaseModel):
    id: str = "" # Optional ID for deduplication
    file_path: str
    line_number: int
    issue_type: IssueType
    severity: Severity
    tldr: str # Short summary (10-12 words)
    description: str
    suggestion: str
