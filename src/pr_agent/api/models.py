from pydantic import BaseModel
from typing import List, Optional
from pr_agent.models.issues import CodeIssue

class ReviewRequest(BaseModel):
    repo_url: str
    pr_number: Optional[int] = None
    github_token: Optional[str] = None # Optional, can use env var

class ReviewResponse(BaseModel):
    issues: List[CodeIssue]
    status: str
