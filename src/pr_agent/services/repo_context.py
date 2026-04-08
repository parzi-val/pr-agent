import os
from gitingest import ingest

class RepoContextManager:
    @staticmethod
    def get_context(repo_url: str) -> str:
        """
        Fetches the repository context using gitingest.
        """
        try:
            # Clean URL: If it's a PR URL, strip the suffix to get the base repo context
            # https://github.com/owner/repo/pull/1 -> https://github.com/owner/repo
            clean_url = repo_url.split('/pull/')[0]
            
            # Only include known text-based source files to prevent encoding errors
            include = ["*.py", "*.md", "*.txt", "*.json", "*.js", "*.ts", "*.tsx", "*.css", "*.html", "*.yaml", "*.yml"]
            exclude = ["package-lock.json", "yarn.lock", "node_modules/*", ".next/*", ".git/*"]
            
            summary, tree, content = ingest(
                clean_url, 
                include_patterns=include,
                exclude_patterns=exclude,
                max_file_size=50000
            )
            return f"{summary}\n\nFile Tree:\n{tree}\n\nContent:\n{content}"
        except Exception as e:
            return f"Error fetching context: {str(e)}"
