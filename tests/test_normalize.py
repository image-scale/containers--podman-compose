"""Tests for data normalization utilities."""

import os
import unittest

from compose_flow.normalize import (
    as_dict,
    as_list,
    filter_empty,
    is_iterable,
    is_relative_path,
    normalize_ulimit,
    parse_short_mount,
    safe_float,
    safe_int,
    time_to_seconds,
    version_less_than,
    version_to_list,
)


class TestIsIterable(unittest.TestCase):
    """Test cases for is_iterable function."""

    def test_list_is_iterable(self):
        self.assertTrue(is_iterable([1, 2, 3]))

    def test_tuple_is_iterable(self):
        self.assertTrue(is_iterable((1, 2, 3)))

    def test_set_is_iterable(self):
        self.assertTrue(is_iterable({1, 2, 3}))

    def test_generator_is_iterable(self):
        self.assertTrue(is_iterable(x for x in range(3)))

    def test_string_not_iterable(self):
        """Strings should return False despite having __iter__."""
        self.assertFalse(is_iterable("hello"))

    def test_dict_not_iterable(self):
        """Dicts should return False despite having __iter__."""
        self.assertFalse(is_iterable({"key": "value"}))

    def test_int_not_iterable(self):
        self.assertFalse(is_iterable(42))

    def test_none_not_iterable(self):
        self.assertFalse(is_iterable(None))


class TestAsList(unittest.TestCase):
    """Test cases for as_list function."""

    def test_none_returns_empty_list(self):
        self.assertEqual(as_list(None), [])

    def test_dict_to_list(self):
        result = as_list({"key": "value", "flag": None})
        self.assertIn("key=value", result)
        self.assertIn("flag", result)

    def test_list_passed_through(self):
        input_list = ["a", "b", "c"]
        self.assertEqual(as_list(input_list), input_list)

    def test_string_to_list(self):
        self.assertEqual(as_list("single"), ["single"])

    def test_tuple_to_list(self):
        self.assertEqual(as_list(("a", "b")), ["a", "b"])

    def test_empty_dict(self):
        self.assertEqual(as_list({}), [])


class TestAsDict(unittest.TestCase):
    """Test cases for as_dict function."""

    def test_none_returns_empty_dict(self):
        self.assertEqual(as_dict(None), {})

    def test_dict_copied(self):
        input_dict = {"key": "value"}
        result = as_dict(input_dict)
        self.assertEqual(result, input_dict)
        self.assertIsNot(result, input_dict)

    def test_list_to_dict(self):
        result = as_dict(["key=value", "flag"])
        self.assertEqual(result, {"key": "value", "flag": None})

    def test_string_with_equals(self):
        result = as_dict("key=value")
        self.assertEqual(result, {"key": "value"})

    def test_string_without_equals(self):
        result = as_dict("flag")
        self.assertEqual(result, {"flag": None})

    def test_empty_string_in_list_ignored(self):
        result = as_dict(["key=val", "", "flag"])
        self.assertEqual(result, {"key": "val", "flag": None})

    def test_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            as_dict(123)  # type: ignore


class TestFilterEmpty(unittest.TestCase):
    """Test cases for filter_empty function."""

    def test_filters_empty_strings(self):
        self.assertEqual(filter_empty(["a", "", "b", ""]), ["a", "b"])

    def test_all_empty(self):
        self.assertEqual(filter_empty(["", "", ""]), [])

    def test_no_empty(self):
        self.assertEqual(filter_empty(["a", "b", "c"]), ["a", "b", "c"])


class TestNormalizeUlimit(unittest.TestCase):
    """Test cases for normalize_ulimit function."""

    def test_dict_soft_hard(self):
        result = normalize_ulimit({"soft": 1024, "hard": 2048})
        self.assertEqual(result, "1024:2048")

    def test_dict_soft_only(self):
        result = normalize_ulimit({"soft": 1024})
        self.assertEqual(result, "1024:1024")

    def test_dict_hard_only(self):
        result = normalize_ulimit({"hard": 2048})
        self.assertEqual(result, "2048:2048")

    def test_dict_missing_both_raises(self):
        with self.assertRaises(ValueError):
            normalize_ulimit({"other": 1024})

    def test_int_passthrough(self):
        result = normalize_ulimit(1024)
        self.assertEqual(result, "1024")

    def test_string_passthrough(self):
        result = normalize_ulimit("unlimited")
        self.assertEqual(result, "unlimited")


class TestTimeToSeconds(unittest.TestCase):
    """Test cases for time_to_seconds function."""

    def test_none_returns_none(self):
        self.assertIsNone(time_to_seconds(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(time_to_seconds(""))

    def test_int_passthrough(self):
        self.assertEqual(time_to_seconds(30), 30)

    def test_float_truncated(self):
        self.assertEqual(time_to_seconds(30.5), 30)

    def test_seconds_only(self):
        self.assertEqual(time_to_seconds("30s"), 30)
        self.assertEqual(time_to_seconds("30"), 30)

    def test_minutes_only(self):
        self.assertEqual(time_to_seconds("3m"), 180)

    def test_minutes_seconds(self):
        self.assertEqual(time_to_seconds("1m30s"), 90)

    def test_colon_format(self):
        self.assertEqual(time_to_seconds("1:30"), 90)

    def test_fractional_seconds(self):
        # Fractional seconds are truncated to int
        self.assertEqual(time_to_seconds("30.5s"), 30)

    def test_invalid_returns_none(self):
        self.assertIsNone(time_to_seconds("invalid"))


class TestVersionComparison(unittest.TestCase):
    """Test cases for version comparison functions."""

    def test_version_to_list(self):
        result = version_to_list("1.2.3")
        self.assertEqual(result, [1, '.', 2, '.', 3])

    def test_version_to_list_empty(self):
        self.assertEqual(version_to_list(""), [])
        self.assertEqual(version_to_list(None), [])  # type: ignore

    def test_version_less_than(self):
        self.assertTrue(version_less_than("1.0.0", "2.0.0"))
        self.assertTrue(version_less_than("1.2.3", "1.2.4"))
        self.assertTrue(version_less_than("1.2.3", "1.3.0"))
        self.assertTrue(version_less_than("4.5.0", "4.6.0"))

    def test_version_not_less(self):
        self.assertFalse(version_less_than("2.0.0", "1.0.0"))
        self.assertFalse(version_less_than("1.2.3", "1.2.3"))

    def test_version_with_none(self):
        self.assertTrue(version_less_than(None, "1.0.0"))  # type: ignore
        self.assertFalse(version_less_than("1.0.0", None))  # type: ignore


class TestSafeConversions(unittest.TestCase):
    """Test cases for safe_int and safe_float functions."""

    def test_safe_int_valid(self):
        self.assertEqual(safe_int(42), 42)
        self.assertEqual(safe_int("42"), 42)

    def test_safe_int_invalid(self):
        self.assertIsNone(safe_int("not a number"))
        self.assertIsNone(safe_int(None))

    def test_safe_int_fallback(self):
        self.assertEqual(safe_int("bad", 0), 0)

    def test_safe_float_valid(self):
        self.assertEqual(safe_float(3.14), 3.14)
        self.assertEqual(safe_float("3.14"), 3.14)

    def test_safe_float_invalid(self):
        self.assertIsNone(safe_float("not a number"))

    def test_safe_float_fallback(self):
        self.assertEqual(safe_float("bad", 0.0), 0.0)


class TestParseShortMount(unittest.TestCase):
    """Test cases for parse_short_mount function."""

    def test_anonymous_volume(self):
        result = parse_short_mount("/var/lib/data")
        self.assertEqual(result["type"], "volume")
        self.assertIsNone(result["source"])
        self.assertEqual(result["target"], "/var/lib/data")

    def test_named_volume(self):
        result = parse_short_mount("mydata:/var/lib/data")
        self.assertEqual(result["type"], "volume")
        self.assertEqual(result["source"], "mydata")
        self.assertEqual(result["target"], "/var/lib/data")

    def test_bind_mount_absolute(self):
        result = parse_short_mount("/host/path:/container/path", "/base")
        self.assertEqual(result["type"], "bind")
        self.assertEqual(result["source"], "/host/path")
        self.assertEqual(result["target"], "/container/path")

    def test_bind_mount_relative(self):
        result = parse_short_mount("./data:/app/data", "/home/user/project")
        self.assertEqual(result["type"], "bind")
        self.assertEqual(result["target"], "/app/data")
        # Source should be resolved to absolute path
        self.assertTrue(os.path.isabs(result["source"]))

    def test_bind_mount_home(self):
        result = parse_short_mount("~/configs:/etc/configs", "/base")
        self.assertEqual(result["type"], "bind")
        self.assertEqual(result["target"], "/etc/configs")
        # Source should be expanded and absolute
        self.assertTrue(os.path.isabs(result["source"]))
        self.assertNotIn("~", result["source"])

    def test_readonly_option(self):
        result = parse_short_mount("/host:/container:ro")
        self.assertTrue(result["read_only"])

    def test_readwrite_option(self):
        result = parse_short_mount("/host:/container:rw")
        self.assertFalse(result["read_only"])

    def test_consistency_option(self):
        result = parse_short_mount("/host:/container:cached")
        self.assertEqual(result["consistency"], "cached")

    def test_propagation_option(self):
        result = parse_short_mount("/host:/container:z")
        self.assertEqual(result["bind"]["propagation"], "z")

    def test_multiple_options(self):
        result = parse_short_mount("/host:/container:ro,z")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["bind"]["propagation"], "z")

    def test_invalid_option_raises(self):
        with self.assertRaises(ValueError):
            parse_short_mount("/host:/container:invalid_option")

    def test_too_many_colons_raises(self):
        with self.assertRaises(ValueError):
            parse_short_mount("a:b:c:d")


class TestIsRelativePath(unittest.TestCase):
    """Test cases for is_relative_path function."""

    def test_dot_slash(self):
        self.assertTrue(is_relative_path("./path"))

    def test_dotdot_slash(self):
        self.assertTrue(is_relative_path("../path"))

    def test_dot_colon(self):
        self.assertTrue(is_relative_path(".:options"))

    def test_dotdot_colon(self):
        self.assertTrue(is_relative_path("..:options"))

    def test_absolute_path(self):
        self.assertFalse(is_relative_path("/absolute/path"))

    def test_named_volume(self):
        self.assertFalse(is_relative_path("volume_name"))


if __name__ == '__main__':
    unittest.main()
