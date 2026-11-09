import unittest
import ast

from worker import fix_python_code

class FixPythonCodeTests(unittest.TestCase):
    def test_fix_python_code_reformats_common_style_issues(self):
        original = "def add(a,b):\n    return a+b\n"

        fixed = fix_python_code(original)

        self.assertIn("def add(a, b):", fixed)
        self.assertIn("return a+b", fixed)
        self.assertNotEqual(original, fixed)

    def test_fixes_missing_function_colon_and_formats_sample(self):
        original = (
            "import json\n"
            "import os\n"
            "\n"
            "def build_profile(name, email)\n"
            "  profile={\"name\":name,\"email\":email}\n"
            "  unused_token = \"temporary\"\n"
            "  print(\"Profile:\",profile)\n"
            "  return profile\n"
        )

        fixed = fix_python_code(original)

        self.assertIn("def build_profile(name, email):", fixed)
        self.assertIn('profile = {"name": name, "email": email}', fixed)
        self.assertIn('print("Profile:", profile)', fixed)
        self.assertNotIn("import json", fixed)
        self.assertNotIn("import os", fixed)
        self.assertNotIn("unused_token", fixed)

    def test_fixes_missing_commas(self):
        for original in ("values = [1 2]\n", "result = add(1 2)\n"):
            with self.subTest(original=original):
                fixed = fix_python_code(original)
                ast.parse(fixed)
                self.assertIn(",", fixed)

    def test_fixes_unclosed_delimiters(self):
        samples = {
            "result = add(1, 2\n": ")",
            "values = [1, 2\n": "]",
            'profile = {"name": "Ada"\n': "}",
        }
        for original, expected_closer in samples.items():
            with self.subTest(original=original):
                fixed = fix_python_code(original)
                ast.parse(fixed)
                self.assertTrue(fixed.rstrip().endswith(expected_closer))

    def test_fixes_unmatched_closer_in_simple_assignment(self):
        fixed = fix_python_code("values = data]\n")

        ast.parse(fixed)
        self.assertIn("values = [data]", fixed)

    def test_rejects_ambiguous_missing_bracket(self):
        with self.assertRaisesRegex(ValueError, "Could not safely auto-fix syntax error"):
            fix_python_code("values = 1, 2]\n")

    def test_separates_same_line_assignments(self):
        fixed = fix_python_code("first = 1 second = 2\n")

        parsed = ast.parse(fixed)
        self.assertEqual(len(parsed.body), 2)
        self.assertTrue(all(isinstance(statement, ast.Assign) for statement in parsed.body))

if __name__ == "__main__":
    unittest.main()