"""Tests for recursive substitution and merge functions."""

import unittest
from typing import Any

from compose_flow.merge import (
    clone,
    recursive_merge,
    recursive_merge_one,
    recursive_substitute,
)


class TestClone(unittest.TestCase):
    """Test cases for clone function."""

    def test_clone_dict(self):
        original = {"key": "value"}
        cloned = clone(original)
        self.assertEqual(cloned, original)
        self.assertIsNot(cloned, original)

    def test_clone_list(self):
        original = [1, 2, 3]
        cloned = clone(original)
        self.assertEqual(cloned, original)
        self.assertIsNot(cloned, original)

    def test_clone_string(self):
        original = "test"
        cloned = clone(original)
        self.assertEqual(cloned, original)
        self.assertIs(cloned, original)  # Strings are immutable, same reference OK

    def test_clone_int(self):
        original = 42
        cloned = clone(original)
        self.assertEqual(cloned, original)


class TestRecursiveSubstitute(unittest.TestCase):
    """Test cases for recursive_substitute function."""

    def test_substitute_string(self):
        result = recursive_substitute("Hello $NAME", {"NAME": "World"})
        self.assertEqual(result, "Hello World")

    def test_substitute_in_list(self):
        result = recursive_substitute(["$VAR1", "$VAR2"], {"VAR1": "a", "VAR2": "b"})
        self.assertEqual(result, ["a", "b"])

    def test_substitute_in_dict_values(self):
        result = recursive_substitute(
            {"key": "$VALUE"},
            {"VALUE": "result"}
        )
        self.assertEqual(result, {"key": "result"})

    def test_substitute_in_dict_keys(self):
        result = recursive_substitute(
            {"$KEY": "value"},
            {"KEY": "actual_key"}
        )
        self.assertEqual(result, {"actual_key": "value"})

    def test_service_environment_priority(self):
        """Service env variables should have lower priority than global env."""
        input_data = {
            "environment": {
                "v1": "low priority",
                "actual-v1": "$v1"
            }
        }
        result = recursive_substitute(input_data, {"v1": "high priority"})
        self.assertEqual(result["environment"]["actual-v1"], "high priority")

    def test_service_environment_can_reference_itself(self):
        """Service env variables can reference each other."""
        input_data = {
            "environment": {
                "v100": "v1.0.0",
                "image": "abc:$v100"
            }
        }
        result = recursive_substitute(input_data, {})
        self.assertEqual(result["environment"]["image"], "abc:v1.0.0")

    def test_escaped_dollar(self):
        """$$ should become literal $."""
        input_data = {
            "environment": {
                "non_var": "$$v1",
                "vx": "$non_var"
            },
            "image": "abc:$non_var"
        }
        result = recursive_substitute(input_data, {})
        self.assertEqual(result["environment"]["non_var"], "$v1")
        self.assertEqual(result["environment"]["vx"], "$v1")
        self.assertEqual(result["image"], "abc:$v1")

    def test_nested_dict(self):
        """Test deeply nested structures."""
        input_data = {
            "level1": {
                "level2": {
                    "value": "$VAR"
                }
            }
        }
        result = recursive_substitute(input_data, {"VAR": "deep"})
        self.assertEqual(result["level1"]["level2"]["value"], "deep")

    def test_non_string_passthrough(self):
        """Non-string values should pass through unchanged."""
        input_data = {
            "number": 42,
            "boolean": True,
            "null": None
        }
        result = recursive_substitute(input_data, {})
        self.assertEqual(result["number"], 42)
        self.assertEqual(result["boolean"], True)
        self.assertIsNone(result["null"])


class TestRecursiveMerge(unittest.TestCase):
    """Test cases for recursive merge functions."""

    def test_merge_adds_new_keys(self):
        target = {"a": 1}
        source = {"b": 2}
        result = recursive_merge_one(target, source)
        self.assertEqual(result, {"a": 1, "b": 2})

    def test_merge_replaces_values(self):
        target = {"a": 1}
        source = {"a": 2}
        result = recursive_merge_one(target, source)
        self.assertEqual(result, {"a": 2})

    def test_merge_nested_dicts(self):
        target = {"outer": {"a": 1}}
        source = {"outer": {"b": 2}}
        result = recursive_merge_one(target, source)
        self.assertEqual(result, {"outer": {"a": 1, "b": 2}})

    def test_merge_appends_lists(self):
        target = {"items": [1, 2]}
        source = {"items": [3, 4]}
        result = recursive_merge_one(target, source)
        self.assertEqual(result, {"items": [1, 2, 3, 4]})

    def test_merge_command_replaces(self):
        """command should be replaced, not appended."""
        target = {"command": ["original", "cmd"]}
        source = {"command": ["new", "cmd"]}
        result = recursive_merge_one(target, source)
        self.assertEqual(result, {"command": ["new", "cmd"]})

    def test_merge_entrypoint_replaces(self):
        """entrypoint should be replaced, not appended."""
        target = {"entrypoint": "/bin/sh"}
        source = {"entrypoint": "/bin/bash"}
        result = recursive_merge_one(target, source)
        self.assertEqual(result, {"entrypoint": "/bin/bash"})

    def test_merge_volumes_removes_duplicates(self):
        """Volumes with same target should be replaced."""
        target = {"volumes": ["./old:/mnt", "/etc/config:/config"]}
        source = {"volumes": ["./new:/mnt"]}
        result = recursive_merge_one(target, source)
        # ./old:/mnt should be replaced by ./new:/mnt
        self.assertIn("./new:/mnt", result["volumes"])
        self.assertNotIn("./old:/mnt", result["volumes"])
        # /etc/config:/config should be kept
        self.assertIn("/etc/config:/config", result["volumes"])

    def test_merge_none_to_dict(self):
        """Can merge dicts into None values."""
        target = {"config": None}
        source = {"config": {"key": "value"}}
        result = recursive_merge_one(target, source)
        self.assertEqual(result, {"config": {"key": "value"}})

    def test_merge_multiple_sources(self):
        target = {"a": 1}
        source1 = {"b": 2}
        source2 = {"c": 3}
        result = recursive_merge(target, source1, source2)
        self.assertEqual(result, {"a": 1, "b": 2, "c": 3})

    def test_merge_type_mismatch_raises(self):
        """Merging incompatible types should raise."""
        target = {"key": "string"}
        source = {"key": {"nested": "dict"}}
        with self.assertRaises(ValueError):
            recursive_merge_one(target, source)

    def test_merge_preserves_target_only_keys(self):
        target = {"keep_me": "value", "shared": "target"}
        source = {"shared": "source"}
        result = recursive_merge_one(target, source)
        self.assertEqual(result["keep_me"], "value")
        self.assertEqual(result["shared"], "source")


class TestIntegration(unittest.TestCase):
    """Integration tests combining substitution and merge."""

    def test_substitute_in_nested_service(self):
        """Test variable substitution in a realistic service structure."""
        env = {"VERSION": "1.0", "DB_HOST": "localhost"}
        service = {
            "image": "myapp:$VERSION",
            "environment": {
                "DATABASE_URL": "postgres://$DB_HOST:5432/db"
            },
            "labels": {
                "version": "$VERSION"
            }
        }
        result = recursive_substitute(service, env)
        self.assertEqual(result["image"], "myapp:1.0")
        self.assertEqual(
            result["environment"]["DATABASE_URL"],
            "postgres://localhost:5432/db"
        )
        self.assertEqual(result["labels"]["version"], "1.0")


if __name__ == '__main__':
    unittest.main()
