from typing import Dict, Any
from langgraph.graph import StateGraph, END
from pr_agent.core.state import AgentState
from pr_agent.agents.reviewer import ReviewerAgent
from pr_agent.agents.supervisor import SupervisorAgent
from pr_agent.models.issues import IssueType, CodeIssue
from pr_agent.services.diff_parser import DiffParser
from pr_agent.services.repo_context import RepoContextManager

import logging

logger = logging.getLogger(__name__)

# Define nodes
def fetch_context_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing fetch_context_node")
    repo_url = state.get("repo_url")
    if not repo_url:
        # Fallback or error if not provided?
        # For now, we assume it's there or we can't fetch context.
        logger.warning("No repo_url provided in state.")
        return {"repo_context": "No repository URL provided."}
        
    context = RepoContextManager.get_context(repo_url)
    logger.info("Fetched repo context.")
    return {"repo_context": context}

def parse_diff_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing parse_diff_node")
    diff_content = state.get("pr_diff")
    if not diff_content:
        logger.warning("No pr_diff provided in state.")
        return {"pr_diff_structured": None}
        
    structured_diff = DiffParser.parse(diff_content)
    logger.info("Parsed diff.")
    return {"pr_diff_structured": structured_diff}

def make_reviewer_node(role: IssueType):
    def reviewer_node(state: AgentState) -> Dict[str, Any]:
        logger.info(f"Executing reviewer_node for role: {role}")
        agent = ReviewerAgent(role)
        # Pass structured diff
        issues = agent.review(state["pr_diff_structured"], state["repo_context"])
        logger.info(f"Reviewer {role} found {len(issues)} issues.")
        return {"issues": issues}
    return reviewer_node

def supervisor_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing supervisor_node")
    supervisor = SupervisorAgent()
    merged_issues = supervisor.merge_issues(state["issues"])
    logger.info(f"Supervisor merged issues into {len(merged_issues)} final issues.")
    # Return to final_issues to avoid appending to the existing issues list (due to operator.add)
    return {"final_issues": merged_issues}

# Build graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("fetch_context", fetch_context_node)
workflow.add_node("parse_diff", parse_diff_node)
workflow.add_node("logic_review", make_reviewer_node(IssueType.LOGIC))
workflow.add_node("security_review", make_reviewer_node(IssueType.SECURITY))
workflow.add_node("performance_review", make_reviewer_node(IssueType.PERFORMANCE))
workflow.add_node("readability_review", make_reviewer_node(IssueType.READABILITY))
workflow.add_node("supervisor", supervisor_node)

# Define edges
workflow.set_entry_point("fetch_context")
workflow.add_edge("fetch_context", "parse_diff")

# Parallel reviews
workflow.add_edge("parse_diff", "logic_review")
workflow.add_edge("parse_diff", "security_review")
workflow.add_edge("parse_diff", "performance_review")
workflow.add_edge("parse_diff", "readability_review")

# Fan-in to supervisor
workflow.add_edge("logic_review", "supervisor")
workflow.add_edge("security_review", "supervisor")
workflow.add_edge("performance_review", "supervisor")
workflow.add_edge("readability_review", "supervisor")

workflow.add_edge("supervisor", END)

app = workflow.compile()
