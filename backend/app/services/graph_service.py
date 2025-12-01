import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

import numpy as np

from app.services.mongodb_service import mongodb_service
from app.services.neo4j_service import neo4j_service

logger = logging.getLogger(__name__)


class GraphConstructionService:
    def __init__(self):
        self.min_similarity = 0.1

    def calculate_jaccard_similarity(self, set1: set, set2: set) -> float:
        """Calculate Jaccard similarity between two sets"""
        if not set1 or not set2:
            return 0.0

        intersection = set1.intersection(set2)
        union = set1.union(set2)

        return len(intersection) / len(union) if union else 0.0

    async def build_protein_graph(
        self, min_similarity: float = 0.1, max_proteins: Optional[int] = None
    ):
        """Build protein graph using Jaccard similarity on domains"""
        self.min_similarity = min_similarity
        logger.info(f"Building protein graph with min_similarity={min_similarity}")

        proteins_data = await mongodb_service.get_all_proteins_for_graph(max_proteins)
        logger.info(f"Retrieved {len(proteins_data)} proteins from MongoDB")

        if not proteins_data:
            logger.warning("No proteins found in database")
            return

        domain_index = self._build_domain_index(proteins_data)
        logger.info(f"Built domain index with {len(domain_index)} unique domains")

        edges = self._compute_similarities(proteins_data, domain_index)
        logger.info(f"Computed {len(edges)} similarity edges")

        await neo4j_service.build_protein_graph(proteins_data, min_similarity)
        logger.info("Protein graph construction completed")

    def _build_domain_index(
        self, proteins_data: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Build inverted index mapping domains to proteins"""
        domain_index = defaultdict(list)

        for protein in proteins_data:
            protein_id = protein["protein_id"]
            domains = set(protein.get("domains", []))

            for domain in domains:
                domain_index[domain].append(protein_id)

        return domain_index

    def _compute_similarities(
        self, proteins_data: List[Dict[str, Any]], domain_index: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """Compute pairwise Jaccard similarities efficiently"""
        protein_domains = {}
        for protein in proteins_data:
            protein_domains[protein["protein_id"]] = set(protein.get("domains", []))

        protein_pairs = defaultdict(
            lambda: {"shared_domains": set(), "shared_count": 0}
        )

        for domain, protein_list in domain_index.items():
            if len(protein_list) < 2:
                continue

            for i in range(len(protein_list)):
                for j in range(i + 1, len(protein_list)):
                    protein1, protein2 = protein_list[i], protein_list[j]
                    pair_key = tuple(sorted([protein1, protein2]))

                    protein_pairs[pair_key]["shared_domains"].add(domain)
                    protein_pairs[pair_key]["shared_count"] += 1

        edges = []
        for (protein1, protein2), similarity_data in protein_pairs.items():
            domains1 = protein_domains[protein1]
            domains2 = protein_domains[protein2]

            shared_domains = similarity_data["shared_domains"]
            union_domains = domains1.union(domains2)

            if not union_domains:
                continue

            jaccard_similarity = len(shared_domains) / len(union_domains)

            if jaccard_similarity >= self.min_similarity:
                edges.append(
                    {
                        "source_protein_id": protein1,
                        "target_protein_id": protein2,
                        "weight": jaccard_similarity,
                        "jaccard_similarity": jaccard_similarity,
                        "shared_domains": list(shared_domains),
                        "shared_domain_count": len(shared_domains),
                    }
                )

        return edges

    async def get_protein_similarity_matrix(
        self, protein_ids: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Get similarity matrix for specific proteins"""
        proteins_data = []
        for protein_id in protein_ids:
            protein = await mongodb_service.get_protein_by_id(protein_id)
            if protein:
                proteins_data.append(
                    {
                        "protein_id": protein.protein_id,
                        "domains": [domain.domain_id for domain in protein.domains],
                    }
                )

        similarity_matrix = {}
        for i, protein1 in enumerate(proteins_data):
            similarity_matrix[protein1["protein_id"]] = {}
            domains1 = set(protein1["domains"])

            for protein2 in proteins_data:
                domains2 = set(protein2["domains"])
                similarity = self.calculate_jaccard_similarity(domains1, domains2)
                similarity_matrix[protein1["protein_id"]][protein2["protein_id"]] = (
                    similarity
                )

        return similarity_matrix

    async def find_similar_proteins(
        self, protein_id: str, top_k: int = 10, min_similarity: float = 0.1
    ) -> List[Dict[str, Any]]:
        """Find most similar proteins to a given protein"""
        target_protein = await mongodb_service.get_protein_by_id(protein_id)
        if not target_protein:
            return []

        target_domains = set(domain.domain_id for domain in target_protein.domains)

        all_proteins = await mongodb_service.get_all_proteins_for_graph()
        similarities = []

        for protein in all_proteins:
            if protein["protein_id"] == protein_id:
                continue

            protein_domains = set(protein.get("domains", []))
            similarity = self.calculate_jaccard_similarity(
                target_domains, protein_domains
            )

            if similarity >= min_similarity:
                similarities.append(
                    {
                        "protein_id": protein["protein_id"],
                        "name": protein.get("name"),
                        "similarity": similarity,
                        "shared_domains": list(
                            target_domains.intersection(protein_domains)
                        ),
                    }
                )

        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:top_k]

    async def analyze_domain_distribution(self) -> Dict[str, Any]:
        """Analyze domain distribution across proteins"""
        proteins_data = await mongodb_service.get_all_proteins_for_graph()

        domain_counts = defaultdict(int)
        protein_domain_counts = []

        for protein in proteins_data:
            domains = protein.get("domains", [])
            protein_domain_counts.append(len(domains))

            for domain in domains:
                domain_counts[domain] += 1

        domain_counts = dict(
            sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
        )

        stats = {
            "total_unique_domains": len(domain_counts),
            "most_common_domains": list(domain_counts.items())[:20],
            "average_domains_per_protein": np.mean(protein_domain_counts)
            if protein_domain_counts
            else 0,
            "median_domains_per_protein": np.median(protein_domain_counts)
            if protein_domain_counts
            else 0,
            "max_domains_per_protein": max(protein_domain_counts)
            if protein_domain_counts
            else 0,
            "min_domains_per_protein": min(protein_domain_counts)
            if protein_domain_counts
            else 0,
            "proteins_with_no_domains": sum(
                1 for count in protein_domain_counts if count == 0
            ),
        }

        return stats


graph_service = GraphConstructionService()
