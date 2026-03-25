from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class PassageMatch:
    """Represents a suspicious passage within a document pair."""

    source_doc_id: str
    target_doc_id: str
    start_pos: int
    end_pos: int
    similarity: float


def merge_overlapping_passages(
    passages: Iterable[PassageMatch],
    max_gap: int = 0,
) -> List[PassageMatch]:
    """
    Merge overlapping or near-adjacent passages for each document pair.

    - Passages are grouped by (source_doc_id, target_doc_id)
    - Overlaps and gaps <= max_gap are merged
    - Similarity of merged passages is the max of merged parts
    """
    passages_list = list(passages)
    if not passages_list:
        return []

    passages_list.sort(
        key=lambda p: (p.source_doc_id, p.target_doc_id, p.start_pos, p.end_pos)
    )

    merged: List[PassageMatch] = []
    current = passages_list[0]

    for p in passages_list[1:]:
        if (
            p.source_doc_id == current.source_doc_id
            and p.target_doc_id == current.target_doc_id
            and p.start_pos <= current.end_pos + max_gap
        ):
            current.end_pos = max(current.end_pos, p.end_pos)
            current.similarity = max(current.similarity, p.similarity)
        else:
            merged.append(current)
            current = p

    merged.append(current)
    return merged


__all__ = ["PassageMatch", "merge_overlapping_passages"]

