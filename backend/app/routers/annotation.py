from fastapi import APIRouter, HTTPException

from app.models import LabelPropagationRequest, LabelPropagationResult
from app.services.label_propagation_service import label_propagation_service

router = APIRouter(prefix="/annotation", tags=["annotation"])


@router.post("/propagate", response_model=LabelPropagationResult)
async def propagate_labels(request: LabelPropagationRequest):
    """Perform label propagation for protein function annotation"""
    try:
        result = await label_propagation_service.propagate_labels(request)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Label propagation failed: {str(e)}"
        )


@router.get("/evaluate/{attribute}")
async def evaluate_propagation_quality(attribute: str):
    """Evaluate the quality of label propagation for a specific attribute"""
    try:
        if attribute not in ["ec", "go"]:
            raise HTTPException(
                status_code=400, detail="Attribute must be 'ec' or 'go'"
            )

        evaluation = await label_propagation_service.evaluate_propagation_quality(
            attribute
        )
        return evaluation

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get("/statistics/{attribute}")
async def get_propagation_statistics(attribute: str):
    """Get label propagation statistics for a specific attribute"""
    try:
        if attribute not in ["ec", "go"]:
            raise HTTPException(
                status_code=400, detail="Attribute must be 'ec' or 'go'"
            )

        stats = await label_propagation_service.get_propagation_statistics(attribute)
        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/overview")
async def get_annotation_overview():
    """Get overview of annotation status for both EC and GO"""
    try:
        ec_stats = await label_propagation_service.get_propagation_statistics("ec")
        go_stats = await label_propagation_service.get_propagation_statistics("go")

        overview = {
            "ec_annotations": ec_stats,
            "go_annotations": go_stats,
            "summary": {
                "total_proteins": ec_stats["total_proteins"],
                "ec_annotated": ec_stats["annotated_proteins"],
                "go_annotated": go_stats["annotated_proteins"],
                "both_annotated": None,
                "either_annotated": None,
                "neither_annotated": None,
            },
        }

        return overview

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}")
