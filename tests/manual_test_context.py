import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from pr_agent.services.repo_context import RepoContextManager

def test_fetch_context():
    # Using a small public repo for testing
    repo_url = "https://github.com/octocat/Spoon-Knife"
    print(f"Fetching context for {repo_url}...")
    
    try:
        context = RepoContextManager.get_context(repo_url)
        
        output_file = "context_output.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(context)
            
        print(f"Context saved to {output_file}")
        print(f"Context length: {len(context)} characters")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fetch_context()
