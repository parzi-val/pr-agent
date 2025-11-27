from typing import List, Optional
from pydantic import BaseModel

class Hunk(BaseModel):
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    header: str
    content: str  # The actual diff content for this hunk
    lines: List[str] # Individual lines

class FileDiff(BaseModel):
    path: str
    old_path: Optional[str] = None
    is_binary: bool = False
    is_deleted: bool = False
    is_new: bool = False
    hunks: List[Hunk] = []

class PullRequestDiff(BaseModel):
    files: List[FileDiff]
