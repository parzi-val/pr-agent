from enum import Enum
from typing import Literal
from pydantic import BaseModel

class IssueType(str, Enum):
    LOGIC = "Logic"
    SECURITY = "Security"
    PERFORMANCE = "Performance"
    STYLE = "Style"

class Severity(str, Enum):
    CRITICAL = "Critical"
    MEDIUM = "Medium"
    LOW = "Low"

class CodeIssue(BaseModel):
    file_path: str
    line_number: int
    issue_type: IssueType
    severity: Severity
    description: str
    suggestion: str
