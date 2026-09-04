import pytest
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from app.domain.models import (
    AnalysisRequest, ToolRequest, ImageAsset, AgentExecutionPlan, AgentPlanStep
)
from app.agent.registry import ToolRegistry
from app.agent.execution import ToolExecutionService
from app.agent.orchestrator import SatQueryAgent
from app.agent.providers import DummyLLMProvider
from app.analytics.tools import NdviTool, AreaTool
from app.analytics.models import DummySceneClassifierAdapter, SceneClassificationTool
from app.services.validator import InputValidator


def create_test_raster(path, bands=4):
    transform = from_bounds(0, 0, 1000, 1000, 100, 100)
    with rasterio.open(
        path, 'w', driver='GTiff', height=100, width=100, count=bands,
        dtype=rasterio.uint8, crs='EPSG:32633', transform=transform
    ) as dst:
        for i in range(1, bands + 1):
            dst.write(np.ones((100, 100), dtype=np.uint8) * (i * 10), i)


@pytest.fixture
def agent_env(tmp_path):
    """Sets up a full agent environment with registry, tools, and a test raster."""
    registry = ToolRegistry()
    registry.register(NdviTool())
    registry.register(AreaTool())
    adapter = DummySceneClassifierAdapter()
    registry.register(SceneClassificationTool(adapter))

    service = ToolExecutionService(registry)

    raster_path = str(tmp_path / "test_ms.tif")
    create_test_raster(raster_path, 4)

    val = InputValidator()
    r = val.validate(raster_path)
    r["capabilities"]["can_ndvi"] = True
    r["band_semantics"] = {1: "BLUE", 2: "GREEN", 3: "RED", 4: "NIR"}
    asset = ImageAsset(
        asset_id="asset_1", filename="test_ms.tif",
        mime_type="image/tiff", storage_location=raster_path, **r
    )

    return service, asset


# ── Test 1: Successful NDVI through agent ────────────────────────────────────

def test_agent_ndvi_success(agent_env):
    service, asset = agent_env

    plan = AgentExecutionPlan(
        intent="Calculate NDVI",
        steps=[AgentPlanStep(
            tool_id="ndvi_calculator",
            input_asset_ids=["asset_1"],
            purpose="Calculate vegetation index"
        )]
    )
    provider = DummyLLMProvider(
        predefined_plan=plan,
        predefined_answer="The mean NDVI is {mean_ndvi}."
    )
    agent = SatQueryAgent(service, provider)

    request = AnalysisRequest(
        query="Calculate NDVI for this image.",
        input_asset_ids=["asset_1"],
        session_context="sess_1"
    )
    result = agent.process_request(request, [asset])

    assert result.status == "SUCCESS"
    assert "mean_ndvi" in result.metrics
    assert result.task == "Calculate NDVI"


# ── Test 2: Hallucinated tool rejection ──────────────────────────────────────

def test_agent_hallucinated_tool_rejection(agent_env):
    service, asset = agent_env

    plan = AgentExecutionPlan(
        intent="Fake task",
        steps=[AgentPlanStep(
            tool_id="nonexistent_magic_tool",
            input_asset_ids=["asset_1"],
            purpose="Do something impossible"
        )]
    )
    provider = DummyLLMProvider(predefined_plan=plan)
    agent = SatQueryAgent(service, provider)

    request = AnalysisRequest(
        query="Do magic.", input_asset_ids=["asset_1"], session_context="sess_2"
    )
    result = agent.process_request(request, [asset])

    assert result.status == "FAILED"


# ── Test 3: Capability rejection (NDVI on grayscale) ─────────────────────────

def test_agent_capability_rejection(agent_env, tmp_path):
    service, _ = agent_env

    # Create a 1-band raster (no NDVI capability)
    gray_path = str(tmp_path / "gray.tif")
    create_test_raster(gray_path, 1)
    val = InputValidator()
    r = val.validate(gray_path)
    gray_asset = ImageAsset(
        asset_id="asset_gray", filename="gray.tif",
        mime_type="image/tiff", storage_location=gray_path, **r
    )

    plan = AgentExecutionPlan(
        intent="Calculate NDVI",
        steps=[AgentPlanStep(
            tool_id="ndvi_calculator",
            input_asset_ids=["asset_gray"],
            purpose="Calculate NDVI"
        )]
    )
    provider = DummyLLMProvider(predefined_plan=plan)
    agent = SatQueryAgent(service, provider)

    request = AnalysisRequest(
        query="Calculate NDVI.", input_asset_ids=["asset_gray"], session_context="sess_3"
    )
    result = agent.process_request(request, [gray_asset])

    assert result.status == "PARTIAL_FAILURE"


# ── Test 4: Multi-step plan ──────────────────────────────────────────────────

def test_agent_multi_step_plan(agent_env):
    service, asset = agent_env

    plan = AgentExecutionPlan(
        intent="NDVI then Area",
        steps=[
            AgentPlanStep(tool_id="ndvi_calculator", input_asset_ids=["asset_1"], purpose="Get NDVI"),
            AgentPlanStep(tool_id="area_calculator", input_asset_ids=["asset_1"], purpose="Get area"),
        ]
    )
    provider = DummyLLMProvider(
        predefined_plan=plan,
        predefined_answer="NDVI and area computed."
    )
    agent = SatQueryAgent(service, provider)

    request = AnalysisRequest(
        query="Calculate NDVI and total area.",
        input_asset_ids=["asset_1"],
        session_context="sess_4"
    )
    result = agent.process_request(request, [asset])

    assert result.status == "SUCCESS"
    assert "mean_ndvi" in result.metrics
    assert "total_area" in result.metrics


# ── Test 5: Empty plan ───────────────────────────────────────────────────────

def test_agent_empty_plan(agent_env):
    service, asset = agent_env

    plan = AgentExecutionPlan(intent="Nothing to do", steps=[])
    provider = DummyLLMProvider(predefined_plan=plan, predefined_answer="No tools needed.")
    agent = SatQueryAgent(service, provider)

    request = AnalysisRequest(
        query="Hello", input_asset_ids=[], session_context="sess_5"
    )
    result = agent.process_request(request, [])

    assert result.status == "SUCCESS"
    assert result.summary == "No tools needed."


# ── Test 6: Test adapter clearly labelled ────────────────────────────────────

def test_agent_test_adapter_labeled(agent_env):
    service, asset = agent_env

    plan = AgentExecutionPlan(
        intent="Scene classification",
        steps=[AgentPlanStep(
            tool_id="scene_classifier",
            input_asset_ids=["asset_1"],
            purpose="Classify scene"
        )]
    )
    provider = DummyLLMProvider(predefined_plan=plan, predefined_answer="Scene classified.")
    agent = SatQueryAgent(service, provider)

    request = AnalysisRequest(
        query="What is in this image?", input_asset_ids=["asset_1"], session_context="sess_6"
    )
    result = agent.process_request(request, [asset])

    assert result.status == "SUCCESS"
    # Verify the tool is clearly labelled as a test adapter
    ndvi_tool_def = service.registry.get_tool("scene_classifier").definition
    assert "TEST ADAPTER" in ndvi_tool_def.name

@pytest.mark.skip(reason="Requires full 4.5GB weights and ~6GB RAM. Run manually via python scripts/test_qwen.py")
def test_agent_live_qwen2vl(agent_env):
    service, asset = agent_env
    
    from app.analytics.models import Qwen2VLAdapter
    from app.analytics.tools import Qwen2VLTool
    
    qwen_adapter = Qwen2VLAdapter()
    qwen_tool = Qwen2VLTool(qwen_adapter)
    
    service.registry.register(qwen_tool)
    
    plan = AgentExecutionPlan(
        intent="Visual understanding",
        steps=[AgentPlanStep(
            tool_id="visual_language_specialist",
            input_asset_ids=["asset_1"],
            purpose="Describe the image",
            parameters={"query": "What objects or land-cover features are visible in this image?"}
        )]
    )
    provider = DummyLLMProvider(predefined_plan=plan, predefined_answer="Real VLM inference complete.")
    agent = SatQueryAgent(service, provider)

    request = AnalysisRequest(
        query="What is visible in this image?", input_asset_ids=["asset_1"], session_context="sess_live"
    )
    
    # This will trigger the actual Qwen2VLAdapter.load() and predict()
    result = agent.process_request(request, [asset])
    
    assert result.status == "SUCCESS"
    assert "visual_language_specialist" in [t.tool_id for t in result.execution_trace if t.stage == "TOOL_EXECUTION"]
