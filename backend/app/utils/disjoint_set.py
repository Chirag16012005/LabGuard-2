from __future__ import annotations

from typing import Dict, Iterable, List


class DisjointSet:
    """Disjoint Set Union (DSU) with path compression and union by size."""

    def __init__(self, elements: Iterable[str]) -> None:
        self.parent: Dict[str, str] = {}
        self.size: Dict[str, int] = {}
        for element in elements:
            self.parent[element] = element
            self.size[element] = 1

    def find(self, x: str) -> str:
        """Find the root of the set containing x with path compression."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str) -> None:
        """Union the sets containing x and y using union by size."""
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x != root_y:
            if self.size[root_x] > self.size[root_y]:
                self.parent[root_y] = root_x
                self.size[root_x] += self.size[root_y]
            else:
                self.parent[root_x] = root_y
                self.size[root_y] += self.size[root_x]


__all__ = ["DisjointSet"]