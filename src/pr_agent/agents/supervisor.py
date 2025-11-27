from typing import List
from pr_agent.models.issues import CodeIssue

class SupervisorAgent:
    @staticmethod
    def merge_issues(issues: List[CodeIssue]) -> List[CodeIssue]:
        # Deduplicate based on file_path, line_number, and issue_type
        unique_issues = {}
        for issue in issues:
            key = (issue.file_path, issue.line_number, issue.issue_type)
            # We could also check for similar descriptions using fuzzy matching if needed
            if key not in unique_issues:
                unique_issues[key] = issue
            else:
                # Keep the one with higher severity or merge descriptions?
                # For now, simple first-come-first-serve or overwrite
                pass
                
        return list(unique_issues.values())
