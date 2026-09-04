from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime

class AssetFormat(str, Enum):
    GEOTIFF = "GeoTIFF"
    TIFF = "TIFF"
    PNG = "PNG"
    JPEG = "JPEG"
    UNKNOWN = "UNKNOWN"

class AssetModality(str, Enum):
    OPTICAL = "Optical"
    MULTISPECTRAL = "Multispectral"
    SAR = "SAR"
    GRAYSCALE = "Grayscale"
    RGB = "RGB"
    UNKNOWN = "UNKNOWN"

class BoundingBox(BaseModel):
    min_x: float
    min_y: float
    max_x: float
    max_y: float

class ImageAsset(BaseModel):
    asset_id: str
    filename: str
    mime_type: str
    format: AssetFormat = AssetFormat.UNKNOWN
    dimensions: Optional[tuple[int, int]] = None
    band_count: Optional[int] = None
    modality: AssetModality = AssetModality.UNKNOWN
    sensor: Optional[str] = None
    acquisition_time: Optional[datetime] = None
    crs: Optional[str] = None
    geospatial_bounds: Optional[BoundingBox] = None
    transform: Optional[List[float]] = None # 6-element affine transform
    pixel_resolution: Optional[tuple[float, float]] = None
    band_semantics: Dict[int, str] = Field(default_factory=dict)
    capabilities: Dict[str, bool] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    storage_location: str
    validation_state: str = "PENDING"
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

class RelationshipType(str, Enum):
    SINGLE = "SINGLE"
    TEMPORAL_PAIR = "TEMPORAL_PAIR"
    CROSS_MODAL_PAIR = "CROSS_MODAL_PAIR"
    SPATIALLY_OVERLAPPING = "SPATIALLY_OVERLAPPING"
    PARTIALLY_OVERLAPPING = "PARTIALLY_OVERLAPPING"
    NON_OVERLAPPING = "NON_OVERLAPPING"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"

class AlignmentStatus(str, Enum):
    ALIGNED = "ALIGNED"
    ALIGNABLE = "ALIGNABLE"
    REQUIRES_REGISTRATION = "REQUIRES_REGISTRATION"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"

class ImageRelationshipAssessment(BaseModel):
    relationship_types: List[RelationshipType]
    alignment_status: AlignmentStatus
    overlap_percentage_a: float = 0.0
    overlap_percentage_b: float = 0.0
    intersection_bounds_wgs84: Optional[BoundingBox] = None
    is_temporally_distinct: bool = False
    is_cross_modal: bool = False
    notes: List[str] = Field(default_factory=list)

class AnalysisSession(BaseModel):
    session_id: str
    uploaded_assets: List[str] = Field(default_factory=list)
    active_images: List[str] = Field(default_factory=list)
    active_region_of_interest: Optional[BoundingBox] = None
    previous_results: List[str] = Field(default_factory=list)
    execution_history: List[str] = Field(default_factory=list)

class AnalysisRequest(BaseModel):
    query: str
    input_asset_ids: List[str]
    requested_task: Optional[str] = None
    roi: Optional[BoundingBox] = None
    session_context: str

class ToolDefinition(BaseModel):
    tool_id: str
    name: str
    description: str
    task_capabilities: List[str]
    accepted_modalities: List[AssetModality]
    required_capabilities: List[str] = Field(default_factory=list)
    output_schema: Dict[str, Any]
    hardware_requirements: str = "CPU"
    availability: str = "AVAILABLE"
    version: str

class ExecutionTraceEvent(BaseModel):
    event_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stage: str
    action: str
    tool_or_model: Optional[str] = None
    status: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)

class AnalysisResult(BaseModel):
    analysis_id: str
    task: str
    status: str = "SUCCESS"
    summary: str
    claims: List[str] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)
    spatial_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    visual_evidence: List[str] = Field(default_factory=list)
    model_evidence: List[str] = Field(default_factory=list)
    provenance: List[str] = Field(default_factory=list)
    confidence: Dict[str, float] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    execution_trace: List[ExecutionTraceEvent] = Field(default_factory=list)

class Artifact(BaseModel):
    artifact_id: str
    type: str
    source_analysis: str
    source_inputs: List[str]
    storage_reference: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    creation_timestamp: datetime = Field(default_factory=datetime.utcnow)

class ToolErrorCode(str, Enum):
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_UNAVAILABLE = "TOOL_UNAVAILABLE"
    INPUT_INVALID = "INPUT_INVALID"
    CAPABILITY_UNSUPPORTED = "CAPABILITY_UNSUPPORTED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    TIMEOUT = "TIMEOUT"
    OUTPUT_INVALID = "OUTPUT_INVALID"
    ARTIFACT_FAILURE = "ARTIFACT_FAILURE"
    NO_SPATIAL_OVERLAP = "NO_SPATIAL_OVERLAP"
    INSUFFICIENT_VALID_DATA = "INSUFFICIENT_VALID_DATA"
    CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
    NONE = "NONE"

class ToolRequest(BaseModel):
    request_id: str
    analysis_id: str
    tool_id: str
    input_asset_ids: List[str]
    roi: Optional[BoundingBox] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requested_outputs: List[str] = Field(default_factory=list)
    execution_context: Dict[str, Any] = Field(default_factory=dict)

class ToolResult(BaseModel):
    request_id: str
    tool_id: str
    tool_version: str
    success: bool
    execution_duration_sec: float
    outputs: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)
    spatial_artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    visual_artifacts: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    error_code: ToolErrorCode = ToolErrorCode.NONE
    error_message: Optional[str] = None
    confidence: Dict[str, float] = Field(default_factory=dict)
    provenance: List[str] = Field(default_factory=list)
    trace_events: List[ExecutionTraceEvent] = Field(default_factory=list)

class ModelAdapterDefinition(BaseModel):
    model_id: str
    model_version: str
    task: str
    modality: AssetModality
    input_requirements: Dict[str, Any]
    preprocessing_requirements: Dict[str, Any]
    output_type: str
    hardware_requirements: str
    parameter_count: Optional[str] = None
    quantization: Optional[str] = None
    memory_estimate: Optional[str] = None
    license: Optional[str] = None
    source: Optional[str] = None
    inference_method: str
    availability: str

class AgentPlanStep(BaseModel):
    tool_id: str
    input_asset_ids: List[str]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    purpose: str

class AgentExecutionPlan(BaseModel):
    intent: str
    steps: List[AgentPlanStep]

class EvidenceRelationship(str, Enum):
    AGREEMENT = "AGREEMENT"
    DISAGREEMENT = "DISAGREEMENT"
    COMPLEMENTARY = "COMPLEMENTARY"
    INCONCLUSIVE = "INCONCLUSIVE"
    FUSION_UNAVAILABLE = "FUSION_UNAVAILABLE"

class EvidenceQuality(BaseModel):
    spatial_overlap_quality: str
    temporal_consistency: str
    data_validity: str
    score_components: Dict[str, float] = {}

class EvidenceItem(BaseModel):
    modality: AssetModality
    observation: str
    metrics: Dict[str, Any]
    spatial_artifacts: List[Dict[str, Any]] = []
    source_tool: str
    provenance: List[str]
