# Acceptance Criteria

## Task 1: Implement variable interpolation for compose files

### Acceptance Criteria
- [x] Simple variable substitution: "$NAME" with {"NAME": "Alice"} returns "Hello Alice"
- [x] Braced variable substitution: "${NAME}" works the same as "$NAME"
- [x] Unset variable returns empty string: "${NAME}" with {} returns ""
- [x] Default if unset or empty (:-): "${USER:-guest}" with {} or {"USER": ""} returns "guest"
- [x] Default only if unset (-): "${USER-guest}" with {"USER": ""} returns "" (not default)
- [x] Required nonempty (:?): "${PATH:?error}" raises ValueError when PATH is unset or empty
- [x] Required set (?): "${PATH?error}" raises ValueError only when PATH is unset
- [x] Alternative if nonempty (:+): "${MODE:+active}" returns "active" only when MODE is nonempty
- [x] Alternative if set (+): "${MODE+active}" returns "active" when MODE is set (even if empty)
- [x] Escaped dollar: "$$" becomes literal "$"
- [x] Nested variables: "${OUTER:-${INNER:-default}}" resolves correctly
- [x] Invalid variable names (starting with digit) raise ValueError
- [x] Dollar not followed by valid var name treated as literal: "$5" remains "$5"

## Task 2: Implement data normalization utilities

### Acceptance Criteria
- [ ] is_iterable: returns True for lists and iterables, False for strings and dicts
- [ ] as_list: convert dict {k: v} to list ["k=v"], convert string to list, pass through list
- [ ] as_dict: convert list ["k=v", "k2"] to dict {"k": "v", "k2": None}, handle string input
- [ ] normalize_ulimit: parse soft/hard limits from dict {"soft": x, "hard": y} to "x:y" format
- [ ] time_to_seconds: parse "3m", "30s", "1m30s", "90" to integer seconds
- [ ] version_compare: compare version strings like "4.5.0" vs "4.6.0" correctly
- [ ] parse_short_mount: parse short volume syntax "/host:/container:opts" to mount dict
