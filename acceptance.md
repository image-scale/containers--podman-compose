# Acceptance Criteria

## Task 1: Implement variable interpolation for compose files

### Acceptance Criteria
- [ ] Simple variable substitution: "$NAME" with {"NAME": "Alice"} returns "Hello Alice"
- [ ] Braced variable substitution: "${NAME}" works the same as "$NAME"
- [ ] Unset variable returns empty string: "${NAME}" with {} returns ""
- [ ] Default if unset or empty (:-): "${USER:-guest}" with {} or {"USER": ""} returns "guest"
- [ ] Default only if unset (-): "${USER-guest}" with {"USER": ""} returns "" (not default)
- [ ] Required nonempty (:?): "${PATH:?error}" raises ValueError when PATH is unset or empty
- [ ] Required set (?): "${PATH?error}" raises ValueError only when PATH is unset
- [ ] Alternative if nonempty (:+): "${MODE:+active}" returns "active" only when MODE is nonempty
- [ ] Alternative if set (+): "${MODE+active}" returns "active" when MODE is set (even if empty)
- [ ] Escaped dollar: "$$" becomes literal "$"
- [ ] Nested variables: "${OUTER:-${INNER:-default}}" resolves correctly
- [ ] Invalid variable names (starting with digit) raise ValueError
- [ ] Dollar not followed by valid var name treated as literal: "$5" remains "$5"
