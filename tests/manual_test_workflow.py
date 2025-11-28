import os
import sys
import asyncio
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from pr_agent.agents.graph import app as workflow_app

async def test_workflow():
    load_dotenv()
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found in .env")
        return
        
    if not os.getenv("GITHUB_TOKEN"):
        print("Error: GITHUB_TOKEN not found in .env")
        return

    # Test parameters
    repo_url = "https://github.com/agno-agi/agno"
    pr_number = 5546 # Using the PR we verified earlier
    
    print(f"Starting workflow for {repo_url} PR #{pr_number}...")
    
    # We need to fetch the diff first to pass it to the state, 
    # OR we can rely on the graph to fetch it if we modify the graph/nodes.
    # Currently, the graph expects 'pr_diff' in the initial state.
    # So we need to fetch it using GitHubClient here.
    
    from pr_agent.services.github_api import GitHubClient
    client = GitHubClient()
    repo_name = "agno-agi/agno"
    
    print("Fetching PR diff...")
    diff_content = client.get_pr_diff(repo_name, pr_number)
    
    initial_state = {
        "repo_url": repo_url,
        "pr_number": pr_number,
        "github_token": os.getenv("GITHUB_TOKEN"),
        "pr_diff": diff_content,
        # repo_context will be fetched by the graph's fetch_context_node
        "issues": []
    }
    
    print("Invoking workflow...")
    try:
        result = await workflow_app.ainvoke(initial_state)
        
        print("\nWorkflow completed!")
        issues = result.get('final_issues') or result.get('issues')
        print(f"Total issues found: {len(issues)}")
        
        for issue in issues:
            print(f"\n[{issue.issue_type}] {issue.file_path}:{issue.line_number}")
            print(f"Severity: {issue.severity}")
            print(f"Description: {issue.description}")
            print(f"Suggestion: {issue.suggestion}")
            
    except Exception as e:
        print(f"Workflow failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow())
