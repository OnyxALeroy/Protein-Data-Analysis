from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.models import Protein, ProteinSearch
from app.services.mongodb_service import mongodb_service

router = APIRouter(prefix="/proteins", tags=["proteins"])


@router.get("/", response_model=List[Protein])
async def search_proteins(
    query: Optional[str] = Query(None, description="Text search query"),
    protein_id: Optional[str] = Query(None, description="Protein ID filter"),
    name: Optional[str] = Query(None, description="Protein name filter"),
    ec_number: Optional[str] = Query(None, description="EC number filter"),
    go_term: Optional[str] = Query(None, description="GO term filter"),
    taxonomy_id: Optional[str] = Query(None, description="Taxonomy ID filter"),
    status: Optional[str] = Query(None, description="Protein status filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
):
    """Search proteins with various filters"""
    try:
        search_params = ProteinSearch(
            query=query,
            protein_id=protein_id,
            name=name,
            ec_numbers=[ec_number] if ec_number else [],
            go_terms=[go_term] if go_term else [],
            taxonomy_id=taxonomy_id,
            status=status,
            limit=limit,
            offset=offset,
        )

        proteins = await mongodb_service.search_proteins(search_params)
        return proteins

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/{protein_id}", response_model=Protein)
async def get_protein(protein_id: str):
    """Get a specific protein by ID"""
    try:
        protein = await mongodb_service.get_protein_by_id(protein_id)

        if not protein:
            raise HTTPException(status_code=404, detail="Protein not found")

        return protein

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get protein: {str(e)}")


@router.post("/", response_model=dict)
async def create_protein(protein: Protein):
    """Create a new protein"""
    try:
        existing = await mongodb_service.get_protein_by_id(protein.protein_id)
        if existing:
            raise HTTPException(status_code=400, detail="Protein already exists")

        protein_id = await mongodb_service.insert_protein(protein)

        return {"message": "Protein created successfully", "protein_id": protein_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create protein: {str(e)}"
        )


@router.get("/{protein_id}/domains", response_model=List[str])
async def get_protein_domains(protein_id: str):
    """Get domains for a specific protein"""
    try:
        domains = await mongodb_service.get_protein_domains(protein_id)
        return domains

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get domains: {str(e)}")


@router.get("/{protein_id}/similar")
async def get_similar_proteins(
    protein_id: str,
    top_k: int = Query(
        10, ge=1, le=100, description="Number of similar proteins to return"
    ),
    min_similarity: float = Query(
        0.1, ge=0, le=1, description="Minimum similarity threshold"
    ),
):
    """Get proteins similar to the specified protein"""
    try:
        from app.services.graph_service import graph_service

        similar_proteins = await graph_service.find_similar_proteins(
            protein_id, top_k, min_similarity
        )

        return similar_proteins

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to find similar proteins: {str(e)}"
        )
