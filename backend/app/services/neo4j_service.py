import logging
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase

from app.models import GraphData, GraphEdge, GraphNode, GraphStats, ProteinStatus

load_dotenv()
logger = logging.getLogger(__name__)


class Neo4jService:
    def __init__(self):
        self.driver = None

    async def connect(self):
        """Initialize Neo4j connection"""
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

        await self._create_constraints()

    async def _create_constraints(self):
        """Create database constraints for uniqueness"""
        if self.driver is None:
            raise Exception("Neo4j driver not initialized")

        logger.info(
            "Skipping constraint creation due to Neo4j driver type restrictions"
        )
        # Constraints will need to be created manually or via a different method

    async def disconnect(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()

    async def clear_database(self):
        """Clear all nodes and relationships"""
        if self.driver is None:
            raise Exception("Neo4j driver not initialized")

        async with self.driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")

    async def create_protein_node(self, protein_data: Dict[str, Any]) -> bool:
        """Create a protein node"""
        query = """
        MERGE (p:Protein {protein_id: $protein_id})
        SET p.name = $name,
            p.status = $status,
            p.ec_numbers = $ec_numbers,
            p.go_terms = $go_terms,
            p.domain_count = $domain_count,
            p.taxonomy_id = $taxonomy_id
        RETURN p
        """

        if self.driver is None:
            raise Exception("Neo4j driver not initialized")

        async with self.driver.session() as session:
            result = await session.run(query, **protein_data)
            return bool(await result.single())

    async def create_similarity_edge(
        self, source_id: str, target_id: str, edge_data: Dict[str, Any]
    ) -> bool:
        """Create a similarity edge between two proteins"""
        query = """
        MATCH (source:Protein {protein_id: $source_id})
        MATCH (target:Protein {protein_id: $target_id})
        MERGE (source)-[r:SIMILAR_TO]-(target)
        SET r.weight = $weight,
            r.jaccard_similarity = $jaccard_similarity,
            r.shared_domains = $shared_domains,
            r.shared_domain_count = $shared_domain_count
        RETURN r
        """

        if self.driver is None:
            raise Exception("Neo4j driver not initialized")

        async with self.driver.session() as session:
            result = await session.run(
                query, source_id=source_id, target_id=target_id, **edge_data
            )
            return bool(await result.single())

    async def build_protein_graph(
        self, proteins_data: List[Dict[str, Any]], min_similarity: float = 0.1
    ):
        """Build the complete protein graph"""
        if self.driver is None:
            raise Exception("Neo4j driver not initialized")

        logger.info(f"Building graph with {len(proteins_data)} proteins")

        await self.clear_database()

        protein_nodes = []
        for protein in proteins_data:
            node_data = {
                "protein_id": protein["protein_id"],
                "name": protein.get("name", ""),
                "status": protein.get("status", "unreviewed"),
                "ec_numbers": protein.get("ec_numbers", []),
                "go_terms": protein.get("go_terms", []),
                "domain_count": len(protein.get("domains", [])),
                "taxonomy_id": protein.get("taxonomy_id", ""),
            }
            protein_nodes.append(node_data)

        async with self.driver.session() as session:
            for node_data in protein_nodes:
                await session.run(
                    """
                    MERGE (p:Protein {protein_id: $protein_id})
                    SET p.name = $name,
                        p.status = $status,
                        p.ec_numbers = $ec_numbers,
                        p.go_terms = $go_terms,
                        p.domain_count = $domain_count,
                        p.taxonomy_id = $taxonomy_id
                    """,
                    **node_data,
                )

        edges_created = 0
        for i, protein1 in enumerate(proteins_data):
            domains1 = set(protein1.get("domains", []))

            for j, protein2 in enumerate(proteins_data[i + 1 :], i + 1):
                domains2 = set(protein2.get("domains", []))

                if not domains1 or not domains2:
                    continue

                intersection = domains1.intersection(domains2)
                union = domains1.union(domains2)

                if not intersection:
                    continue

                jaccard_similarity = len(intersection) / len(union)

                if jaccard_similarity >= min_similarity:
                    edge_data = {
                        "weight": jaccard_similarity,
                        "jaccard_similarity": jaccard_similarity,
                        "shared_domains": list(intersection),
                        "shared_domain_count": len(intersection),
                    }

                    await self.create_similarity_edge(
                        protein1["protein_id"], protein2["protein_id"], edge_data
                    )
                    edges_created += 1

        logger.info(
            f"Graph built with {len(protein_nodes)} nodes and {edges_created} edges"
        )

    async def get_protein_neighbors(self, protein_id: str, depth: int = 1) -> GraphData:
        """Get protein and its neighbors"""
        if self.driver is None:
            raise Exception("Neo4j driver not initialized")

        # Build query with depth as literal since Neo4j doesn't support parameters in relationship patterns
        query = f"""
        MATCH path = (p:Protein {{protein_id: $protein_id}})-[:SIMILAR_TO*1..{depth}]-(connected)
        WITH collect(DISTINCT p) + collect(DISTINCT connected) as nodes,
             collect(DISTINCT relationships(path)) as rels
        UNWIND rels as rel_list
        UNWIND rel_list as rel
        RETURN nodes, collect(DISTINCT rel) as relationships
        """

        async with self.driver.session() as session:
            result = await session.run(query, protein_id=protein_id)
            record = await result.single()

            if not record:
                return GraphData(nodes=[], edges=[])

            nodes = []
            for node in record["nodes"]:
                node_data = dict(node)

                status = node_data.get("status")
                if status not in ["reviewed", "unreviewed"]:
                    status = ProteinStatus("unreviewed")

                graph_node = GraphNode(
                    protein_id=node_data["protein_id"],
                    name=node_data.get("name"),
                    status=status,
                    ec_numbers=node_data.get("ec_numbers", []),
                    go_terms=node_data.get("go_terms", []),
                    domain_count=node_data.get("domain_count", 0),
                )
                nodes.append(graph_node)

            edges = []
            for rel in record["relationships"]:
                edge_data = dict(rel)
                graph_edge = GraphEdge(
                    source_protein_id=edge_data["source_protein_id"],
                    target_protein_id=edge_data["target_protein_id"],
                    weight=edge_data.get("weight", 0),
                    shared_domains=edge_data.get("shared_domains", []),
                    jaccard_similarity=edge_data.get("jaccard_similarity", 0),
                )
                edges.append(graph_edge)

            return GraphData(nodes=nodes, edges=edges)

    async def search_proteins(
        self, search_query: str, limit: int = 50
    ) -> List[GraphNode]:
        """Search proteins by name or ID"""
        if self.driver is None:
            raise Exception("Neo4j driver not initialized")

        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (p:Protein)
                WHERE toLower(p.protein_id) CONTAINS toLower($search_query)
                   OR toLower(p.name) CONTAINS toLower($search_query)
                RETURN p
                LIMIT $limit
                """,
                search_query=search_query,
                limit=limit,
            )
            nodes = []

            async for record in result:
                node_data = dict(record["p"])
                status_str = node_data.get("status", "unreviewed")
                if status_str not in ["reviewed", "unreviewed"]:
                    status_str = "unreviewed"
                status = ProteinStatus(status_str)

                graph_node = GraphNode(
                    protein_id=node_data["protein_id"],
                    name=node_data.get("name"),
                    status=status,
                    ec_numbers=node_data.get("ec_numbers", []),
                    go_terms=node_data.get("go_terms", []),
                    domain_count=node_data.get("domain_count", 0),
                )
                nodes.append(graph_node)

            return nodes

    async def get_graph_statistics(self) -> GraphStats:
        """Get comprehensive graph statistics"""
        if self.driver is None:
            raise Exception("Neo4j driver not initialized")

        async with self.driver.session() as session:
            total_proteins_result = await session.run(
                "MATCH (p:Protein) RETURN count(p) as count"
            )
            total_proteins_record = await total_proteins_result.single()
            total_proteins = (
                total_proteins_record["count"] if total_proteins_record else 0
            )

            reviewed_result = await session.run(
                "MATCH (p:Protein {status: 'reviewed'}) RETURN count(p) as count"
            )
            reviewed_record = await reviewed_result.single()
            reviewed_proteins = reviewed_record["count"] if reviewed_record else 0

            unreviewed_result = await session.run(
                "MATCH (p:Protein {status: 'unreviewed'}) RETURN count(p) as count"
            )
            unreviewed_record = await unreviewed_result.single()
            unreviewed_proteins = unreviewed_record["count"] if unreviewed_record else 0

            isolated_result = await session.run("""
                MATCH (p:Protein)
                WHERE NOT (p)-[:SIMILAR_TO]-()
                RETURN count(p) as count
            """)
            isolated_record = await isolated_result.single()
            isolated_proteins = isolated_record["count"] if isolated_record else 0

            edges_result = await session.run(
                "MATCH ()-[r:SIMILAR_TO]-() RETURN count(r) as count"
            )
            edges_record = await edges_result.single()
            total_edges = edges_record["count"] if edges_record else 0

            avg_degree = 0
            if total_proteins > 0:
                avg_degree = (2 * total_edges) / total_proteins

            clustering_result = await session.run("""
                CALL gds.localClusteringCoefficient.stream({
                    nodeProjection: 'Protein',
                    relationshipProjection: {
                        SIMILAR_TO: {
                            type: 'SIMILAR_TO',
                            orientation: 'UNDIRECTED'
                        }
                    }
                })
                YIELD nodeId, localClusteringCoefficient
                RETURN avg(localClusteringCoefficient) as avgClustering
            """)

            clustering_coefficient = None
            clustering_record = await clustering_result.single()
            if clustering_record:
                clustering_coefficient = clustering_record["avgClustering"]

            return GraphStats(
                total_proteins=total_proteins,
                reviewed_proteins=reviewed_proteins,
                unreviewed_proteins=unreviewed_proteins,
                isolated_proteins=isolated_proteins,
                total_edges=total_edges,
                average_degree=avg_degree,
                clustering_coefficient=clustering_coefficient,
            )

    async def get_proteins_for_label_propagation(
        self, attribute: str
    ) -> List[Dict[str, Any]]:
        """Get proteins with their labels for label propagation"""
        if self.driver is None:
            raise Exception("Neo4j driver not initialized")

        if attribute == "ec":
            query = """
            MATCH (p:Protein)
            RETURN p.protein_id as protein_id,
                   p.ec_numbers as labels,
                   [(p)-[:SIMILAR_TO]-(neighbor) | neighbor.protein_id] as neighbors
            """
        elif attribute == "go":
            query = """
            MATCH (p:Protein)
            RETURN p.protein_id as protein_id,
                   p.go_terms as labels,
                   [(p)-[:SIMILAR_TO]-(neighbor) | neighbor.protein_id] as neighbors
            """
        else:
            raise ValueError("Attribute must be 'ec' or 'go'")

        async with self.driver.session() as session:
            result = await session.run(query)
            proteins = []

            async for record in result:
                proteins.append(
                    {
                        "protein_id": record["protein_id"],
                        "labels": record["labels"] or [],
                        "neighbors": record["neighbors"] or [],
                    }
                )

            return proteins

    async def update_protein_labels(
        self, protein_id: str, labels: List[str], attribute: str
    ) -> bool:
        """Update protein labels after propagation"""
        if self.driver is None:
            raise Exception("Neo4j driver not initialized")

        if attribute == "ec":
            query = """
            MATCH (p:Protein {protein_id: $protein_id})
            SET p.ec_numbers = $labels
            RETURN p
            """
        elif attribute == "go":
            query = """
            MATCH (p:Protein {protein_id: $protein_id})
            SET p.go_terms = $labels
            RETURN p
            """
        else:
            raise ValueError("Attribute must be 'ec' or 'go'")

        async with self.driver.session() as session:
            result = await session.run(query, protein_id=protein_id, labels=labels)
            return bool(await result.single())


neo4j_service = Neo4jService()
