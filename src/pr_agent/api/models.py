from pydantic import BaseModel
from typing import List
from pr_agent.models.issues import CodeIssue

class ReviewRequest(BaseModel):
    repo_url: str
    pr_number: int
    github_token: str = None # Optional, can use env var

class ReviewResponse(BaseModel):
    issues: List[CodeIssue]
    status: str
