import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from pr_agent.services.github_api import GitHubClient

def test_github_client():
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN not found in .env")
        return

    # Replace these with a real repo/PR to test
    # You can use a public repo for reading, but need permissions for commenting
    repo_name = "octocat/Spoon-Knife" 
    pr_number = 38569

    print(f"Testing GitHubClient with {repo_name} PR #{pr_number}...")
    
    try:
        client = GitHubClient(token=token)
        
        # 1. Test fetching PR
        pr = client.get_pr(repo_name, pr_number)
        print(f"Successfully fetched PR: {pr.title}")
        
        # 2. Test fetching Diff
        diff = client.get_pr_diff(repo_name, pr_number)
        print(f"Successfully fetched diff. Length: {len(diff)} characters")
        
        with open("diff_output.txt", "w", encoding="utf-8") as f:
            f.write(diff)
        print("Diff saved to diff_output.txt")
        
        print("First 200 chars of diff:")
        print(diff[:200])
        
        # 3. Test Posting Comment (Uncomment to test - requires write access)
        # print("Attempting to post a comment...")
        # # You need a valid file path and position/line from the diff
        # # This is tricky to guess without parsing the diff first to find a valid line.
        # # client.post_inline_comment(repo_name, pr_number, pr.head.sha, "README.md", 1, "Test comment from PR Agent")
        # print("Comment posting skipped (uncomment in script to test)")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_github_client()
