from typing import Dict, List, Optional
from app.domain.models import ToolDefinition, ImageAsset
from app.agent.interfaces import BaseTool

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        
    def register(self, tool: BaseTool):
        self.tools[tool.definition.tool_id] = tool
        
    def unregister(self, tool_id: str):
        if tool_id in self.tools:
            del self.tools[tool_id]
            
    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        return self.tools.get(tool_id)
        
    def list_tools(self) -> List[ToolDefinition]:
        return [tool.definition for tool in self.tools.values()]
        
    def find_compatible_tools(self, task: str) -> List[ToolDefinition]:
        return [t.definition for t in self.tools.values() if task in t.definition.task_capabilities]
        
    def check_capability_compatibility(self, tool_id: str, assets: List[ImageAsset]) -> bool:
        tool = self.get_tool(tool_id)
        if not tool:
            return False
            
        required = tool.definition.required_capabilities
        
        for asset in assets:
            for cap in required:
                if not asset.capabilities.get(cap, False):
                    return False
        return True
