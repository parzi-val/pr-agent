from typing import List, TypedDict, Annotated
import operator
from pr_agent.models.issues import CodeIssue

class AgentState(TypedDict):
    pr_diff: str
    repo_context: str
    issues: Annotated[List[CodeIssue], operator.add]
