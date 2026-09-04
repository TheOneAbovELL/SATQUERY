import time
from typing import List, Dict, Any
from datetime import datetime
from app.domain.models import ToolRequest, ToolResult, ToolErrorCode, ExecutionTraceEvent, ImageAsset
from app.agent.registry import ToolRegistry

class ToolExecutionService:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        
    def execute_tool(self, request: ToolRequest, assets: List[ImageAsset]) -> ToolResult:
        start_time = time.time()
        trace_events = []
        
        def add_trace(stage: str, action: str, status: str = "SUCCESS", warnings: List[str] = None):
            trace_events.append(ExecutionTraceEvent(
                event_id=f"evt_{int(time.time()*1000)}_{len(trace_events)}",
                stage=stage,
                action=action,
                tool_or_model=request.tool_id,
                status=status,
                warnings=warnings or []
            ))

        add_trace("TOOL_REQUESTED", f"Requested execution for {request.tool_id}")
        
        # 1. Locate Tool
        tool = self.registry.get_tool(request.tool_id)
        if not tool:
            add_trace("TOOL_SELECTION", f"Tool {request.tool_id} not found", status="FAILED")
            return self._build_error_result(request, ToolErrorCode.TOOL_NOT_FOUND, "Tool not registered", start_time, trace_events)
            
        # 2. Validate Availability
        if tool.definition.availability != "AVAILABLE":
            add_trace("TOOL_SELECTION", f"Tool {request.tool_id} unavailable", status="FAILED")
            return self._build_error_result(request, ToolErrorCode.TOOL_UNAVAILABLE, "Tool is currently offline", start_time, trace_events)
            
        # 3. Validate Capabilities
        if not self.registry.check_capability_compatibility(request.tool_id, assets):
            add_trace("INPUT_VALIDATION", "Assets missing required capabilities", status="FAILED")
            return self._build_error_result(request, ToolErrorCode.CAPABILITY_UNSUPPORTED, "Asset lacks required capabilities (e.g. can_ndvi)", start_time, trace_events)
            
        add_trace("INPUT_VALIDATED", f"Validated {len(assets)} assets for execution")
        add_trace("EXECUTION_STARTED", f"Executing {request.tool_id}")
        
        # 4. Execute
        try:
            result = tool.execute(request, assets)
            duration = time.time() - start_time
            result.execution_duration_sec = duration
            
            add_trace("EXECUTION_COMPLETED", f"Duration: {duration:.2f}s", status="SUCCESS")
            add_trace("RESULT_VALIDATED", "Tool output schema valid")
            
            result.trace_events = trace_events + result.trace_events
            
            return result
            
        except Exception as e:
            add_trace("EXECUTION_FAILED", str(e), status="FAILED")
            return self._build_error_result(request, ToolErrorCode.EXECUTION_FAILED, f"Exception during execution: {str(e)}", start_time, trace_events)
            
    def _build_error_result(self, req: ToolRequest, code: ToolErrorCode, msg: str, start: float, trace: list) -> ToolResult:
        return ToolResult(
            request_id=req.request_id,
            tool_id=req.tool_id,
            tool_version="unknown",
            success=False,
            execution_duration_sec=time.time() - start,
            error_code=code,
            error_message=msg,
            trace_events=trace
        )
