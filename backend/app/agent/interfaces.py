from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.domain.models import ToolRequest, ToolResult, ToolDefinition, ModelAdapterDefinition, ImageAsset

class BaseTool(ABC):
    def __init__(self, definition: ToolDefinition):
        self.definition = definition
        
    @abstractmethod
    def execute(self, request: ToolRequest, assets: List[ImageAsset]) -> ToolResult:
        """Executes the tool logic and returns a structured ToolResult."""
        pass

class BaseModelAdapter(ABC):
    def __init__(self, definition: ModelAdapterDefinition):
        self.definition = definition
        
    @abstractmethod
    def load(self):
        """Loads the model weights/connection."""
        pass
        
    @abstractmethod
    def unload(self):
        """Frees hardware resources."""
        pass
        
    @abstractmethod
    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Runs inference and returns raw predictions."""
        pass
