from collections import defaultdict, Counter
from typing import Dict, List
from itertools import combinations


class CooccurrenceTracker:
    def __init__(self, k: int = 20):
        """
        Initialize the co-occurrence tracker.

        Args:
            k: Maximum number of co-occurrences to return per tag
        """
        self.k = k
        # Store co-occurrence counts for each tag
        self.cooccurrences = defaultdict(Counter)

    def observe(self, tags: List[str]):
        """
        Record co-occurrences between tags in a list.

        Args:
            tags: List of string tags

        If fewer than 2 unique tags, the observation is ignored.
        """
        # Remove duplicates while preserving order, then filter out empty/None
        unique_tags = []
        seen = set()
        for tag in tags:
            if tag and tag not in seen:
                unique_tags.append(tag)
                seen.add(tag)

        # Ignore if fewer than 2 unique tags
        if len(unique_tags) < 2:
            return

        # Record all pairwise co-occurrences
        for tag1, tag2 in combinations(unique_tags, 2):
            self.cooccurrences[tag1][tag2] += 1
            self.cooccurrences[tag2][tag1] += 1

    def get_cooccurrences(self) -> Dict[str, List[str]]:
        """
        Get the top k co-occurrences for each tag.

        Returns:
            Dictionary mapping each tag to its most common co-occurring tags
        """
        result = {}
        for tag, counter in self.cooccurrences.items():
            # Get top k most common co-occurring tags
            most_common = counter.most_common(self.k)
            result[tag] = [cooccurring_tag for cooccurring_tag, count in most_common]
        return result

    def get_cooccurrences_with_counts(self) -> Dict[str, List[tuple]]:
        """
        Get the top k co-occurrences with their counts.

        Returns:
            Dictionary mapping each tag to list of (tag, count) tuples
        """
        result = {}
        for tag, counter in self.cooccurrences.items():
            result[tag] = counter.most_common(self.k)
        return result

    def get_count(self, tag1: str, tag2: str) -> int:
        """Get the co-occurrence count between two specific tags."""
        return self.cooccurrences[tag1][tag2]

    def reset(self):
        """Clear all recorded co-occurrences."""
        self.cooccurrences.clear()


# Example usage
if __name__ == "__main__":
    # Create tracker with k=2 for demo
    tracker = CooccurrenceTracker(k=20)

    # Record some observations - takes lists only
    tracker.observe(['#foo', '#bar'])  # Two tags
    tracker.observe(['#foo', '#baz'])  # Two tags
    tracker.observe(['#foo', '#bar', '#qux'])  # Multiple tags - all pairs recorded
    tracker.observe(['#blah', '#yada', '#foo'])  # Multiple tags
    tracker.observe(['#single'])  # Ignored (only 1 tag)
    tracker.observe([])  # Ignored (empty list)

    # Get results
    cooccurrences = tracker.get_cooccurrences()
    print("Top co-occurrences:")
    for tag, related in cooccurrences.items():
        print(f"  {tag}: {related}")

    # Get results with counts
    print("\nWith counts:")
    cooccurrences_with_counts = tracker.get_cooccurrences_with_counts()
    for tag, related in cooccurrences_with_counts.items():
        print(f"  {tag}: {related}")