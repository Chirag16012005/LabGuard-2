from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Tile:
    """Represents a matched token span between two sequences."""

    src_start: int
    src_end: int
    dst_start: int
    dst_end: int

    @property
    def length(self) -> int:
        return self.src_end - self.src_start


class GreedyStringTiler:
    """Greedy String Tiling over token sequences with basic safeguards."""

    DEFAULT_MIN_MATCH_LENGTH = 5
    DEFAULT_MAX_TOKENS = 20_000

    def __init__(
        self,
        min_match_length: int | None = None,
        max_tokens: int | None = None,
    ) -> None:
        if min_match_length is not None and min_match_length <= 0:
            raise ValueError("min_match_length must be positive")
        self.min_match_length = min_match_length or self.DEFAULT_MIN_MATCH_LENGTH
        self.max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS

    def find_tiles(
        self, src_tokens: Sequence[str], dst_tokens: Sequence[str]
    ) -> List[Tile]:
        """
        Run GST and return matched tiles.

        This uses a straightforward implementation that is suitable
        once documents have been narrowed to suspicious passages.
        """
        if not isinstance(src_tokens, Sequence) or not isinstance(
            dst_tokens, Sequence
        ):
            raise TypeError("src_tokens and dst_tokens must be sequences")

        if len(src_tokens) > self.max_tokens or len(dst_tokens) > self.max_tokens:
            logger.warning(
                "Token sequence lengths (%d, %d) exceed max_tokens=%d; limiting",
                len(src_tokens),
                len(dst_tokens),
                self.max_tokens,
            )
            src_tokens = src_tokens[: self.max_tokens]
            dst_tokens = dst_tokens[: self.max_tokens]

        tiles: List[Tile] = []
        src_marked = [False] * len(src_tokens)
        dst_marked = [False] * len(dst_tokens)

        min_len = self.min_match_length

        while True:
            matches: List[Tuple[int, int, int]] = []
            max_len = min_len

            for i in range(len(src_tokens)):
                if src_marked[i]:
                    continue
                for j in range(len(dst_tokens)):
                    if dst_marked[j]:
                        continue

                    k = 0
                    while (
                        i + k < len(src_tokens)
                        and j + k < len(dst_tokens)
                        and not src_marked[i + k]
                        and not dst_marked[j + k]
                        and src_tokens[i + k] == dst_tokens[j + k]
                    ):
                        k += 1

                    if k == 0:
                        continue

                    if k > max_len:
                        max_len = k
                        matches = [(i, j, k)]
                    elif k == max_len and k >= min_len:
                        matches.append((i, j, k))

            if not matches:
                break

            for i, j, k in matches:
                for offset in range(k):
                    src_marked[i + offset] = True
                    dst_marked[j + offset] = True
                tiles.append(Tile(i, i + k, j, j + k))

        tiles.sort(key=lambda t: (t.src_start, t.dst_start))
        return tiles

    def find_tiles_for_passages(
        self,
        src_tokens: Iterable[str],
        dst_tokens: Iterable[str],
    ) -> List[Tile]:
        """Convenience wrapper for iterable inputs."""
        return self.find_tiles(list(src_tokens), list(dst_tokens))


__all__ = ["GreedyStringTiler", "Tile"]

