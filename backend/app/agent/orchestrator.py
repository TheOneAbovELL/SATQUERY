from typing import List, Dict, Any
import uuid
from app.domain.models import AnalysisRequest, AnalysisResult, ToolRequest, ImageAsset, ToolResult
from app.agent.execution import ToolExecutionService
from app.agent.registry import ToolRegistry
from app.agent.providers import BaseLLMProvider

class SatQueryAgent:
    """
    Dynamic orchestrator using LLM to generate plans and synthesize answers.
    """
    def __init__(self, execution_service: ToolExecutionService, llm_provider: BaseLLMProvider):
        self.execution_service = execution_service
        self.llm_provider = llm_provider
        
    def process_request(self, request: AnalysisRequest, loaded_assets: List[ImageAsset]) -> AnalysisResult:
        # 1. Fetch available tools
        available_tools = self.execution_service.registry.list_tools()
        
        # 2. Get Structured Plan
        context = request.session_context
        try:
            plan = self.llm_provider.generate_plan(request.query, context, available_tools)
        except Exception as e:
            return AnalysisResult(
                analysis_id=str(uuid.uuid4()),
                task="Plan Generation Failed",
                status="FAILED",
                summary=f"Agent could not generate plan: {str(e)}"
            )

        # 3. Execute Plan
        all_traces = []
        final_metrics = {}
        tool_results = []
        status = "SUCCESS"
        
        for step in plan.steps:
            # Plan Validation
            tool = self.execution_service.registry.get_tool(step.tool_id)
            if not tool:
                status = "FAILED"
                break
                
            tool_req = ToolRequest(
                request_id=str(uuid.uuid4()),
                analysis_id=request.session_context,
                tool_id=step.tool_id,
                input_asset_ids=step.input_asset_ids,
                parameters=step.parameters,
                execution_context={"agent_orchestrated": True}
            )
            
            tool_res = self.execution_service.execute_tool(tool_req, loaded_assets)
            
            all_traces.extend(tool_res.trace_events)
            tool_results.append(tool_res)
            
            if not tool_res.success:
                status = "PARTIAL_FAILURE"
                break # Stop sequential execution on failure
                
            final_metrics.update(tool_res.metrics)
            
        # 4. Synthesize Answer
        try:
            final_summary = self.llm_provider.synthesize_answer(request.query, tool_results)
        except Exception as e:
            final_summary = f"Synthesizer error: {str(e)}. Raw results available in metrics."
            if status == "SUCCESS":
                status = "PARTIAL_FAILURE"

        return AnalysisResult(
            analysis_id=request.session_context,
            task=plan.intent,
            status=status,
            summary=final_summary,
            metrics=final_metrics,
            claims=[f"Executed tools: {[t.tool_id for t in tool_results]}"],
            execution_trace=all_traces
        )
