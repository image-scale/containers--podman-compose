"""
Variable interpolation for compose file values.

Supports bash-style variable substitution:
- $VARIABLE or ${VARIABLE} - basic substitution
- ${VARIABLE:-default} - use default if unset or empty
- ${VARIABLE-default} - use default only if unset
- ${VARIABLE:?error} - error if unset or empty
- ${VARIABLE?error} - error only if unset
- ${VARIABLE:+alternative} - use alternative if set and nonempty
- ${VARIABLE+alternative} - use alternative if set (even if empty)
- $$ - literal dollar sign
"""

from __future__ import annotations

import string
from dataclasses import dataclass
from enum import Enum
from typing import Any


class InterpolationOperator(Enum):
    """Supported variable interpolation operators."""
    DEFAULT_IF_EMPTY = ':-'
    DEFAULT_IF_UNSET = '-'
    ERROR_IF_EMPTY = ':?'
    ERROR_IF_UNSET = '?'
    ALT_IF_NONEMPTY = ':+'
    ALT_IF_SET = '+'


# Characters valid for variable names
VAR_NAME_CHARS = string.ascii_letters + string.digits + '_'
VAR_NAME_START_CHARS = string.ascii_letters + '_'


@dataclass
class LiteralSegment:
    """A segment of literal text."""
    text: str

    def evaluate(self, env: dict[str, str | None]) -> str:
        return self.text


@dataclass
class VariableSegment:
    """A variable reference segment."""
    name: str
    operator: str | None = None
    operand: str | None = None

    def evaluate(self, env: dict[str, str | None]) -> str:
        value = env.get(self.name)

        # Simple substitution - no operator
        if self.operator is None or self.operand is None:
            return value if value is not None else ''

        # Error if empty/unset operators
        if self.operator == InterpolationOperator.ERROR_IF_EMPTY.value:
            if value is None or value == '':
                resolved_msg = interpolate(self.operand, env) if self.operand else ''
                raise ValueError(
                    f"required variable {self.name} is missing a value: {resolved_msg}"
                )
            return value

        if self.operator == InterpolationOperator.ERROR_IF_UNSET.value:
            if value is None:
                resolved_msg = interpolate(self.operand, env) if self.operand else ''
                raise ValueError(
                    f"required variable {self.name} is missing a value: {resolved_msg}"
                )
            return value

        # Default value operators
        if self.operator == InterpolationOperator.DEFAULT_IF_EMPTY.value:
            # Use default if unset OR empty
            if value is None or value == '':
                return interpolate(self.operand, env)
            return value

        if self.operator == InterpolationOperator.DEFAULT_IF_UNSET.value:
            # Use default only if unset (not if empty)
            if value is None:
                return interpolate(self.operand, env)
            return value

        # Alternative operators
        if self.operator == InterpolationOperator.ALT_IF_NONEMPTY.value:
            # Use alternative if set AND nonempty
            if value is not None and value != '':
                return interpolate(self.operand, env)
            return ''

        if self.operator == InterpolationOperator.ALT_IF_SET.value:
            # Use alternative if set (even if empty)
            if value is not None:
                return interpolate(self.operand, env)
            return ''

        raise ValueError(f"Unknown operator in variable interpolation: {self.operator}")


def _scan_var_name(text: str, start: int) -> tuple[int, str]:
    """Scan forward to extract a variable name, return (end_pos, name)."""
    pos = start
    name = ''
    while pos < len(text) and text[pos] in VAR_NAME_CHARS:
        name += text[pos]
        pos += 1
    return pos, name


def _find_closing_brace(text: str, start: int) -> int:
    """Find the matching closing brace, handling nested braces."""
    depth = 1
    pos = start
    while pos < len(text):
        if text[pos] == '}':
            depth -= 1
            if depth == 0:
                return pos
        elif text[pos] == '{':
            depth += 1
        pos += 1
    raise ValueError("No closing brace found for variable interpolation")


def _parse_brace_content(content: str) -> VariableSegment:
    """Parse the content inside ${...} and return a VariableSegment."""
    if not content or content[0] not in VAR_NAME_START_CHARS:
        raise ValueError(
            f"Invalid interpolation format: ${{{content}}}."
            " You may need to escape any $ with another $"
        )

    # Extract variable name
    pos, name = _scan_var_name(content, 0)

    # Check for operator
    remaining = content[pos:]
    if not remaining:
        return VariableSegment(name=name)

    # Find which operator matches
    operators = [op.value for op in InterpolationOperator]
    for op in operators:
        if remaining.startswith(op):
            operand = remaining[len(op):]
            return VariableSegment(name=name, operator=op, operand=operand)

    raise ValueError(f"Invalid variable interpolation syntax: ${{{content}}}")


def _tokenize(value: str) -> list[LiteralSegment | VariableSegment]:
    """Parse a string into segments of literals and variable references."""
    segments: list[LiteralSegment | VariableSegment] = []

    def append_literal(char: str) -> None:
        if segments and isinstance(segments[-1], LiteralSegment):
            segments[-1].text += char
        else:
            segments.append(LiteralSegment(text=char))

    pos = 0
    while pos < len(value):
        char = value[pos]

        if char == '$':
            # Check what follows
            if pos + 1 >= len(value):
                # $ at end of string - treat as literal
                append_literal(char)
                pos += 1
                continue

            next_char = value[pos + 1]

            if next_char == '$':
                # Escaped dollar - literal $
                append_literal('$')
                pos += 2
                continue

            if next_char == '{':
                # Braced variable ${...}
                close_pos = _find_closing_brace(value, pos + 2)
                content = value[pos + 2:close_pos]
                segments.append(_parse_brace_content(content))
                pos = close_pos + 1
                continue

            if next_char in VAR_NAME_START_CHARS:
                # Unbraced variable $NAME
                end_pos, name = _scan_var_name(value, pos + 1)
                segments.append(VariableSegment(name=name))
                pos = end_pos
                continue

            # $ not followed by valid var start - treat as literal
            append_literal(char)
            pos += 1
            continue

        # Regular character
        append_literal(char)
        pos += 1

    return segments


def interpolate(value: str, env: dict[str, Any]) -> str:
    """
    Perform bash-style variable interpolation on a string.

    Args:
        value: The string containing variable references
        env: Dictionary mapping variable names to their values

    Returns:
        The interpolated string

    Raises:
        ValueError: For invalid syntax or required variables that are missing
    """
    segments = _tokenize(value)
    parts = [seg.evaluate(env) for seg in segments]
    return ''.join(parts)
