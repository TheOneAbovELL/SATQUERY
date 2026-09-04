from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.domain.models import AnalysisRequest, AnalysisResult, BoundingBox
from app.agent.registry import ToolRegistry
from app.agent.execution import ToolExecutionService
from app.agent.orchestrator import SatQueryAgent
from app.agent.providers import DummyLLMProvider, AgentExecutionPlan, AgentPlanStep
from app.analytics.tools import NdviTool, AreaTool

router = APIRouter()

# Dependency injection for the agent
def get_satquery_agent():
    registry = ToolRegistry()
    registry.register(NdviTool())
    registry.register(AreaTool())
    
    execution_service = ToolExecutionService(registry)
    
    # In a real environment, we would inject GeminiProvider here
    # For now, we use a simple DummyLLMProvider that maps requests statically
    llm_provider = DummyLLMProvider(
        predefined_plan=AgentExecutionPlan(
            intent="Calculated requested metrics",
            steps=[AgentPlanStep(tool_id="ndvi_calculator", input_asset_ids=["mock_1"], purpose="extract NDVI")]
        ),
        predefined_answer="The mean NDVI value calculated by the tool is provided in the metrics."
    )
    
    return SatQueryAgent(execution_service, llm_provider)

class AnalyzePayload(BaseModel):
    query: str
    asset_ids: List[str]
    roi: Optional[BoundingBox] = None

@router.post("/analyze", response_model=AnalysisResult)
def analyze(payload: AnalyzePayload, agent: SatQueryAgent = Depends(get_satquery_agent)):
    """
    Primary endpoint for natural language analysis queries.
    """
    request = AnalysisRequest(
        query=payload.query,
        input_asset_ids=payload.asset_ids,
        roi=payload.roi,
        session_context="session_123"
    )
    
    # In a real pipeline, we'd fetch the ImageAssets from DB using asset_ids.
    # Passing an empty list here will trigger input validation failures 
    # if the tool requires assets (which proves the execution boundary works).
    loaded_assets = [] 
    
    result = agent.process_request(request, loaded_assets)
    return result
