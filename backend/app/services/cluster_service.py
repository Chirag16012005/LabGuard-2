from __future__ import annotations

from ..repositories.report_repository import ReportRepository


class ClusteringService:
    """Generate document clusters based on plagiarism similarity."""

    def __init__(self) -> None:
        self.report_repo = ReportRepository()

    async def get_assignment_clusters(self, assignment_id: str) -> dict:
        """Get plagiarism clusters for an assignment."""
        # Get the latest report for the assignment
        report = await self.report_repo.get_latest_report(assignment_id)

        if not report:
            return {
                "assignment_id": assignment_id,
                "clusters": [],
                "message": "No reports available for this assignment",
            }

        # Extract clusters from report results
        results = report.get("results", {})
        clusters = self._build_clusters_from_results(results)

        return {
            "assignment_id": assignment_id,
            "clusters": clusters,
            "report_id": report["id"],
        }

    @staticmethod
    def _build_clusters_from_results(results: dict) -> list[dict]:
        """Build document clusters from detection results using DSU."""
        from ..utils.disjoint_set import DisjointSet

        if not results:
            return []

        # Initialize DSU with all documents
        dsu = DisjointSet(results.keys())

        # Union documents with high similarity
        similarity_threshold = 0.5
        for doc_id, (_, doc_group, score) in results.items():
            for target_doc_id, (_, similarity_score) in doc_group.items():
                if similarity_score >= similarity_threshold:
                    if doc_id < target_doc_id:
                        dsu.union(doc_id, target_doc_id)

        # Group documents by cluster
        from collections import defaultdict

        clusters_map = defaultdict(list)
        for doc_id in results.keys():
            root = dsu.find(doc_id)
            clusters_map[root].append(doc_id)

        # Build cluster list (only include clusters with 2+ documents)
        clusters = []
        for root, members in clusters_map.items():
            if len(members) >= 2:
                clusters.append(
                    {
                        "cluster_id": root,
                        "members": sorted(members),
                        "size": len(members),
                    }
                )

        return clusters
