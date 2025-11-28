from typing import List, TypedDict, Annotated, Any
import operator
from pr_agent.models.issues import CodeIssue

class AgentState(TypedDict):
    repo_url: str
    pr_number: int
    github_token: str
    pr_diff: str
    pr_diff_structured: Any
    repo_context: str
    issues: Annotated[List[CodeIssue], operator.add]
    final_issues: List[CodeIssue]
