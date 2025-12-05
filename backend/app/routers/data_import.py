import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.data_import_service import data_import_service

router = APIRouter(prefix="/import", tags=["data-import"])


@router.post("/proteins")
async def import_proteins(
    file: UploadFile = File(...),
    data_format: str = Form("uniprot"),
    batch_size: int = Form(100),
):
    """Import protein data from uploaded file"""
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No file uploaded")

    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file.filename).suffix
        ) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            result = await data_import_service.import_protein_data(
                tmp_file_path, data_format
            )
            return result
        finally:
            os.unlink(tmp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/domains")
async def import_domains(file: UploadFile = File(...)):
    """Import domain annotations from protein2ipr format"""
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No file uploaded")

    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file.filename).suffix
        ) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            result = await data_import_service.import_domain_annotations(tmp_file_path)
            return result
        finally:
            os.unlink(tmp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Domain import failed: {str(e)}")


@router.post("/go-annotations")
async def import_go_annotations(file: UploadFile = File(...)):
    """Import GO annotations from GAF format"""
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No file uploaded")

    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file.filename).suffix
        ) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            result = await data_import_service.import_go_annotations(tmp_file_path)
            return result
        finally:
            os.unlink(tmp_file_path)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"GO annotation import failed: {str(e)}"
        )


@router.post("/generate-sample")
async def generate_sample_data(num_proteins: int = 1000):
    """Generate sample protein data for testing"""
    try:
        result = await data_import_service.generate_sample_data(num_proteins)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Sample data generation failed: {str(e)}"
        )


@router.get("/formats")
async def get_supported_formats():
    """Get supported data import formats"""
    return {
        "protein_formats": {
            "uniprot": {
                "description": "UniProt-like CSV/TSV format",
                "required_columns": ["protein_id", "name"],
                "optional_columns": [
                    "description",
                    "sequence",
                    "length",
                    "taxonomy_id",
                    "taxonomy_name",
                    "status",
                    "ec_numbers",
                    "go_terms",
                    "domains",
                ],
            },
            "custom": {
                "description": "Custom text format with headers",
                "format": ">protein_id|name\nEC:1.1.1.1;2.2.2.2\nGO:GO:0008150;GO:0003674\nDomains:IPR000123;IPR000456\nSequence:ACDEFGHIK...",
            },
        },
        "annotation_formats": {
            "domains": {
                "description": "protein2ipr format (tab-separated)",
                "columns": ["protein_id", "domain_id", "domain_name", ...],
            },
            "go_annotations": {
                "description": "GAF format (Gene Ontology Annotation)",
                "format": "Standard GAF 2.0 format",
            },
        },
    }
