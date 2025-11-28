import os
from typing import List, Optional
from github import Github, Auth
from github.PullRequest import PullRequest
from github.Repository import Repository

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        self.auth = Auth.Token(self.token)
        self.g = Github(auth=self.auth)

    def get_pr(self, repo_name: str, pr_number: int) -> PullRequest:
        repo = self.g.get_repo(repo_name)
        return repo.get_pull(pr_number)

    def get_pr_diff(self, repo_name: str, pr_number: int) -> str:
        pr = self.get_pr(repo_name, pr_number)
        # Using requests to get the raw diff content if needed, 
        # but PyGithub exposes files. 
        # For unified diff string, we might need to fetch the diff_url content.
        import requests
        headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3.diff"}
        response = requests.get(pr.diff_url, headers=headers)
        response.raise_for_status()
        return response.text

    def post_inline_comment(self, repo_name: str, pr_number: int, commit_id: str, path: str, line: int, body: str):
        pr = self.get_pr(repo_name, pr_number)

        pr.create_review_comment(
            body=body,
            commit=pr.get_commits().reversed[0], 
            path=path,
            line=line,
            side="RIGHT"
        )
