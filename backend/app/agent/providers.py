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
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        import google.generativeai as genai
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_plan(self, query: str, context: str, available_tools: List[ToolDefinition]) -> AgentExecutionPlan:
        tool_descriptions = "\n".join(
            f"- tool_id: {t.tool_id} | {t.description} | capabilities: {t.task_capabilities}"
            for t in available_tools
        )
        
        prompt = f"""You are SatQuery, a geospatial AI analyst. Given a user query and a set of available tools, produce a JSON execution plan.

Available tools:
{tool_descriptions}

User query: {query}

Asset context: {context}

IMPORTANT RULES:
- Only select tools from the list above.
- Return ONLY valid JSON matching this schema exactly, no markdown fences:
{{"intent": "<purpose>", "steps": [{{"tool_id": "<id>", "input_asset_ids": ["<id>"], "parameters": {{}}, "purpose": "<why>"}}]}}
- Do not hallucinate tool_ids.
- If no tool is appropriate, return an empty steps array."""

        try:
            response = self.model.generate_content(prompt)
            raw = response.text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            plan_data = json.loads(raw.strip())
            steps = []
            for s in plan_data.get("steps", []):
                steps.append(AgentPlanStep(
                    tool_id=s["tool_id"],
                    input_asset_ids=s.get("input_asset_ids", []),
                    parameters=s.get("parameters", {}),
                    purpose=s.get("purpose", "")
                ))
            return AgentExecutionPlan(intent=plan_data.get("intent", query), steps=steps)
        except Exception as e:
            return AgentExecutionPlan(intent=f"Plan parse error: {e}", steps=[])

    def synthesize_answer(self, query: str, tool_results: List[ToolResult]) -> str:
        evidence_summary = []
        for res in tool_results:
            if res.success:
                evidence_summary.append(
                    f"Tool '{res.tool_id}': outputs={res.outputs}, metrics={res.metrics}, "
                    f"regions={len(res.spatial_artifacts)}, provenance={res.provenance[:3]}"
                )
            else:
                evidence_summary.append(
                    f"Tool '{res.tool_id}' FAILED: {res.error_code} — {res.error_message}"
                )
        
        evidence_text = "\n".join(evidence_summary) if evidence_summary else "No tools executed."
        
        prompt = f"""You are SatQuery, a geospatial AI analyst.

User query: {query}

Tool evidence (all deterministic, do not modify these numbers):
{evidence_text}

RULES:
1. Synthesize a clear, concise answer grounded ONLY in the tool evidence above.
2. Do NOT invent numbers. Use only the values from the evidence.
3. Distinguish what is measured from what is uncertain.
4. Use scientific language. Never say "proves" or "confirms" without caveats.
5. Keep the answer under 200 words."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Synthesis failed: {str(e)}. Raw evidence: {evidence_text[:500]}"

