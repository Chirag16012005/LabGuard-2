from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class PassageMatch:
    """Represents a suspicious passage within a document pair."""

    source_doc_id: str
    target_doc_id: str
    source_start: int
    source_end: int
    target_start: int
    target_end: int
    similarity: float
    pos_similarity: float


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
        key=lambda p: (p.source_doc_id, p.target_doc_id, p.source_start, p.source_end)
    )

    merged: List[PassageMatch] = []
    current = PassageMatch(**vars(passages_list[0]))

    for p in passages_list[1:]:
        if (
            p.source_doc_id == current.source_doc_id
            and p.target_doc_id == current.target_doc_id
            and p.source_start <= current.source_end + max_gap
        ):
            current.source_end = max(current.source_end, p.source_end)
            current.target_end = max(current.target_end, p.target_end)
            current.similarity = max(current.similarity, p.similarity)
            current.pos_similarity = max(current.pos_similarity, p.pos_similarity)
        else:
            merged.append(current)
            current = PassageMatch(**vars(p))

    merged.append(current)
    return merged


__all__ = ["PassageMatch", "merge_overlapping_passages"]

