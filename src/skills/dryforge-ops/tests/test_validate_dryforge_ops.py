import importlib.util
import unittest
from pathlib import Path

VALIDATOR = Path(__file__).resolve().parents[1] / "scripts" / "validate_dryforge_ops.py"

spec = importlib.util.spec_from_file_location("validate_dryforge_ops", VALIDATOR)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ValidateDryforgeOpsTests(unittest.TestCase):
    def test_current_skill_validates(self):
        skill_dir = Path(__file__).resolve().parents[1]
        self.assertEqual(module.validate_skill(skill_dir), [])

    def test_frontmatter_requires_name_and_description(self):
        data = module.parse_frontmatter('---\nname: dryforge-ops\ndescription: "x"\n---\n# Body\n')
        self.assertEqual(data["name"], "dryforge-ops")
        self.assertEqual(data["description"], "x")


if __name__ == "__main__":
    unittest.main()
