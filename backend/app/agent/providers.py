import json
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.domain.models import AgentExecutionPlan, AgentPlanStep, ToolDefinition, ToolResult

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_plan(self, query: str, context: str, available_tools: List[ToolDefinition]) -> AgentExecutionPlan:
        pass
        
    @abstractmethod
    def synthesize_answer(self, query: str, tool_results: List[ToolResult]) -> str:
        pass

class DummyLLMProvider(BaseLLMProvider):
    """
    Deterministic provider for testing without API keys.
    """
    def __init__(self, predefined_plan: AgentExecutionPlan = None, predefined_answer: str = None):
        self.predefined_plan = predefined_plan or AgentExecutionPlan(
            intent="Test Plan", steps=[]
        )
        self.predefined_answer = predefined_answer or "Test answer"
        
    def generate_plan(self, query: str, context: str, available_tools: List[ToolDefinition]) -> AgentExecutionPlan:
        return self.predefined_plan
        
    def synthesize_answer(self, query: str, tool_results: List[ToolResult]) -> str:
        return self.predefined_answer

class GeminiProvider(BaseLLMProvider):
    """
    Integration for Google Gemini via structured prompt.
    Requires GEMINI_API_KEY environment variable.
    """
    def __init__(self, model_name="gemini-pro"):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        
    def generate_plan(self, query: str, context: str, available_tools: List[ToolDefinition]) -> AgentExecutionPlan:
        if not self.api_key:
            # Fallback for testing environments without keys
            raise RuntimeError("GEMINI_API_KEY is not configured.")
            
        # In a real environment with google-genai, we would use structured generation here.
        # e.g., model.generate_content(prompt, response_schema=AgentExecutionPlan)
        # For now, we simulate the interface.
        raise NotImplementedError("Live Gemini integration requires SDK installation.")

    def synthesize_answer(self, query: str, tool_results: List[ToolResult]) -> str:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
            
        raise NotImplementedError("Live Gemini integration requires SDK installation.")
