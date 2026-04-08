from typing import List, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pr_agent.core.llm import get_llm
from pr_agent.models.issues import CodeIssue, IssueType

class ReviewerAgent:
    def __init__(self):
        self.llm = get_llm()

    def review(self, diff: Any, context: str) -> List[CodeIssue]:
        from pydantic import BaseModel
        from pr_agent.models.diff import PullRequestDiff
        
        # Ensure diff is a PullRequestDiff object
        if not isinstance(diff, PullRequestDiff):
            print("Warning: ReviewerAgent received non-structured diff")
            return []

        class IssueList(BaseModel):
            issues: List[CodeIssue]
            
        list_parser = PydanticOutputParser(pydantic_object=IssueList)
        
        all_issues = []
        
        # Batch all file diffs into a single prompt for better cross-file context
        all_diffs_str = ""
        # Files to skip to reduce noise and save tokens
        EXCLUDED_FILES = {'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock', 'go.sum'}
        
        for file_diff in diff.files:
            if file_diff.is_deleted or any(file_diff.path.endswith(ext) for ext in EXCLUDED_FILES):
                continue
            
            # Simple heuristic: skip files with massive hunks (e.g., generated files)
            file_content = ""
            for hunk in file_diff.hunks:
                file_content += f"{hunk.header}\n"
                for i, line in enumerate(hunk.lines):
                    line_num = hunk.new_start + i
                    file_content += f"{line_num}: {line}\n"
            
            if len(file_content) > 50000: # Skip extremely large files in diff
                all_diffs_str += f"\n--- File: {file_diff.path} (Large file diff skipped) ---\n"
                continue
                
            all_diffs_str += f"\n--- File: {file_diff.path} ---\n" + file_content
        
        prompt = ChatPromptTemplate.from_template(
            """You are an expert multi-disciplinary code reviewer.
            Your task is to review the following changes from a pull request across four key domains:
            
            1. LOGIC: Bugs, race conditions, edge cases, and API misuse.
            2. SECURITY: Vulnerabilities (XSS, SQLi), hardcoded secrets, and unsafe data handling.
            3. PERFORMANCE: N+1 queries, inefficient loops, and memory leaks.
            4. READABILITY: Naming clarity, function complexity, and helpful documentation.
            
            CRITICAL INSTRUCTION:
            The provided diff may contain changes to multiple files. Use this cross-file context to verify 
            if a check (e.g., zero-division or null check) is handled internally in one file before flagging 
            it as missing in another file that uses it.
            
            Specifically: If a function handles an edge case (like division by zero) internally, 
            do NOT flag the caller for not checking it unless it's a specific requirement for the caller.
            
            Instructions:
            - Identify issues across ALL four domains in a single pass.
            - Use the line numbers provided in the format 'LINE_NUMBER: LINE_CONTENT'.
            - For each issue, provide a concise "tldr" (max 12 words).
            
            Repository Context (Summary of existing code):
            {context}
            
            Combined PR Diff (The new changes):
            {file_diff}
            
            Output the discovered issues in JSON format.
            {format_instructions}
            """
        )
        
        chain = prompt | self.llm | list_parser
        
        try:
            result = chain.invoke({
                "context": context[:8000], # Increased context limit for Gemini
                "file_diff": all_diffs_str,
                "format_instructions": list_parser.get_format_instructions()
            })
            
            import uuid
            for issue in result.issues:
                if not issue.id:
                    issue.id = str(uuid.uuid4())[:12]
                all_issues.append(issue)
                
        except Exception as e:
            print(f"Error in batched review: {e}")
            
        return all_issues
                
        return all_issues
