from typing import List, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pr_agent.core.llm import get_llm
from pr_agent.models.issues import CodeIssue, IssueType

class ReviewerAgent:
    def __init__(self, role: IssueType):
        self.role = role
        self.llm = get_llm()
        self.parser = PydanticOutputParser(pydantic_object=CodeIssue)

    def review(self, diff: Any, context: str) -> List[CodeIssue]:
        from pydantic import BaseModel
        from pr_agent.models.diff import PullRequestDiff
        
        # Ensure diff is a PullRequestDiff object
        if not isinstance(diff, PullRequestDiff):
            # Fallback or error? For now, assume it's passed correctly or handle raw string if needed (but we want structured)
            # If it's a string, we might need to parse it here or assume caller did.
            # The plan says caller (graph node) parses it.
            print("Warning: ReviewerAgent received non-structured diff")
            return []

        class IssueList(BaseModel):
            issues: List[CodeIssue]
            
        list_parser = PydanticOutputParser(pydantic_object=IssueList)
        
        all_issues = []
        
        # We can review file by file to avoid context window limits and give better focus
        for file_diff in diff.files:
            if file_diff.is_deleted:
                continue
                
            # Construct a file-specific context/prompt
            # We serialize the file diff to a string for the prompt
            file_diff_str = f"File: {file_diff.path}\n"
            for hunk in file_diff.hunks:
                file_diff_str += f"{hunk.header}\n{hunk.content}\n"
            
            # Custom prompts per role
            role_prompts = {
                IssueType.LOGIC: """
                    Focus on:
                    - Bugs, race conditions, logical errors.
                    - Incorrect handling of edge cases.
                    - API misuse.
                    
                    Do NOT flag:
                    - Style issues (indentation, whitespace).
                    - Minor performance optimizations unless critical.
                """,
                IssueType.SECURITY: """
                    Focus on:
                    - Vulnerabilities (XSS, SQLi, RCE).
                    - Hardcoded secrets/credentials.
                    - Unsafe data handling.
                    
                    Do NOT flag:
                    - Using external trusted domains (like github.com) unless clearly unsafe.
                    - General best practices unless there's a tangible risk.
                """,
                IssueType.PERFORMANCE: """
                    Focus on:
                    - N+1 queries, O(n^2) loops on large data.
                    - Memory leaks.
                    - Extremely inefficient operations.
                    
                    Do NOT flag:
                    - Minor micro-optimizations.
                    - Using standard image formats (GIF/PNG) unless they are massive.
                """,
                IssueType.READABILITY: """
                    Focus on:
                    - Code clarity and understandability.
                    - Variable and function naming (are they descriptive?).
                    - Function length and complexity (is it too complex?).
                    - Comments and documentation (are they helpful?).
                    
                    Do NOT flag:
                    - Minor indentation or whitespace issues (unless they severely hurt readability).
                    - Personal stylistic preferences.
                """
            }
            
            specific_instructions = role_prompts.get(self.role, "")
            
            prompt = ChatPromptTemplate.from_template(
                """You are an expert code reviewer focusing on {role}.
                
                {specific_instructions}
                
                Review the following file diff from a pull request.
                Identify any {role} issues.
                
                For each issue, provide:
                - A "tldr": A very short summary (10-12 words max).
                - A description, suggestion, severity, etc.
                
                Repository Context (Summary):
                {context}
                
                File Diff:
                {file_diff}
                
                Output the issues in JSON format.
                {format_instructions}
                """
            )
            
            chain = prompt | self.llm | list_parser
            
            try:
                result = chain.invoke({
                    "role": self.role.value,
                    "specific_instructions": specific_instructions,
                    "context": context[:5000], 
                    "file_diff": file_diff_str,
                    "format_instructions": list_parser.get_format_instructions()
                })
                
                # Ensure returned issues have the correct file path and an ID
                import uuid
                for issue in result.issues:
                    if not issue.file_path:
                        issue.file_path = file_diff.path
                    if not issue.id:
                        issue.id = str(uuid.uuid4())[:8] # Short ID
                    all_issues.append(issue)
                    
            except Exception as e:
                print(f"Error in {self.role} review for {file_diff.path}: {e}")
                
        return all_issues
