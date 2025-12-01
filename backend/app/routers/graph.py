from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.models import GraphData, GraphNode
from app.services.neo4j_service import neo4j_service

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/search", response_model=List[GraphNode])
async def search_graph_proteins(
    query: str = Query(..., description="Search query for protein names or IDs"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
):
    """Search proteins in the graph database"""
    try:
        proteins = await neo4j_service.search_proteins(query, limit)
        return proteins

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph search failed: {str(e)}")


@router.get("/{protein_id}/neighbors", response_model=GraphData)
async def get_protein_neighborhood(
    protein_id: str,
    depth: int = Query(1, ge=1, le=3, description="Neighborhood depth (1-3)"),
):
    """Get protein and its neighbors in the graph"""
    try:
        graph_data = await neo4j_service.get_protein_neighbors(protein_id, depth)

        if not graph_data.nodes:
            raise HTTPException(status_code=404, detail="Protein not found in graph")

        return graph_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get neighborhood: {str(e)}"
        )


@router.post("/build")
async def build_protein_graph(
    min_similarity: float = Query(
        0.1, ge=0, le=1, description="Minimum Jaccard similarity"
    ),
    max_proteins: Optional[int] = Query(
        None, ge=1, description="Maximum number of proteins to process"
    ),
):
    """Build the protein similarity graph"""
    try:
        from app.services.graph_service import graph_service

        await graph_service.build_protein_graph(min_similarity, max_proteins)

        return {"message": "Protein graph built successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build graph: {str(e)}")


@router.get("/statistics")
async def get_graph_statistics():
    """Get comprehensive graph statistics"""
    try:
        stats = await neo4j_service.get_graph_statistics()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        )


@router.delete("/clear")
async def clear_graph():
    """Clear all nodes and edges from the graph"""
    try:
        await neo4j_service.clear_database()
        return {"message": "Graph cleared successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear graph: {str(e)}")


@router.get("/domain-analysis")
async def analyze_domain_distribution():
    """Analyze domain distribution across proteins"""
    try:
        from app.services.graph_service import graph_service

        analysis = await graph_service.analyze_domain_distribution()
        return analysis

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze domains: {str(e)}"
        )


@router.get("/{protein_id}/similarity-matrix")
async def get_similarity_matrix(
    protein_id: str,
    additional_proteins: List[str] = Query(
        [], description="Additional protein IDs for comparison"
    ),
):
    """Get similarity matrix for specified proteins"""
    try:
        from app.services.graph_service import graph_service

        protein_ids = [protein_id] + additional_proteins
        similarity_matrix = await graph_service.get_protein_similarity_matrix(
            protein_ids
        )

        return similarity_matrix

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to compute similarity matrix: {str(e)}"
        )
