import re
from typing import List
from pr_agent.models.diff import PullRequestDiff, FileDiff, Hunk

class DiffParser:
    @staticmethod
    def parse(diff_content: str) -> PullRequestDiff:
        files = []
        current_file = None
        current_hunk = None
        
        lines = diff_content.splitlines()
        
        for line in lines:
            if line.startswith('diff --git'):
                if current_file:
                    if current_hunk:
                        current_file.hunks.append(current_hunk)
                    files.append(current_file)
                    current_hunk = None
                
                # Start new file
                parts = line.split(' ')
                path = parts[-1][2:] # remove b/
                current_file = FileDiff(path=path)
                
            elif line.startswith('--- a/'):
                if current_file:
                    current_file.old_path = line[6:]
            elif line.startswith('+++ b/'):
                pass # Already got path from diff --git
            elif line.startswith('@@'):
                if current_file and current_hunk:
                    current_file.hunks.append(current_hunk)
                
                # Parse hunk header
                # @@ -1,5 +1,5 @@
                match = re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)', line)
                if match:
                    old_start = int(match.group(1))
                    old_lines = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_lines = int(match.group(4)) if match.group(4) else 1
                    header = match.group(0)
                    
                    current_hunk = Hunk(
                        old_start=old_start,
                        old_lines=old_lines,
                        new_start=new_start,
                        new_lines=new_lines,
                        header=header,
                        content="",
                        lines=[]
                    )
            elif current_hunk:
                current_hunk.content += line + "\n"
                current_hunk.lines.append(line)
                
        if current_file:
            if current_hunk:
                current_file.hunks.append(current_hunk)
            files.append(current_file)
            
        return PullRequestDiff(files=files)
