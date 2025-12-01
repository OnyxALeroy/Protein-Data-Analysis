from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AnnotationType(str, Enum):
    GO = "go"
    EC = "ec"
    INTERPRO = "interpro"


class ProteinStatus(str, Enum):
    REVIEWED = "reviewed"
    UNREVIEWED = "unreviewed"


class Domain(BaseModel):
    domain_id: str
    domain_name: Optional[str] = None
    domain_type: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None


class Annotation(BaseModel):
    annotation_type: AnnotationType
    annotation_value: str
    description: Optional[str] = None
    evidence: Optional[str] = None


class Protein(BaseModel):
    protein_id: str = Field(..., description="Unique protein identifier")
    name: Optional[str] = None
    description: Optional[str] = None
    sequence: Optional[str] = None
    length: Optional[int] = None
    taxonomy_id: Optional[str] = None
    taxonomy_name: Optional[str] = None
    status: ProteinStatus = ProteinStatus.UNREVIEWED
    ec_numbers: List[str] = Field(default_factory=list)
    go_terms: List[str] = Field(default_factory=list)
    domains: List[Domain] = Field(default_factory=list)
    annotations: List[Annotation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ProteinSearch(BaseModel):
    query: Optional[str] = None
    protein_id: Optional[str] = None
    name: Optional[str] = None
    ec_numbers: List[str] = Field(default_factory=list)
    go_terms: List[str] = Field(default_factory=list)
    taxonomy_id: Optional[str] = None
    status: Optional[ProteinStatus] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class GraphEdge(BaseModel):
    source_protein_id: str
    target_protein_id: str
    weight: float = Field(..., ge=0, le=1)
    shared_domains: List[str] = Field(default_factory=list)
    jaccard_similarity: float = Field(..., ge=0, le=1)


class GraphNode(BaseModel):
    protein_id: str
    name: Optional[str] = None
    status: ProteinStatus
    ec_numbers: List[str] = Field(default_factory=list)
    go_terms: List[str] = Field(default_factory=list)
    domain_count: int = 0
    neighbor_count: int = 0


class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class GraphStats(BaseModel):
    total_proteins: int
    reviewed_proteins: int
    unreviewed_proteins: int
    isolated_proteins: int
    total_edges: int
    average_degree: float
    clustering_coefficient: Optional[float] = None


class LabelPropagationRequest(BaseModel):
    attribute: str = Field(..., description="Attribute to propagate: 'ec' or 'go'")
    max_iterations: int = Field(default=100, ge=1, le=1000)
    threshold: float = Field(default=0.01, ge=0.0001, le=1.0)
    min_similarity: float = Field(default=0.1, ge=0, le=1)


class LabelPropagationResult(BaseModel):
    iterations_completed: int
    converged: bool
    annotated_proteins: int
    confidence_scores: Dict[str, float]
    predicted_labels: Dict[str, List[str]]
