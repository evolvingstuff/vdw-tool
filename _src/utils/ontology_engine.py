#!/usr/bin/env python3
"""
Complete Ontology Engine Implementation
Handles implications, associations, equality, and text mapping with proper propagation
Ported from vitD project with FAIL FAST philosophy
"""

import re
from collections import defaultdict
from typing import Dict, Set, List, Tuple, Optional, Any
import json
import time


class ImplicationIndex:
    """Manages implication hierarchy with transitive closure"""

    def __init__(self):
        # Forward: what does X imply?
        self.implies = defaultdict(set)  # tag -> {tags it implies}

        # Backward: what implies X? (for inheritance)
        self.implied_by = defaultdict(set)  # tag -> {tags that imply it}

        # Transitive closure cache
        self.transitive_implies = {}  # tag -> {all tags it transitively implies}
        self.transitive_implied_by = {}  # tag -> {all tags that transitively imply it}

        # Dirty flags for cache invalidation
        self._transitive_cache_dirty = True

    def add_implication(self, source: str, target: str):
        """Add a direct implication: source => target"""
        self.implies[source].add(target)
        self.implied_by[target].add(source)
        self._transitive_cache_dirty = True

    def _compute_transitive_closure(self):
        """Compute transitive closure using Floyd-Warshall-like algorithm"""
        if not self._transitive_cache_dirty:
            return

        # Initialize with direct implications
        all_tags = set(self.implies.keys()) | set(self.implied_by.keys())

        self.transitive_implies = {tag: set(self.implies[tag]) for tag in all_tags}
        self.transitive_implied_by = {tag: set(self.implied_by[tag]) for tag in all_tags}

        # Floyd-Warshall for transitive closure
        for k in all_tags:
            for i in all_tags:
                for j in all_tags:
                    if k in self.transitive_implies[i] and j in self.transitive_implies[k]:
                        self.transitive_implies[i].add(j)
                        self.transitive_implied_by[j].add(i)

        self._transitive_cache_dirty = False

    def get_all_implications(self, tag: str) -> Set[str]:
        """Get all tags that this tag implies (including transitive)"""
        self._compute_transitive_closure()
        return self.transitive_implies.get(tag, set())

    def get_all_implied_by(self, tag: str) -> Set[str]:
        """Get all tags that imply this tag (including transitive)"""
        self._compute_transitive_closure()
        return self.transitive_implied_by.get(tag, set())


class EqualityIndex:
    """Union-find structure for equality groups"""

    def __init__(self):
        self.parent = {}  # tag -> canonical representative
        self.groups = defaultdict(set)  # canonical -> {all equivalent tags}

    def add_equality(self, tag1: str, tag2: str):
        """Add equality relationship: tag1 = tag2"""
        canon1 = self.canonical(tag1)
        canon2 = self.canonical(tag2)

        if canon1 != canon2:
            # Merge groups - use lexicographically smaller as canonical
            if canon1 < canon2:
                new_canon, old_canon = canon1, canon2
            else:
                new_canon, old_canon = canon2, canon1

            # Update all members of old group
            for tag in self.groups[old_canon]:
                self.parent[tag] = new_canon
                self.groups[new_canon].add(tag)

            # Remove old group
            del self.groups[old_canon]

    def canonical(self, tag: str) -> str:
        """Get canonical representative of tag's equality group"""
        if tag not in self.parent:
            self.parent[tag] = tag
            self.groups[tag].add(tag)
            return tag

        # Path compression
        if self.parent[tag] != tag:
            self.parent[tag] = self.canonical(self.parent[tag])
        return self.parent[tag]

    def get_equivalent_tags(self, tag: str) -> Set[str]:
        """Get all tags equivalent to this tag"""
        canon = self.canonical(tag)
        return self.groups[canon].copy()


class AssociationIndex:
    """Manages associations with transitivity and inheritance"""

    def __init__(self):
        # Direct associations only (bidirectional)
        self.direct_associations = defaultdict(set)  # tag -> {directly associated tags}

        # Computed associations (includes inheritance + transitivity)
        self.all_associations = defaultdict(set)  # tag -> {all associated tags}

        # Dirty flag for rebuilding computed associations
        self._computed_cache_dirty = True

    def add_association(self, tag1: str, tag2: str):
        """Add bidirectional association: tag1 ~ tag2"""
        self.direct_associations[tag1].add(tag2)
        self.direct_associations[tag2].add(tag1)
        self._computed_cache_dirty = True

    def rebuild_computed_associations(self, equality_index: 'EqualityIndex',
                                      implication_index: ImplicationIndex):
        """Rebuild all computed associations with propagation rules"""
        if not self._computed_cache_dirty:
            return

        self.all_associations.clear()

        # Step 1: Copy direct associations with equality expansion
        for tag, assocs in self.direct_associations.items():
            canonical_tag = equality_index.canonical(tag)
            for assoc in assocs:
                canonical_assoc = equality_index.canonical(assoc)
                self.all_associations[canonical_tag].add(canonical_assoc)
                self.all_associations[canonical_assoc].add(canonical_tag)

        # Step 2: Forward propagation through associations (transitivity)
        # A ~ B and B ~ C implies A ~ C
        changed = True
        while changed:
            changed = False
            for tag, assocs in list(self.all_associations.items()):
                for assoc in list(assocs):
                    # Add associations of associations
                    for second_level in self.all_associations[assoc]:
                        if second_level not in assocs and second_level != tag:
                            self.all_associations[tag].add(second_level)
                            self.all_associations[second_level].add(tag)
                            changed = True

        # Step 3: Backward propagation through implications (inheritance)
        # A => B and X ~ B implies X ~ A
        for tag, assocs in list(self.all_associations.items()):
            for assoc in list(assocs):
                # Find all things that imply this tag
                for specific_tag in implication_index.get_all_implied_by(tag):
                    self.all_associations[specific_tag].add(assoc)
                    self.all_associations[assoc].add(specific_tag)

                # Find all things that imply the associated tag
                for specific_assoc in implication_index.get_all_implied_by(assoc):
                    self.all_associations[tag].add(specific_assoc)
                    self.all_associations[specific_assoc].add(tag)

        self._computed_cache_dirty = False

    def get_associations(self, tag: str) -> Set[str]:
        """Get all tags associated with this tag"""
        return self.all_associations.get(tag, set())

    def mark_dirty(self):
        """Mark computed associations as needing rebuild"""
        self._computed_cache_dirty = True


class TextIndex:
    """Handles text-to-tag mappings and negations"""

    def __init__(self):
        # Positive mappings for page processing
        self.text_to_tags = {}  # "exact text" -> tag
        self.regex_patterns = []  # [(compiled_regex, tag), ...]

        # Negated patterns for query filtering only
        self.negated_text = set()  # For query: -"exclude this"
        self.negated_regex = []  # For query: -/exclude pattern/

    def add_text_mapping(self, text: str, tag: str):
        """Add text => tag mapping"""
        self.text_to_tags[text] = tag

    def add_regex_mapping(self, pattern: str, flags: str, tag: str):
        """Add regex => tag mapping"""
        # Parse flags
        re_flags = 0
        if 'i' in flags: re_flags |= re.IGNORECASE
        if 'm' in flags: re_flags |= re.MULTILINE
        if 's' in flags: re_flags |= re.DOTALL
        if 'x' in flags: re_flags |= re.VERBOSE

        compiled_pattern = re.compile(pattern, re_flags)
        self.regex_patterns.append((compiled_pattern, tag))

    def add_negated_text(self, text: str):
        """Add negated text pattern for queries"""
        self.negated_text.add(text)

    def add_negated_regex(self, pattern: str, flags: str):
        """Add negated regex pattern for queries"""
        re_flags = 0
        if 'i' in flags: re_flags |= re.IGNORECASE
        if 'm' in flags: re_flags |= re.MULTILINE
        if 's' in flags: re_flags |= re.DOTALL
        if 'x' in flags: re_flags |= re.VERBOSE

        compiled_pattern = re.compile(pattern, re_flags)
        self.negated_regex.append(compiled_pattern)

    def extract_tags_from_text(self, page_text: str) -> Set[str]:
        """Extract tags from page text (no negation checking)"""
        derived_tags = set()

        # Check exact text matches - with whole word boundary check
        for text, tag in self.text_to_tags.items():
            # Use regex word boundary check to ensure whole word matches
            # \b represents a word boundary in regex
            pattern = r'\b' + re.escape(text) + r'\b'
            if re.search(pattern, page_text, re.IGNORECASE):
                derived_tags.add(tag)

        # Check regex patterns
        for pattern, tag in self.regex_patterns:
            if pattern.search(page_text):
                derived_tags.add(tag)

        return derived_tags

    def check_negations_for_query(self, page_text: str) -> Dict[str, bool]:
        """Check negations only when filtering for queries"""
        return {
            'excluded_by_text': any(text in page_text for text in self.negated_text),
            'excluded_by_regex': any(pattern.search(page_text) for pattern in self.negated_regex)
        }


class ContextGroup:
    """Represents a context group like (#a #b) => #c"""

    def __init__(self, elements: List[Tuple[str, str]], target: str):
        self.elements = elements  # [(type, value), ...]
        self.target = target

    def expand_with_implications(self, implication_index: ImplicationIndex,
                                 equality_index: EqualityIndex) -> List['ContextGroup']:
        """Expand context group considering implications: (#b #c) => #d with #a => #b gives (#a #c) => #d"""
        expanded_groups = []

        # Get all possible substitutions for each element
        substitution_options = []
        for elem_type, elem_value in self.elements:
            if elem_type == 'tag':
                canonical = equality_index.canonical(elem_value)
                # Include original tag plus all things that imply it
                options = {canonical} | implication_index.get_all_implied_by(canonical)
                substitution_options.append(list(options))
            else:
                # For non-tags, no substitution
                substitution_options.append([elem_value])

        # Generate Cartesian product of all substitution options
        from itertools import product
        for combination in product(*substitution_options):
            if combination != tuple(elem[1] for elem in self.elements):  # Skip original
                new_elements = [(self.elements[i][0], combination[i]) for i in range(len(combination))]
                expanded_groups.append(ContextGroup(new_elements, self.target))

        return expanded_groups


class OntologyEngine:
    """Main ontology engine that coordinates all indexes"""

    def __init__(self):
        self.implications = ImplicationIndex()
        self.associations = AssociationIndex()
        self.equality = EqualityIndex()
        self.text_mapping = TextIndex()
        self.context_groups = []  # List of ContextGroup objects

    def add_rule(self, source: Any, operator: str, target: Any):
        """Add a single rule and update indexes"""
        if operator == '=>':
            self._add_implication(source, target)
        elif operator == '~':
            self._add_association(source, target)
        elif operator == '=':
            self._add_equality(source, target)

    def _add_implication(self, source: Any, target: Any):
        """Add implication rule"""
        if isinstance(source, tuple) and source[0] == 'context_group':
            # Handle context groups like (#a #b) => #c
            context_group = ContextGroup(source[1], target[1])
            self.context_groups.append(context_group)

            # Also expand immediately and add expanded rules
            expanded = context_group.expand_with_implications(self.implications, self.equality)
            for expanded_group in expanded:
                self.context_groups.append(expanded_group)
        else:
            # Handle text/regex => tag mappings
            if source[0] in ['text', 'negated_text']:
                text = source[1].strip('"')
                if source[0] == 'text':
                    self.text_mapping.add_text_mapping(text, target[1])
                else:  # negated_text
                    text = text[1:]  # Remove leading '-'
                    self.text_mapping.add_negated_text(text)

            elif source[0] in ['regex', 'negated_regex']:
                pattern_with_flags = source[1]
                if source[0] == 'regex':
                    # Parse /pattern/flags format
                    if pattern_with_flags.startswith('/') and pattern_with_flags.rfind('/') > 0:
                        last_slash = pattern_with_flags.rfind('/')
                        pattern = pattern_with_flags[1:last_slash]
                        flags = pattern_with_flags[last_slash + 1:]
                        self.text_mapping.add_regex_mapping(pattern, flags, target[1])
                else:  # negated_regex
                    pattern_with_flags = pattern_with_flags[1:]  # Remove leading '-'
                    if pattern_with_flags.startswith('/') and pattern_with_flags.rfind('/') > 0:
                        last_slash = pattern_with_flags.rfind('/')
                        pattern = pattern_with_flags[1:last_slash]
                        flags = pattern_with_flags[last_slash + 1:]
                        self.text_mapping.add_negated_regex(pattern, flags)

            elif source[0] == 'tag':
                # Regular tag => tag implication
                source_canonical = self.equality.canonical(source[1])
                target_canonical = self.equality.canonical(target[1])
                self.implications.add_implication(source_canonical, target_canonical)

                # Mark associations as dirty since implications affect them
                self.associations.mark_dirty()

    def _add_association(self, source: Any, target: Any):
        """Add association rule (only tag ~ tag allowed)"""
        if source[0] != 'tag' or target[0] != 'tag':
            raise ValueError("Associations only allowed between tags")

        source_canonical = self.equality.canonical(source[1])
        target_canonical = self.equality.canonical(target[1])
        self.associations.add_association(source_canonical, target_canonical)

    def _add_equality(self, source: Any, target: Any):
        """Add equality rule"""
        if source[0] != 'tag' or target[0] != 'tag':
            raise ValueError("Equality only allowed between tags")

        self.equality.add_equality(source[1], target[1])

        # Mark associations as dirty since equality affects them
        self.associations.mark_dirty()

    def process_rules_from_parser(self, rules: List[Tuple[Any, str, Any]]):
        """Process a list of rules from the parser using batched processing for better performance"""
        # Collect all rules by type for batch processing
        implication_rules = []
        association_rules = []
        equality_rules = []
        text_mappings = []
        negated_text = []
        regex_mappings = []
        negated_regex = []
        context_groups = []

        # First pass: categorize all rules by type
        for source, operator, target in rules:
            if operator == '=>':
                if isinstance(source, tuple) and source[0] == 'context_group':
                    context_groups.append((source, target))
                elif source[0] == 'tag':
                    implication_rules.append((source[1], target[1]))
                elif source[0] == 'text':
                    text_mappings.append((source[1].strip('"'), target[1]))
                elif source[0] == 'negated_text':
                    negated_text.append(source[1].strip('"')[1:])  # Remove leading '-'
                elif source[0] == 'regex':
                    regex_mappings.append((source[1], target[1]))
                elif source[0] == 'negated_regex':
                    negated_regex.append(source[1][1:])  # Remove leading '-'
            elif operator == '~':
                if source[0] == 'tag' and target[0] == 'tag':
                    association_rules.append((source[1], target[1]))
                else:
                    raise ValueError("❌ Associations only allowed between tags")
            elif operator == '=':
                if source[0] == 'tag' and target[0] == 'tag':
                    equality_rules.append((source[1], target[1]))
                else:
                    raise ValueError("❌ Equality only allowed between tags")

        # Process equality rules in batch (these affect canonical representations)
        if equality_rules:
            for source_tag, target_tag in equality_rules:
                self.equality.add_equality(source_tag, target_tag)
            # Mark associations as dirty since equalities affect them
            self.associations.mark_dirty()

        # Process tag implications in batch
        if implication_rules:
            for source_tag, target_tag in implication_rules:
                source_canonical = self.equality.canonical(source_tag)
                target_canonical = self.equality.canonical(target_tag)
                self.implications.add_implication(source_canonical, target_canonical)
            # Mark associations as dirty since implications affect them
            self.associations.mark_dirty()

        # Process text mappings in batch
        if text_mappings:
            for text, tag in text_mappings:
                self.text_mapping.add_text_mapping(text, tag)

        # Process negated text in batch
        if negated_text:
            for text in negated_text:
                self.text_mapping.add_negated_text(text)

        # Process regex mappings in batch
        if regex_mappings:
            for pattern_with_flags, tag in regex_mappings:
                if pattern_with_flags.startswith('/') and pattern_with_flags.rfind('/') > 0:
                    last_slash = pattern_with_flags.rfind('/')
                    pattern = pattern_with_flags[1:last_slash]
                    flags = pattern_with_flags[last_slash + 1:]
                    self.text_mapping.add_regex_mapping(pattern, flags, tag)

        # Process negated regex in batch
        if negated_regex:
            for pattern_with_flags in negated_regex:
                if pattern_with_flags.startswith('/') and pattern_with_flags.rfind('/') > 0:
                    last_slash = pattern_with_flags.rfind('/')
                    pattern = pattern_with_flags[1:last_slash]
                    flags = pattern_with_flags[last_slash + 1:]
                    self.text_mapping.add_negated_regex(pattern, flags)

        # Process associations in batch
        if association_rules:
            for source_tag, target_tag in association_rules:
                source_canonical = self.equality.canonical(source_tag)
                target_canonical = self.equality.canonical(target_tag)
                self.associations.add_association(source_canonical, target_canonical)

        # Process context groups (these are more complex and might need individual processing)
        for source, target in context_groups:
            context_group = ContextGroup(source[1], target[1])
            self.context_groups.append(context_group)

            # Expand immediately and add expanded rules
            expanded = context_group.expand_with_implications(self.implications, self.equality)
            for expanded_group in expanded:
                self.context_groups.append(expanded_group)

        # Rebuild computed structures once at the end
        self._rebuild_computed_structures()

        print(f"✅ Processed {len(rules)} ontology rules")

    def _rebuild_computed_structures(self):
        """Rebuild all computed structures"""
        self.associations.rebuild_computed_associations(self.equality, self.implications)

    def expand_page_tags(self, page_text: str, explicit_tags: Set[str]) -> Dict[str, Set[str]]:
        """Given page text and explicit tags, return all inferred tags and associations"""
        result = {
            'explicit_tags': set(),
            'text_derived_tags': set(),
            'implied_tags': set(),
            'associated_tags': set(),
            'all_tags': set()  # Union of all above
        }

        # Process explicit tags through equality and get implications
        for tag in explicit_tags:
            canonical = self.equality.canonical(tag)
            result['explicit_tags'].add(canonical)

            # Add all things this tag implies
            result['implied_tags'].update(self.implications.get_all_implications(canonical))

            # Add all associated tags
            result['associated_tags'].update(self.associations.get_associations(canonical))

        # Extract tags from text
        text_derived = self.text_mapping.extract_tags_from_text(page_text)
        for tag in text_derived:
            canonical = self.equality.canonical(tag)
            result['text_derived_tags'].add(canonical)

            # Add implications and associations of text-derived tags
            result['implied_tags'].update(self.implications.get_all_implications(canonical))
            result['associated_tags'].update(self.associations.get_associations(canonical))

        # Check context groups
        all_page_tags = result['explicit_tags'] | result['text_derived_tags']
        for context_group in self.context_groups:
            if self._context_group_matches(context_group, all_page_tags, page_text):
                target_canonical = self.equality.canonical(context_group.target)
                result['implied_tags'].add(target_canonical)
                result['implied_tags'].update(self.implications.get_all_implications(target_canonical))
                result['associated_tags'].update(self.associations.get_associations(target_canonical))

        # Create union of all tags
        result['all_tags'] = (result['explicit_tags'] | result['text_derived_tags'] |
                              result['implied_tags'] | result['associated_tags'])

        return result

    def _context_group_matches(self, context_group: ContextGroup, page_tags: Set[str], page_text: str) -> bool:
        """Check if a context group matches the page"""
        for elem_type, elem_value in context_group.elements:
            if elem_type == 'tag':
                canonical = self.equality.canonical(elem_value)
                if canonical not in page_tags:
                    return False
            elif elem_type == 'text':
                text = elem_value.strip('"')
                if text not in page_text:
                    return False
            elif elem_type == 'regex':
                # Parse and check regex
                if elem_value.startswith('/') and elem_value.rfind('/') > 0:
                    last_slash = elem_value.rfind('/')
                    pattern = elem_value[1:last_slash]
                    flags = elem_value[last_slash + 1:]

                    re_flags = 0
                    if 'i' in flags: re_flags |= re.IGNORECASE
                    if 'm' in flags: re_flags |= re.MULTILINE
                    if 's' in flags: re_flags |= re.DOTALL
                    if 'x' in flags: re_flags |= re.VERBOSE

                    compiled_pattern = re.compile(pattern, re_flags)
                    if not compiled_pattern.search(page_text):
                        return False
        return True


# Standalone function that augments a page with tags from an ontology
def augment_page_tags(ontology: OntologyEngine, page: dict) -> dict:
    """
    Augment a page dictionary with derived tags and associated tags.
    FAIL FAST: Processing errors will raise exceptions immediately.
    """
    if not isinstance(page, dict):
        raise TypeError("❌ Page must be a dictionary")
    
    if 'text' not in page:
        raise KeyError("❌ Page must have 'text' field")
    
    # Create a new page dict to avoid modifying the original
    augmented_page = page.copy()

    # Ensure raw_tags is in the augmented page
    original_tags = set(page.get('raw_tags', []))

    # Validate that all tags start with #
    for tag in original_tags:
        if not tag.startswith('#'):
            raise ValueError(f"❌ Invalid tag format: '{tag}'. All tags must start with '#'")

    augmented_page['raw_tags'] = list(original_tags)

    # Convert list of tags to set of tags for processing
    tag_set = original_tags

    # Expand tags using the ontology engine
    expanded_result = ontology.expand_page_tags(page.get('text', ''), tag_set)

    # Extract all expanded tags (explicit + implied + from text)
    all_tags = set()
    for tag_category in ['explicit_tags', 'implied_tags', 'text_derived_tags']:
        all_tags.update(expanded_result.get(tag_category, set()))

    # Extract associated tags
    associated_tags = expanded_result.get('associated_tags', set())

    # Convert back to lists and store in augmented page
    augmented_page['tags'] = sorted(list(all_tags))
    augmented_page['assoc_tags'] = sorted(list(associated_tags - all_tags))

    return augmented_page