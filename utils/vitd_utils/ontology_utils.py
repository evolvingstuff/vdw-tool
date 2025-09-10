#!/usr/bin/env python3
"""
Shared utilities for ontology parsing and processing
"""

import re
import sys
from typing import List, Tuple, Optional, Dict, Set, Any
import time


class ParseError(Exception):
    """Custom exception for parsing errors"""

    def __init__(self, message: str, position: int, remaining_text: str):
        self.message = message
        self.position = position
        self.remaining_text = remaining_text
        super().__init__(f"{message} at position {position}: '{remaining_text[:50]}...'")


class RegexParser:
    """Regex-based parser for ontology statements"""

    def __init__(self):
        # Define regex patterns in order of matching priority
        self.patterns = {
            'whitespace': re.compile(r'\s+'),
            'comment': re.compile(r'/\*[\s\S]*?\*/'),  # Use [\s\S] instead of . with DOTALL for better compatibility
            'context_start': re.compile(r'\('),
            'context_stop': re.compile(r'\)'),
            'op_imp': re.compile(r'=>'),
            'op_assoc': re.compile(r'~'),
            'op_eq': re.compile(r'='),
            'negated_text': re.compile(r'-"([^"\\]|\\.)*"'),
            'negated_regex': re.compile(r'-/([^/\\]|\\.)+/[gimsuyx]*'),
            'text': re.compile(r'"([^"\\]|\\.)*"'),
            'regex': re.compile(r'/([^/\\]|\\.)+/[gimsuyx]*'),
            'tag': re.compile(r'#[a-zA-Z_][a-zA-Z0-9_-]*'),
            'meta_tag': re.compile(r'@[a-zA-Z_][a-zA-Z0-9_-]*'),
        }

        # Track parsing state
        self.reset_state()

    def reset_state(self):
        """Reset parser state for new statement"""
        self.tokens = []
        self.position = 0
        self.original_text = ""
        self.encountered_operator = False
        self.last_token_type = None
        self.left_side = True  # True if we're on left side of first operator

    def consume_whitespace_and_comments(self, text: str, pos: int) -> int:
        """Consume whitespace and comments, return new position"""
        while pos < len(text):
            # Try whitespace
            match = self.patterns['whitespace'].match(text, pos)
            if match:
                pos = match.end()
                continue

            # Try comment
            match = self.patterns['comment'].match(text, pos)
            if match:
                pos = match.end()
                continue

            # No more whitespace/comments
            break

        return pos

    def try_match_pattern(self, pattern_name: str, text: str, pos: int) -> Optional[Tuple[str, int]]:
        """Try to match a pattern at given position, return (match_text, new_pos) or None"""
        pattern = self.patterns[pattern_name]
        match = pattern.match(text, pos)
        if match:
            return (match.group(0), match.end())
        return None

    def validate_token_placement(self, token_type: str, token_text: str) -> None:
        """Validate that token is allowed in current context"""
        # Check for starting with operator
        if token_type in ['op_imp', 'op_assoc', 'op_eq'] and len(self.tokens) == 0:
            raise ParseError(f"Statement cannot start with operator '{token_text}'",
                             self.position, self.original_text[self.position:])

        # Text and regex (including negated) only allowed on left side of implications
        if token_type in ['text', 'regex', 'negated_text', 'negated_regex']:
            if not self.left_side:
                raise ParseError(f"Text/regex '{token_text}' not allowed on right side",
                                 self.position, self.original_text[self.position:])

        # Context grouping checks
        if token_type in ['context_start', 'context_stop']:
            # Not in a context, allow starting one with (
            if token_type == 'context_start':
                if self.encountered_operator:
                    raise ParseError(f"Context groups not allowed on right side",
                                     self.position, self.original_text[self.position:])

        # Operator can only appear once
        if token_type in ['op_imp', 'op_assoc', 'op_eq']:
            if self.encountered_operator:
                raise ParseError(f"Multiple operators not allowed in a statement",
                                 self.position, self.original_text[self.position:])
            self.encountered_operator = True
            self.left_side = False  # Switching to right side after operator

    def parse_statement(self, text: str) -> List[Tuple[str, str]]:
        """Parse a single ontology statement using regex consumption"""
        self.reset_state()
        self.original_text = text
        self.position = 0
        pos = 0

        # Skip leading whitespace and comments
        pos = self.consume_whitespace_and_comments(text, pos)
        if pos >= len(text):
            return self.tokens  # Return empty tokens for blank/comment-only lines

        # Main parsing loop
        while pos < len(text):
            matched = False
            self.position = pos  # Store for error reporting

            # Try each pattern in priority order
            for pattern_name in self.patterns.keys():
                match_result = self.try_match_pattern(pattern_name, text, pos)
                if match_result:
                    token_text, new_pos = match_result

                    # Validate token placement
                    self.validate_token_placement(pattern_name, token_text)

                    # Add token
                    self.tokens.append((pattern_name, token_text))
                    self.last_token_type = pattern_name
                    pos = new_pos
                    matched = True
                    break

            # Handle no pattern match
            if not matched:
                raise ParseError(f"Invalid syntax",
                                 self.position,
                                 text[self.position:])

            # Skip whitespace and comments
            pos = self.consume_whitespace_and_comments(text, pos)

        # Validate final state
        self.validate_final_state()
        return self.tokens

    def validate_final_state(self) -> None:
        """Validate the final parsing state"""
        # Must have at least one token
        if not self.tokens:
            return  # Allow empty lines

        # Check for unclosed context
        last_token_type = self.tokens[-1][0]
        if last_token_type == 'context_start':
            raise ParseError("Unclosed context group '('",
                             self.position, self.original_text[self.position:])

        # Must have operator and tokens on both sides
        operator_types = ['op_imp', 'op_assoc', 'op_eq']
        has_operator = any(token[0] in operator_types for token in self.tokens)

        # Find the operator position
        op_index = -1
        for i, (token_type, _) in enumerate(self.tokens):
            if token_type in operator_types:
                op_index = i
                break

        # Skip checks for comment-only lines
        if len(self.tokens) == 0:
            return

        if has_operator:
            # Must have tokens on the left side
            if op_index == 0:
                raise ParseError("Missing left side of operator",
                                 self.position, self.original_text[self.position:])

            # Must have tokens on the right side
            if op_index == len(self.tokens) - 1:
                raise ParseError("Missing right side of operator",
                                 self.position, self.original_text[self.position:])
        else:
            # No operator found in non-empty statement
            raise ParseError("Statement must contain an operator (=>, ~, or =)",
                             self.position, self.original_text[self.position:])


def construct_representation(tokens: List[Tuple[str, str]]) -> Tuple[List, str, List]:
    """Convert tokens to representation format, handling contexts"""
    op = None
    lhs = []
    rhs = []
    current_side = lhs

    context_group = []
    in_context = False

    for token_type, token_text in tokens:
        if token_type == 'context_start':
            in_context = True
            context_group = []
        elif token_type == 'context_stop':
            in_context = False
            if context_group:
                current_side.append(('context_group', context_group))
        elif token_type in ['op_imp', 'op_assoc', 'op_eq']:
            op = token_text
            current_side = rhs
        elif in_context:
            # Add to current context group
            if token_type == 'tag':
                context_group.append(('tag', token_text))
            elif token_type == 'text':
                context_group.append(('text', token_text))
            elif token_type == 'regex':
                context_group.append(('regex', token_text))
        else:
            # Add to current side
            if token_type == 'tag':
                current_side.append(('tag', token_text))
            elif token_type == 'meta_tag':
                current_side.append(('meta_tag', token_text))
            elif token_type == 'text':
                current_side.append(('text', token_text))
            elif token_type == 'regex':
                current_side.append(('regex', token_text))

    return (lhs, op, rhs)


def expand_representation(rep: Tuple[List, str, List]) -> List[Tuple[Tuple[str, str], str, Tuple[str, str]]]:
    """Expand representation into individual rules with Cartesian expansion"""
    lhs, op, rhs = rep
    expanded = []

    def expand(lhs, rhs, op):
        results = []

        # Special handling for multiple tags on left side with equality
        if op == '=' and len(lhs) > 1 and all(item[0] == 'tag' for item in lhs):
            # For equality between multiple tags, generate pairwise comparisons
            for i in range(len(lhs)):
                for j in range(i + 1, len(lhs)):
                    results.append((lhs[i], op, lhs[j]))
            return results

        # Multiple tags with => or ~ between LHS and RHS
        if len(lhs) > 1 and op in ['=>', '~'] and all(item[0] == 'tag' for item in lhs):
            # Each tag gets its own rule with the RHS
            for left_item in lhs:
                if len(rhs) == 1:  # Simple case, one RHS
                    results.append((left_item, op, rhs[0]))
                else:  # Multiple RHS, expand Cartesian
                    for right_item in rhs:
                        results.append((left_item, op, right_item))
            return results

        # Default case - full Cartesian product
        for left_item in lhs:
            for right_item in rhs:
                results.append((left_item, op, right_item))
        return results

    return expand(lhs, rhs, op)


def parse_ontology_file(file_path: str) -> List[Tuple[Any, str, Any]]:
    """Parse an ontology file and return the expanded rules"""
    import time
    start_time = time.time()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ontology_text = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Ontology file not found: {file_path}")

    # Preprocess to remove multi-line comments before line-by-line processing
    ontology_text = re.sub(r'/\*[\s\S]*?\*/', '', ontology_text)

    parser = RegexParser()

    # Split into lines and filter
    lines = ontology_text.split('\n')
    statements = []

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if line and not line.startswith('/*') and not (line.startswith('/*') and line.endswith('*/')):
            # Handle inline comments by removing them
            comment_start = line.find('/*')
            if comment_start != -1:
                comment_end = line.find('*/', comment_start)
                if comment_end != -1:
                    line = line[:comment_start] + line[comment_end + 2:]
                    line = line.strip()

            if line:  # If still has content after comment removal
                statements.append((line_num, line))

    parsing_time = time.time()
    print(f"File reading and preprocessing time: {(parsing_time - start_time):.4f} seconds")
    print(f"Found {len(statements)} statements in {file_path}")

    all_expanded_rules = []
    rules_processed = 0

    # Process all statements
    for line_num, statement in statements:
        try:
            tokens = parser.parse_statement(statement)
            rep = construct_representation(tokens)
            expanded = expand_representation(rep)
            all_expanded_rules.extend(expanded)
            rules_processed += 1
        except ParseError as e:
            print(f"Warning - Line {line_num}: Parse error in '{statement}': {e.message}")
        except Exception as e:
            print(f"Warning - Line {line_num}: Unexpected error in '{statement}': {e}")

    end_time = time.time()
    print(f"Rule expansion time: {(end_time - parsing_time):.4f} seconds")
    print(f"Total parsing time: {(end_time - start_time):.4f} seconds")
    print(f"Successfully processed {rules_processed}/{len(statements)} statements")
    print(f"Generated {len(all_expanded_rules)} expanded rules")

    return all_expanded_rules


def ontology_rules_to_engine_format(rules: List[Tuple[Any, str, Any]]) -> List[Tuple[Any, str, Any]]:
    """Convert parsed ontology rules to the format expected by OntologyEngine"""
    engine_rules = []

    for source, op, target in rules:
        engine_rules.append((source, op, target))

    return engine_rules