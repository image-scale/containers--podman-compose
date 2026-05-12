"""Tests for variable interpolation functionality."""

import unittest
from typing import Union

from compose_flow.interpolation import interpolate


class TestInterpolation(unittest.TestCase):
    """Test cases for bash-style variable interpolation."""

    def test_simple_substitution(self):
        """Test basic $VAR substitution."""
        result = interpolate("Hello $NAME!", {"NAME": "Alice"})
        self.assertEqual(result, "Hello Alice!")

    def test_braced_substitution(self):
        """Test ${VAR} substitution."""
        result = interpolate("Hello ${NAME}", {"NAME": "Alice"})
        self.assertEqual(result, "Hello Alice")

    def test_unset_variable_empty(self):
        """Test that unset variables become empty string."""
        result = interpolate("Hello ${NAME}", {})
        self.assertEqual(result, "Hello ")

    def test_default_if_unset_colon_dash(self):
        """Test ${VAR:-default} when unset."""
        result = interpolate("User: ${USER:-guest}", {})
        self.assertEqual(result, "User: guest")

    def test_default_if_empty_colon_dash(self):
        """Test ${VAR:-default} when empty."""
        result = interpolate("User: ${USER:-guest}", {"USER": ""})
        self.assertEqual(result, "User: guest")

    def test_default_if_unset_dash_only(self):
        """Test ${VAR-default} when unset."""
        result = interpolate("User: ${USER-guest}", {})
        self.assertEqual(result, "User: guest")

    def test_empty_not_default_dash_only(self):
        """Test ${VAR-default} when empty - should NOT use default."""
        result = interpolate("User: ${USER-guest}", {"USER": ""})
        self.assertEqual(result, "User: ")

    def test_required_nonempty_success(self):
        """Test ${VAR:?error} when set and nonempty."""
        result = interpolate("Path: ${TEST_PATH:?required}", {"TEST_PATH": "/bin"})
        self.assertEqual(result, "Path: /bin")

    def test_required_nonempty_fails_unset(self):
        """Test ${VAR:?error} raises when unset."""
        with self.assertRaises(ValueError) as ctx:
            interpolate("Path: ${TEST_PATH:?TEST_PATH required}", {})
        self.assertIn("required variable TEST_PATH is missing a value", str(ctx.exception))

    def test_required_nonempty_fails_empty(self):
        """Test ${VAR:?error} raises when empty."""
        with self.assertRaises(ValueError) as ctx:
            interpolate("Path: ${TEST_PATH:?TEST_PATH required}", {"TEST_PATH": ""})
        self.assertIn("required variable TEST_PATH is missing a value", str(ctx.exception))

    def test_required_set_success(self):
        """Test ${VAR?error} when set."""
        result = interpolate("Config: ${CFG?missing}", {"CFG": "cfg.yaml"})
        self.assertEqual(result, "Config: cfg.yaml")

    def test_required_set_fails_unset(self):
        """Test ${VAR?error} raises when unset."""
        with self.assertRaises(ValueError) as ctx:
            interpolate("Config: ${CFG?missing}", {})
        self.assertIn("required variable CFG is missing a value", str(ctx.exception))

    def test_required_set_passes_empty(self):
        """Test ${VAR?error} passes when set to empty string."""
        result = interpolate("Config: ${CFG?missing}", {"CFG": ""})
        self.assertEqual(result, "Config: ")

    def test_alternative_if_nonempty_yes(self):
        """Test ${VAR:+alt} when set and nonempty."""
        result = interpolate("Alt: ${MODE:+active}", {"MODE": "1"})
        self.assertEqual(result, "Alt: active")

    def test_alternative_if_set_empty(self):
        """Test ${VAR+alt} when set but empty."""
        result = interpolate("Alt: ${MODE+active}", {"MODE": ""})
        self.assertEqual(result, "Alt: active")

    def test_alternative_if_unset(self):
        """Test ${VAR+alt} when unset."""
        result = interpolate("Alt: ${MODE+active}", {})
        self.assertEqual(result, "Alt: ")

    def test_multiple_variables(self):
        """Test multiple variable substitutions."""
        result = interpolate("${GREETING:-Hi}, ${NAME:-stranger}!", {})
        self.assertEqual(result, "Hi, stranger!")

    def test_default_with_spaces(self):
        """Test default values containing spaces."""
        result = interpolate("${USER:-default user}", {})
        self.assertEqual(result, "default user")

    def test_escaped_dollar(self):
        """Test that $$ becomes literal $."""
        result = interpolate("Price: $$${AMOUNT}", {"AMOUNT": "100"})
        self.assertEqual(result, "Price: $100")

    def test_empty_variable_value(self):
        """Test variable set to empty string."""
        result = interpolate("Value: ${VAR}", {"VAR": ""})
        self.assertEqual(result, "Value: ")

    def test_nested_default_inner(self):
        """Test nested ${OUTER:-${INNER:-default}} resolving to inner default."""
        result = interpolate("${OUTER:-${INNER:-default}}", {})
        self.assertEqual(result, "default")

    def test_nested_default_inner_value(self):
        """Test nested ${OUTER:-${INNER:-default}} using inner variable."""
        result = interpolate("${OUTER:-${INNER:-default}}", {"INNER": "inner_value"})
        self.assertEqual(result, "inner_value")

    def test_nested_default_outer_value(self):
        """Test nested ${OUTER:-${INNER:-default}} using outer variable."""
        result = interpolate(
            "${OUTER:-${INNER:-default}}",
            {"OUTER": "outer_value", "INNER": "inner_value"}
        )
        self.assertEqual(result, "outer_value")

    def test_triple_nested_fallback(self):
        """Test triple nested defaults."""
        result = interpolate("${A:-${B:-${C:-final}}}", {})
        self.assertEqual(result, "final")

    def test_triple_nested_middle(self):
        """Test triple nested using middle value."""
        result = interpolate("${A:-${B:-${C:-final}}}", {"B": "mid"})
        self.assertEqual(result, "mid")

    def test_triple_nested_top(self):
        """Test triple nested using top value."""
        result = interpolate("${A:-${B:-${C:-final}}}", {"A": "top"})
        self.assertEqual(result, "top")

    def test_invalid_var_name_digit(self):
        """Test that variable names starting with digits are rejected."""
        with self.assertRaises(ValueError) as ctx:
            interpolate("${1INVALID}", {})
        self.assertIn("Invalid interpolation format", str(ctx.exception))

    def test_invalid_var_name_dash(self):
        """Test that variable names starting with dash are rejected."""
        with self.assertRaises(ValueError) as ctx:
            interpolate("${-INVALID}", {})
        self.assertIn("Invalid interpolation format", str(ctx.exception))

    def test_invalid_empty_braces(self):
        """Test that empty ${} is rejected."""
        with self.assertRaises(ValueError) as ctx:
            interpolate("${}", {})
        self.assertIn("Invalid interpolation format", str(ctx.exception))

    def test_dollar_not_followed_by_var(self):
        """Test that $5 (dollar not followed by valid name) is treated as literal."""
        result = interpolate("Price is $5", {})
        self.assertEqual(result, "Price is $5")

    def test_dollar_at_end(self):
        """Test dollar sign at end of string."""
        result = interpolate("end$", {})
        self.assertEqual(result, "end$")

    def test_unbraced_var_with_text(self):
        """Test unbraced variable followed by more text."""
        result = interpolate("$NAME_VALUE", {"NAME_VALUE": "test"})
        self.assertEqual(result, "test")

    def test_no_variable_refs(self):
        """Test string with no variable references."""
        result = interpolate("plain text", {})
        self.assertEqual(result, "plain text")


if __name__ == '__main__':
    unittest.main()
