import os
from gitingest import ingest

class RepoContextManager:
    @staticmethod
    def get_context(repo_url: str) -> str:
        """
        Fetches the repository context using gitingest.
        """
        try:
            summary, tree, content = ingest(repo_url)
            return f"{summary}\n\nFile Tree:\n{tree}\n\nContent:\n{content}"
        except Exception as e:
            return f"Error fetching context: {str(e)}"
