import unittest
from unittest.mock import MagicMock, patch
from pr_agent.models.issues import CodeIssue, IssueType, Severity

# Mocking the LLM to avoid API calls during test
with patch('pr_agent.agents.reviewer.get_llm') as mock_get_llm:
    mock_llm_instance = MagicMock()
    mock_get_llm.return_value = mock_llm_instance
    
    # Mock the chain invoke response
    # We need to mock the chain construction in ReviewerAgent.review
    # This is a bit complex to mock due to the pipe operator.
    # Instead, let's mock ReviewerAgent.review directly.
    pass

from pr_agent.agents.reviewer import ReviewerAgent
from pr_agent.agents.supervisor import SupervisorAgent

class TestWorkflow(unittest.TestCase):
    @patch.object(ReviewerAgent, 'review')
    def test_supervisor_merge(self, mock_review):
        # Setup mock return values
        issue1 = CodeIssue(
            file_path="test.py", line_number=10, issue_type=IssueType.LOGIC,
            severity=Severity.MEDIUM, description="Bug", suggestion="Fix it"
        )
        issue2 = CodeIssue(
            file_path="test.py", line_number=10, issue_type=IssueType.LOGIC,
            severity=Severity.LOW, description="Bug", suggestion="Fix it"
        )
        
        # Test Supervisor merge logic
        merged = SupervisorAgent.merge_issues([issue1, issue2])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].file_path, "test.py")

if __name__ == '__main__':
    unittest.main()
