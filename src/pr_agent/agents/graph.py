from typing import Dict, Any
from langgraph.graph import StateGraph, END
from pr_agent.core.state import AgentState
from pr_agent.agents.reviewer import ReviewerAgent
from pr_agent.agents.supervisor import SupervisorAgent
from pr_agent.models.issues import IssueType, CodeIssue
from pr_agent.services.diff_parser import DiffParser
from pr_agent.services.repo_context import RepoContextManager

# Define nodes
def fetch_context_node(state: AgentState) -> Dict[str, Any]:
    # In a real scenario, we'd get the repo URL from the input
    # For now, we assume it's passed or we might need to adjust the state to include repo_url
    # Let's assume the state is initialized with repo_url if needed, or we parse it from somewhere.
    # For this implementation, we'll assume the context is already passed or we fetch it here if missing.
    # But wait, the state has 'repo_context'.
    return {}

def parse_diff_node(state: AgentState) -> Dict[str, Any]:
    # Diff is already in state['pr_diff']
    # We might want to parse it to a structured object if we were passing that around,
    # but the agents currently take the raw string.
    # So this node might be a pass-through or used for validation.
    return {}

def make_reviewer_node(role: IssueType):
    def reviewer_node(state: AgentState) -> Dict[str, Any]:
        agent = ReviewerAgent(role)
        issues = agent.review(state["pr_diff"], state["repo_context"])
        return {"issues": issues}
    return reviewer_node

def supervisor_node(state: AgentState) -> Dict[str, Any]:
    merged_issues = SupervisorAgent.merge_issues(state["issues"])
    # We replace the issues with the merged list
    return {"issues": merged_issues}

# Build graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("fetch_context", fetch_context_node)
workflow.add_node("parse_diff", parse_diff_node)
workflow.add_node("logic_review", make_reviewer_node(IssueType.LOGIC))
workflow.add_node("security_review", make_reviewer_node(IssueType.SECURITY))
workflow.add_node("performance_review", make_reviewer_node(IssueType.PERFORMANCE))
workflow.add_node("style_review", make_reviewer_node(IssueType.STYLE))
workflow.add_node("supervisor", supervisor_node)

# Define edges
workflow.set_entry_point("fetch_context")
workflow.add_edge("fetch_context", "parse_diff")

# Parallel reviews
workflow.add_edge("parse_diff", "logic_review")
workflow.add_edge("parse_diff", "security_review")
workflow.add_edge("parse_diff", "performance_review")
workflow.add_edge("parse_diff", "style_review")

# Fan-in to supervisor
workflow.add_edge("logic_review", "supervisor")
workflow.add_edge("security_review", "supervisor")
workflow.add_edge("performance_review", "supervisor")
workflow.add_edge("style_review", "supervisor")

workflow.add_edge("supervisor", END)

app = workflow.compile()
