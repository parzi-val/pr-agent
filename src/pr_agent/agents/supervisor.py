from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pr_agent.core.llm import get_llm
from pr_agent.models.issues import CodeIssue

class SupervisorAgent:
    def __init__(self):
        self.llm = get_llm()

    def merge_issues(self, issues: List[CodeIssue] | dict) -> List[CodeIssue]:
        if isinstance(issues, dict):
            issues = issues.get("issues", [])
            
        if not issues:
            return []
            
        from pydantic import BaseModel
        from pr_agent.models.issues import CodeIssue
        import json
        
        class IssueList(BaseModel):
            issues: List[CodeIssue]

        parser = PydanticOutputParser(pydantic_object=IssueList)

        # We pass all issues to a single prompt that performs deduplication,
        # grouping, and merging in one step.
        prompt = ChatPromptTemplate.from_template(
            """You are the SupervisorAgent.
            You are given a list of code review issues identified across different focus areas (Logic, Security, etc.).
            
            Your task:
            1. Identify duplicate or highly related issues that refer to the same underlying problem.
            2. Merge these related issues into a single, high-quality "master" issue.
            3. For unique issues, keep them as is.
            4. Ensure the final list is concise, non-redundant, and professionally formatted.
            
            Input Issues:
            {issues_json}
            
            Instructions for Merging:
            - Combine suggestions to be comprehensive.
            - Pick the highest severity found in the group.
            - Write a clear description and a short "tldr" (max 12 words).
            
            Output the final deduplicated list of issues in JSON format.
            {format_instructions}
            """
        )
        
        chain = prompt | self.llm | parser
        
        try:
            # Flatten the issues and prepare for the prompt
            raw_issues = []
            for issue in issues:
                raw_issues.append({
                    "id": issue.id,
                    "file": f"{issue.file_path}:{issue.line_number}",
                    "type": issue.issue_type.value if hasattr(issue.issue_type, 'value') else issue.issue_type,
                    "severity": issue.severity.value if hasattr(issue.severity, 'value') else issue.severity,
                    "tldr": issue.tldr,
                    "description": issue.description,
                    "suggestion": issue.suggestion
                })

            result = chain.invoke({
                "issues_json": json.dumps(raw_issues, indent=2),
                "format_instructions": parser.get_format_instructions()
            })
            
            # Re-attach original IDs or maintain continuity if needed
            return result.issues
            
        except Exception as e:
            print(f"Error in batched supervisor merge: {e}")
            # Fallback: return unique issues by TLDR as a simple heuristic
            seen_tldrs = set()
            unique_issues = []
            for issue in issues:
                if issue.tldr not in seen_tldrs:
                    unique_issues.append(issue)
                    seen_tldrs.add(issue.tldr)
            return unique_issues
