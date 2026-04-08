from typing import Dict, Any
from langgraph.graph import StateGraph, END
from pr_agent.core.state import AgentState
from pr_agent.agents.reviewer import ReviewerAgent
from pr_agent.agents.supervisor import SupervisorAgent
from pr_agent.agents.static_analyzer import StaticAnalyzerAgent
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

def reviewer_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing batched reviewer_node")
    agent = ReviewerAgent()
    issues = agent.review(state["pr_diff_structured"], state["repo_context"])
    logger.info(f"Batched reviewer found {len(issues)} issues across all categories.")
    return {"issues": issues}

def static_analysis_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing deterministic static_analysis_node")
    agent = StaticAnalyzerAgent()
    issues = agent.analyze(state["pr_diff_structured"])
    logger.info(f"Static analyzer found {len(issues)} deterministic issues.")
    return {"issues": issues}

def supervisor_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing batched supervisor_node")
    supervisor = SupervisorAgent()
    # The 'issues' in state will contain a combined list from both reviewer and static analyzer
    merged_issues = supervisor.merge_issues(state["issues"])
    logger.info(f"Supervisor merged issues into {len(merged_issues)} final issues.")
    return {"final_issues": merged_issues}

# Build graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("fetch_context", fetch_context_node)
workflow.add_node("parse_diff", parse_diff_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_node("static_analysis", static_analysis_node)
workflow.add_node("supervisor", supervisor_node)

# Define edges
workflow.set_entry_point("fetch_context")
workflow.add_edge("fetch_context", "parse_diff")

# Run LLM review and Static Analysis in parallel
workflow.add_edge("parse_diff", "reviewer")
workflow.add_edge("parse_diff", "static_analysis")

# Fan-in to supervisor
workflow.add_edge("reviewer", "supervisor")
workflow.add_edge("static_analysis", "supervisor")

workflow.add_edge("supervisor", END)

app = workflow.compile()
