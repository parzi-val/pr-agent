from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pr_agent.core.llm import get_llm
from pr_agent.models.issues import CodeIssue, IssueType

class ReviewerAgent:
    def __init__(self, role: IssueType):
        self.role = role
        self.llm = get_llm()
        self.parser = PydanticOutputParser(pydantic_object=CodeIssue)

    def review(self, diff: str, context: str) -> List[CodeIssue]:
        from pydantic import BaseModel
        class IssueList(BaseModel):
            issues: List[CodeIssue]
            
        list_parser = PydanticOutputParser(pydantic_object=IssueList)
        
        prompt = ChatPromptTemplate.from_template(
            """You are an expert code reviewer focusing on {role}.
            
            Review the following pull request diff and repository context.
            Identify any {role} issues.
            
            Repository Context:
            {context}
            
            Diff:
            {diff}
            
            Output the issues in JSON format.
            {format_instructions}
            """
        )
        
        chain = prompt | self.llm | list_parser
        
        try:
            result = chain.invoke({
                "role": self.role.value,
                "context": context[:10000], # Truncate context to avoid token limits if necessary
                "diff": diff[:10000],
                "format_instructions": list_parser.get_format_instructions()
            })
            return result.issues
        except Exception as e:
            print(f"Error in {self.role} review: {e}")
            return []
