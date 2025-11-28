from fastapi import APIRouter, HTTPException, BackgroundTasks
from pr_agent.api.models import ReviewRequest, ReviewResponse
from pr_agent.agents.graph import app as workflow_app
from pr_agent.services.github_api import GitHubClient
from pr_agent.services.repo_context import RepoContextManager
import re

router = APIRouter()

import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from pydantic import BaseModel

class CommentRequest(BaseModel):
    repo_url: str
    pr_number: int
    file_path: str
    line_number: int
    body: str
    github_token: str = None

@router.post("/comment")
async def post_comment(request: CommentRequest):
    try:
        logger.info(f"Received comment request for {request.repo_url} PR #{request.pr_number}")
        
        gh_client = GitHubClient(token=request.github_token)
        
        parts = re.search(r"github\.com\/([^\/]+\/[^\/]+)\/pull\/(\d+)", request.repo_url)
        if not parts:
             # Fallback if user passes just repo name? For now assume URL.
             # Or maybe the frontend passes repo_name directly?
             # The frontend currently passes the full URL.
             # Let's support both or just extract from URL as before.
             if "github.com" in request.repo_url:
                 repo_name = parts.group(1)
             else:
                 repo_name = request.repo_url # Assume it's owner/repo
        else:
            repo_name = parts.group(1)
            
        # pr_number is passed explicitly
        
        gh_client.post_inline_comment(
            repo_name=repo_name,
            pr_number=request.pr_number,
            commit_id="latest",
            path=request.file_path,
            line=request.line_number,
            body=request.body
        )
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error posting comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review", response_model=ReviewResponse)
async def trigger_review(request: ReviewRequest):
    try:
        logger.info(f"Received review request for URL: {request.repo_url}")
        
        # 1. Fetch PR Diff
        # We need to initialize GitHubClient. 
        # If token is passed in request, use it, else env var.
        gh_client = GitHubClient(token=request.github_token)
        
        # Parse repo name from URL or assume it's passed? 
        # The request has repo_url, e.g., https://github.com/owner/repo
        # We need to extract owner/repo
        
        parts = re.search(r"github\.com\/([^\/]+\/[^\/]+)\/pull\/(\d+)", request.repo_url)
        if not parts:
            raise ValueError(f"Could not parse URL: {request.repo_url}")
            
        repo_name = parts.group(1)
        pr_number = int(parts.group(2)) # Ensure int
        
        logger.info(f"Extracted repo_name: {repo_name}, pr_number: {pr_number}")
        
        diff_content = gh_client.get_pr_diff(repo_name, pr_number)
        logger.info(f"Fetched diff content (length: {len(diff_content)})")
        
        
        # 2. Fetch Repo Context - Moved to Graph
        # repo_context = RepoContextManager.get_context(request.repo_url)
        
        # 3. Run Workflow
        initial_state = {
            "repo_url": request.repo_url,
            "pr_number": request.pr_number,
            "github_token": request.github_token,
            "pr_diff": diff_content,
            # repo_context will be fetched by the graph's fetch_context_node
            "issues": []
        }
        
        logger.info("Invoking workflow...")
        result = workflow_app.invoke(initial_state)
        logger.info("Workflow finished.")
        
        issues = result.get("final_issues") or result.get("issues")
        logger.info(f"Found {len(issues) if issues else 0} issues.")
        
        # Post issues to GitHub - DISABLED for manual mode
        # if issues:
        #     logger.info("Posting inline comments to GitHub...")
        #     for issue in issues:
        #         try:
        #             body = f"**[{issue.issue_type}]** {issue.tldr}\n\n{issue.description}\n\n**Suggestion:**\n{issue.suggestion}"
        #             gh_client.post_inline_comment(
        #                 repo_name=repo_name,
        #                 pr_number=pr_number,
        #                 commit_id="latest", # Ignored by implementation
        #                 path=issue.file_path,
        #                 line=issue.line_number,
        #                 body=body
        #             )
        #         except Exception as exc:
        #             logger.error(f"Failed to post comment for issue {issue.id}: {exc}")
        #     logger.info("Finished posting comments.")
        
        return ReviewResponse(issues=issues, status="completed")
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
