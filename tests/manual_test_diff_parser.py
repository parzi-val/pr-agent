import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from pr_agent.services.diff_parser import DiffParser

def test_diff_parser_real():
    diff_path = os.path.join(os.path.dirname(__file__), '../partials/diff_output.txt')
    
    if not os.path.exists(diff_path):
        print(f"Error: {diff_path} not found. Run manual_test_github.py first.")
        return

    print(f"Reading diff from {diff_path}...")
    with open(diff_path, "r", encoding="utf-8") as f:
        diff_content = f.read()

    print("Parsing diff...")
    try:
        parsed_diff = DiffParser.parse(diff_content)
        
        print(f"Successfully parsed {len(parsed_diff.files)} files.")
        
        for file in parsed_diff.files:
            print(f"\nFile: {file.path}")
            print(f"  Old Path: {file.old_path}")
            print(f"  Hunks: {len(file.hunks)}")
            for i, hunk in enumerate(file.hunks):
                print(f"    Hunk {i+1}: Old {hunk.old_start} (+{hunk.old_lines}) -> New {hunk.new_start} (+{hunk.new_lines})")
                print(f"    Header: {hunk.header.strip()}")
                print(f"    Content:\n{hunk.content}") # Uncomment to see full content
                
    except Exception as e:
        print(f"Error parsing diff: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_diff_parser_real()
