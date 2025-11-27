import unittest
from pr_agent.services.diff_parser import DiffParser

class TestDiffParser(unittest.TestCase):
    def test_parse_simple_diff(self):
        diff = """diff --git a/file.py b/file.py
index 123..456 100644
--- a/file.py
+++ b/file.py
@@ -1,2 +1,3 @@
 line1
-line2
+line2_modified
+line3
"""
        parsed = DiffParser.parse(diff)
        self.assertEqual(len(parsed.files), 1)
        self.assertEqual(parsed.files[0].path, "file.py")
        self.assertEqual(len(parsed.files[0].hunks), 1)
        self.assertEqual(parsed.files[0].hunks[0].old_start, 1)
        self.assertEqual(parsed.files[0].hunks[0].new_start, 1)
        self.assertEqual(len(parsed.files[0].hunks[0].lines), 4)

if __name__ == '__main__':
    unittest.main()
