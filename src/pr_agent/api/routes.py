from fastapi import APIRouter, HTTPException, BackgroundTasks
from pr_agent.api.models import ReviewRequest, ReviewResponse
from pr_agent.agents.graph import app as workflow_app
from pr_agent.services.github_api import GitHubClient
from pr_agent.services.repo_context import RepoContextManager

router = APIRouter()

@router.post("/review", response_model=ReviewResponse)
async def trigger_review(request: ReviewRequest):
    try:
        # 1. Fetch PR Diff
        # We need to initialize GitHubClient. 
        # If token is passed in request, use it, else env var.
        gh_client = GitHubClient(token=request.github_token)
        
        # Parse repo name from URL or assume it's passed? 
        # The request has repo_url, e.g., https://github.com/owner/repo
        # We need to extract owner/repo
        parts = request.repo_url.rstrip('/').split('/')
        repo_name = f"{parts[-2]}/{parts[-1]}"
        
        diff_content = gh_client.get_pr_diff(repo_name, request.pr_number)
        
        # 2. Fetch Repo Context
        # We can use the repo_url directly with gitingest
        repo_context = RepoContextManager.get_context(request.repo_url)
        
        # 3. Run Workflow
        initial_state = {
            "pr_diff": diff_content,
            "repo_context": repo_context,
            "issues": []
        }
        
        result = workflow_app.invoke(initial_state)
        
        return ReviewResponse(issues=result["issues"], status="completed")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
