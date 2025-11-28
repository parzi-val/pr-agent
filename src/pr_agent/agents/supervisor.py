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
            
        from pydantic import BaseModel, Field
        from langchain_core.output_parsers import JsonOutputParser
        import json
        
        # Pass 1: Pivot (Semantic Grouping by TLDR)
        # Prepare input: 2D array of [id, tldr]
        pivot_input = [[issue.id, issue.tldr] for issue in issues]
        
        # Define output structure for grouping
        class GroupingResult(BaseModel):
            groups: List[List[str]] = Field(description="List of groups, where each group is a list of issue IDs")

        grouping_parser = JsonOutputParser(pydantic_object=GroupingResult)

        pivot_prompt = ChatPromptTemplate.from_template(
            """You are the SupervisorAgent.
            You receive a list of issue summaries (TLDRs) with their IDs.
            
            Your task is to group these issues based on semantic similarity.
            - Issues describing the same underlying problem should be grouped together.
            - If an issue is unique, it should be in a group of its own.
            
            Input Data (ID, TLDR):
            {pivot_input}
            
            Output a JSON object with a "groups" key, containing lists of IDs.
            Example: {{ "groups": [ ["id1", "id3"], ["id2"] ] }}
            """
        )
        
        pivot_chain = pivot_prompt | self.llm | grouping_parser
        
        try:
            print("DEBUG: Running Supervisor Pass 1 (Pivot)...")
            grouped_data = pivot_chain.invoke({"pivot_input": str(pivot_input)})
            groups = grouped_data.get("groups", [])
            print(f"DEBUG: Pivot Result: {groups}")
            
            # For now, we stop here to test the pivot as requested.
            # We will return the original issues but maybe print the groups to verify.
            # The user said: "implement all of this but comment out the second pass, first we will test the pivot"
            
            # Rebuild: Create clubbed representations
            clubbed_issues = []
            issue_map = {issue.id: issue for issue in issues}
            
            for group in groups:
                if not group: continue
                
                # Pick "highest" issue (e.g., highest severity or first one)
                base_issue_id = group[0]
                base_issue = issue_map.get(base_issue_id)
                if not base_issue: continue
                
                # Collect details for the group
                group_details = []
                for issue_id in group:
                    issue = issue_map.get(issue_id)
                    if issue:
                        group_details.append({
                            "file": f"{issue.file_path}:{issue.line_number}",
                            "type": issue.issue_type,
                            "severity": issue.severity,
                            "description": issue.description,
                            "suggestion": issue.suggestion
                        })
                        
                clubbed_issues.append({
                    "base_issue": base_issue, # To keep original fields like file_path
                    "group_details": group_details
                })

            # Pass 2: Condense & Format
            final_issues = []
            
            condense_prompt = ChatPromptTemplate.from_template(
                """You are the SupervisorAgent.
                You are given a group of related code review issues that refer to the same underlying problem.
                
                Your task is to merge them into a single, high-quality code review issue.
                
                Group Details:
                {group_details}
                
                Instructions:
                1. Create a concise description that captures the core problem.
                2. Formulate a single, actionable suggestion.
                3. Determine the highest severity level from the group.
                4. Choose the most appropriate issue type.
                5. Provide a short "tldr" (10-12 words).
                
                Output the result as a JSON object matching the CodeIssue structure.
                {format_instructions}
                """
            )
            
            # We need a parser for CodeIssue
            from pr_agent.models.issues import CodeIssue
            condense_parser = PydanticOutputParser(pydantic_object=CodeIssue)
            condense_chain = condense_prompt | self.llm | condense_parser
            
            print(f"DEBUG: Condensing {len(clubbed_issues)} groups...")
            
            for clubbed in clubbed_issues:
                try:
                    group_details_str = json.dumps(clubbed["group_details"], indent=2, default=str)
                    
                    merged_issue = condense_chain.invoke({
                        "group_details": group_details_str,
                        "format_instructions": condense_parser.get_format_instructions()
                    })
                    
                    # Ensure critical fields are preserved/correct if LLM misses them
                    if not merged_issue.file_path:
                        merged_issue.file_path = clubbed["base_issue"].file_path
                    if not merged_issue.line_number:
                        merged_issue.line_number = clubbed["base_issue"].line_number
                    if not merged_issue.id:
                         merged_issue.id = clubbed["base_issue"].id
                        
                    final_issues.append(merged_issue)
                    
                except Exception as e:
                    print(f"Error condensing group: {e}")
                    # Fallback to base issue
                    final_issues.append(clubbed["base_issue"])
            
            return final_issues
            
        except Exception as e:
            print(f"Error in Supervisor Pass 1 (Pivot): {e}")
            return issues
