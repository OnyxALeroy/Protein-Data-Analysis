from fastapi import APIRouter, HTTPException

from app.services.mongodb_service import mongodb_service
from app.services.neo4j_service import neo4j_service

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/database")
async def get_database_statistics():
    """Get MongoDB database statistics"""
    try:
        stats = await mongodb_service.get_statistics()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get database statistics: {str(e)}"
        )


@router.get("/graph")
async def get_graph_statistics():
    """Get Neo4j graph statistics"""
    try:
        stats = await neo4j_service.get_graph_statistics()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get graph statistics: {str(e)}"
        )


@router.get("/overview")
async def get_overview_statistics():
    """Get comprehensive overview statistics from both databases"""
    try:
        db_stats = await mongodb_service.get_statistics()
        graph_stats = await neo4j_service.get_graph_statistics()

        overview = {
            "database": db_stats,
            "graph": graph_stats,
            "summary": {
                "total_proteins_db": db_stats["total_proteins"],
                "total_proteins_graph": graph_stats.total_proteins,
                "reviewed_percentage": (
                    graph_stats.reviewed_proteins / graph_stats.total_proteins * 100
                )
                if graph_stats.total_proteins > 0
                else 0,
                "unreviewed_percentage": (
                    graph_stats.unreviewed_proteins / graph_stats.total_proteins * 100
                )
                if graph_stats.total_proteins > 0
                else 0,
                "isolated_percentage": (
                    graph_stats.isolated_proteins / graph_stats.total_proteins * 100
                )
                if graph_stats.total_proteins > 0
                else 0,
                "average_degree": graph_stats.average_degree,
                "graph_density": (2 * graph_stats.total_edges)
                / (graph_stats.total_proteins * (graph_stats.total_proteins - 1))
                if graph_stats.total_proteins > 1
                else 0,
            },
        }

        return overview

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get overview statistics: {str(e)}"
        )


@router.get("/annotation-coverage")
async def get_annotation_coverage():
    """Get annotation coverage statistics"""
    try:
        db_stats = await mongodb_service.get_statistics()

        total = db_stats["total_proteins"]
        if total == 0:
            return {"error": "No proteins found in database"}

        coverage = {
            "ec_coverage": (db_stats["proteins_with_ec"] / total * 100),
            "go_coverage": (db_stats["proteins_with_go"] / total * 100),
            "domain_coverage": (db_stats["proteins_with_domains"] / total * 100),
            "total_proteins": total,
            "proteins_with_ec": db_stats["proteins_with_ec"],
            "proteins_with_go": db_stats["proteins_with_go"],
            "proteins_with_domains": db_stats["proteins_with_domains"],
            "proteins_without_annotations": total
            - max(db_stats["proteins_with_ec"], db_stats["proteins_with_go"]),
        }

        return coverage

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get annotation coverage: {str(e)}"
        )


@router.get("/taxonomy-distribution")
async def get_taxonomy_distribution():
    """Get protein distribution by taxonomy"""
    if mongodb_service.proteins_collection is None:
        raise HTTPException(
            status_code=500, detail="MongoDB service is not initialized"
        )

    try:
        pipeline = [
            {"$match": {"taxonomy_id": {"$ne": None, "$ne": ""}}},
            {
                "$group": {
                    "_id": "$taxonomy_id",
                    "count": {"$sum": 1},
                    "taxonomy_name": {"$first": "$taxonomy_name"},
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 50},
        ]

        cursor = mongodb_service.proteins_collection.aggregate(pipeline)
        taxonomy_dist = await cursor.to_list(length=None)

        result = []
        for item in taxonomy_dist:
            result.append(
                {
                    "taxonomy_id": item["_id"],
                    "taxonomy_name": item.get("taxonomy_name", "Unknown"),
                    "protein_count": item["count"],
                }
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get taxonomy distribution: {str(e)}"
        )


@router.get("/domain-distribution")
async def get_domain_distribution():
    """Get domain distribution statistics"""
    try:
        from app.services.graph_service import graph_service

        distribution = await graph_service.analyze_domain_distribution()
        return distribution

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get domain distribution: {str(e)}"
        )


@router.get("/graph-connectivity")
async def get_graph_connectivity_metrics():
    """Get detailed graph connectivity metrics"""
    try:
        graph_stats = await neo4j_service.get_graph_statistics()

        connectivity = {
            "total_nodes": graph_stats.total_proteins,
            "total_edges": graph_stats.total_edges,
            "average_degree": graph_stats.average_degree,
            "clustering_coefficient": graph_stats.clustering_coefficient,
            "isolated_nodes": graph_stats.isolated_proteins,
            "connected_components": None,
            "largest_component_size": None,
            "graph_density": (2 * graph_stats.total_edges)
            / (graph_stats.total_proteins * (graph_stats.total_proteins - 1))
            if graph_stats.total_proteins > 1
            else 0,
        }

        return connectivity

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get connectivity metrics: {str(e)}"
        )
