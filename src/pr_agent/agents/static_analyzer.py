import re
from typing import List, Any
from pr_agent.models.issues import CodeIssue, IssueType, Severity
from pr_agent.models.diff import PullRequestDiff
import uuid

class StaticAnalyzerAgent:
    def __init__(self):
        # Define patterns [regex, issue_type, severity, description, suggestion, tldr]
        self.rules = [
            {
                "id": "sec-001",
                "pattern": r"(?:key|token|secret|password|passwd|auth)\s*[:=]\s*[\"']([a-zA-Z0-9_\-\.]{10,})[\"']",
                "type": IssueType.SECURITY,
                "severity": Severity.CRITICAL,
                "tldr": "Hard-coded secret detected.",
                "description": "A potential API key, token, or secret was found hard-coded in the source code.",
                "suggestion": "Move secrets to environment variables or a secure vault. Do not commit sensitive credentials to version control."
            },
            {
                "id": "sec-002",
                "pattern": r"pickle\.loads\(|yaml\.load\(|jsonpickle\.decode\(",
                "type": IssueType.SECURITY,
                "severity": Severity.HIGH,
                "tldr": "Unsafe deserialization detected.",
                "description": "Use of unsafe deserialization methods (like pickle.loads or yaml.load without a SafeLoader) can lead to arbitrary code execution.",
                "suggestion": "Use safe alternatives like json.loads, yaml.safe_load, or ensure input is from a trusted source."
            },
            {
                "id": "sec-003",
                "pattern": r"\.execute\(.*f[\"'].*\{.*\}[\"']|\.execute\(.*[\"'].*%s[\"']\s*%\s*\(.*\)",
                "type": IssueType.SECURITY,
                "severity": Severity.CRITICAL,
                "tldr": "Potential SQL injection vulnerability.",
                "description": "Detected string formatting or f-strings being used directly inside a database execution call.",
                "suggestion": "Use parameterized queries (e.g., cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))) to prevent SQL injection."
            },
            {
                "id": "sec-004",
                "pattern": r"verify\s*=\s*(?:False|0|None)",
                "type": IssueType.SECURITY,
                "severity": Severity.MEDIUM,
                "tldr": "Insecure TLS verification disabled.",
                "description": "SSL/TLS certificate verification is disabled (verify=False), making the request vulnerable to man-in-the-middle attacks.",
                "suggestion": "Enable certificate verification (verify=True) or provide a valid CA bundle path."
            }
        ]

    def analyze(self, diff: Any) -> List[CodeIssue]:
        if not isinstance(diff, PullRequestDiff):
            return []

        findings = []
        
        for file_diff in diff.files:
            if file_diff.is_deleted:
                continue
                
            for hunk in file_diff.hunks:
                # We analyze each line of the hunk
                # Note: This is a simple line-by-line analyzer for the demo
                for i, line in enumerate(hunk.lines):
                    # Only check added or modified lines (starting with +)
                    if not line.startswith('+'):
                        continue
                        
                    content = line[1:].strip() # Remove the + and whitespace
                    
                    for rule in self.rules:
                        if re.search(rule["pattern"], content, re.IGNORECASE):
                            findings.append(CodeIssue(
                                id=str(uuid.uuid4())[:8],
                                file_path=file_diff.path,
                                # Note: Calculating exact line number is complex in this simple parser,
                                # we'll use the hunk start as a baseline for now.
                                line_number=hunk.new_start + i, 
                                issue_type=rule["type"],
                                severity=rule["severity"],
                                tldr=rule["tldr"],
                                description=rule["description"],
                                suggestion=rule["suggestion"]
                            ))
                            
        return findings
