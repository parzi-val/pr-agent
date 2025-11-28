import sys
import os

# Add src to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
from pr_agent.services.github_api import GitHubClient

load_dotenv()

def test_inline_comment():
    # Configuration
    repo_name = "parzi-val/pr-agent-sandbox"
    pr_number = 1
    
    print(f"Fetching diff for {repo_name} PR #{pr_number}...")
    client = GitHubClient()
    diff_content = client.get_pr_diff(repo_name, pr_number)
    
    # Simple parsing to find a valid file and line
    # We look for "diff --git a/filename b/filename" and then "@@ -x,y +line,z @@"
    import re
    file_match = re.search(r"diff --git a/(.*?) b/(.*)", diff_content)
    if not file_match:
        print("Could not find any file in diff.")
        return
        
    file_path = file_match.group(2) # Use the 'b' path (new file)
    
    # Find the first hunk
    hunk_match = re.search(r"@@ -\d+,\d+ \+(\d+),", diff_content)
    if not hunk_match:
        print("Could not find any hunk in diff.")
        return
        
    # The line number in the hunk header is the start of the hunk in the new file.
    # We can comment on that line.
    line_number = int(hunk_match.group(1)) + 1 # +1 to be safe inside the hunk? Or just the start.
    
    comment_body = "Test inline comment from PR Agent manual test script (Dynamic Line)."

    print(f"Testing inline comment on {repo_name} PR #{pr_number}...")
    print(f"File: {file_path}, Line: {line_number}")

    try:
        # client is already initialized
        # We need to pass a commit_id, but the method calculates it internally if we look at the code?
        # Let's check the signature in github_api.py
        # def post_inline_comment(self, repo_name: str, pr_number: int, commit_id: str, path: str, line: int, body: str):
        # Wait, the method signature requires commit_id.
        # But the implementation I saw earlier:
        # pr.create_review_comment(..., commit_id=pr.get_commits().reversed[0], ...)
        # It seems the implementation IGNORES the passed commit_id and fetches it? 
        # Or did I misread?
        # Let's re-read the file content from memory or check it.
        # In step 60 view_file output:
        # def post_inline_comment(self, repo_name: str, pr_number: int, commit_id: str, path: str, line: int, body: str):
        #     pr = self.get_pr(repo_name, pr_number)
        #     ...
        #     pr.create_review_comment(
        #         body=body,
        #         commit_id=pr.get_commits().reversed[0], 
        #         path=path,
        #         line=line,
        #         side="RIGHT"
        #     )
        # Yes, it ignores the passed commit_id argument and uses the latest one.
        # So we can pass anything for commit_id.
        
        client.post_inline_comment(
            repo_name=repo_name,
            pr_number=pr_number,
            commit_id="ignored", 
            path=file_path,
            line=line_number,
            body=comment_body
        )
        print("Successfully posted inline comment.")

    except Exception as e:
        print(f"Failed to post inline comment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_inline_comment()
