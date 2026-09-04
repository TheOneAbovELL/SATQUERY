# System Architecture

## Component Separation
1. **Web / UI Layer (Next.js)** — Presentation, map, user input. No inference or raster math.
2. **API / Session Layer (FastAPI)** — Pydantic contracts. `POST /analyze` endpoint.
3. **SatQuery Agent** — Receives natural-language query + asset metadata. Uses an LLM Provider to generate a structured `AgentExecutionPlan`, validates it, executes it via the ToolExecutionService, and synthesizes a final grounded answer.
4. **LLM Provider Abstraction** — `BaseLLMProvider` → `DummyLLMProvider` (testing) / `GeminiProvider` (production). Swappable without touching the agent.
5. **Tool Execution Service** — Validates tool availability, checks asset capabilities, records execution trace, handles errors, returns structured `ToolResult`.
6. **Specialist Tools (BaseTool)** — `NdviTool`, `AreaTool`, `SceneClassificationTool`. Each has a `ToolDefinition` with `required_capabilities`.
7. **Model Adapter (BaseModelAdapter)** — Hides PyTorch/ONNX/API details. `DummySceneClassifierAdapter` (test), `Moondream2Adapter` (first real VLM path, pending weights download).
8. **Deterministic Analytics Engine** — NumPy/Rasterio math for NDVI, area. Cannot be bypassed by the LLM.

## Full Pipeline

```
USER QUERY
    ↓
SATQUERY AGENT
    ↓
LLM PROVIDER (generate_plan)
    ↓
STRUCTURED PLAN (AgentExecutionPlan)
    ↓
PLAN VALIDATOR (tool exists? capabilities match?)
    ↓
TOOL EXECUTION SERVICE
    ↓
SPECIALIST / ANALYTICS (BaseTool.execute)
    ↓
TOOL RESULTS (ToolResult)
    ↓
LLM PROVIDER (synthesize_answer)
    ↓
FINAL RESULT (AnalysisResult + evidence + trace)
```

## Security Boundary
- LLM output is **untrusted input**. Tool IDs, asset IDs, and parameters are validated against the registry before execution.
- The LLM cannot execute arbitrary Python, access the filesystem, or invent tool IDs.
- Hallucinated tools are rejected with `TOOL_NOT_FOUND`.
- Capability mismatches are rejected with `CAPABILITY_UNSUPPORTED`.

## Key Distinction
- **Tool ≠ Model.** A Tool is an executable capability. A ModelAdapter is a specific implementation of an ML network. Deterministic analytics (numpy) are just another implementation type.
- The agent **selects** tools. The ToolExecutionService **governs** execution. The specialist **performs** computation.

## Data Contracts
See `backend/app/domain/models.py` for all Pydantic models:
`ImageAsset`, `ToolRequest`, `ToolResult`, `AgentExecutionPlan`, `AgentPlanStep`, `AnalysisResult`, `ExecutionTraceEvent`, `ToolErrorCode`, etc.
