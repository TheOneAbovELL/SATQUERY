with open('backend/app/agent/providers.py', 'a') as f:
    f.write('''

class HeuristicLLMProvider(BaseLLMProvider):
    \"\"\"
    Intelligent mock router for integration testing without an API key.
    Reads the context (which lists assets and modalities) to route correctly.
    \"\"\"
    def generate_plan(self, query: str, context: str, available_tools: List[ToolDefinition]) -> AgentExecutionPlan:
        assets = []
        for line in context.split("\\n"):
            if line.startswith("- "):
                parts = line.split("(Modality: ")
                if len(parts) == 2:
                    a_id = parts[0][2:].strip()
                    mod = parts[1].replace(")", "").strip()
                    assets.append((a_id, mod))

        steps = []
        intent = "Analyzing scene"
        
        if len(assets) == 1:
            a_id, mod = assets[0]
            if mod in ["OPTICAL", "MULTISPECTRAL", "RGB"]:
                steps.append(AgentPlanStep(tool_id="visual_language_specialist", input_asset_ids=[a_id], purpose="Extract insights using VLM", parameters={"query": query}))
                intent = "VLM single-image analysis"
            elif mod == "SAR":
                steps.append(AgentPlanStep(tool_id="sar_analyzer", input_asset_ids=[a_id], purpose="Analyze backscatter properties", parameters={}))
                intent = "SAR analysis"
            else:
                steps.append(AgentPlanStep(tool_id="ndvi_calculator", input_asset_ids=[a_id], purpose="Fallback analysis", parameters={}))
                
        elif len(assets) == 2:
            mods = {a[1] for a in assets}
            if "SAR" in mods and ("OPTICAL" in mods or "MULTISPECTRAL" in mods or "RGB" in mods):
                steps.append(AgentPlanStep(tool_id="cross_modal_evidence", input_asset_ids=[a[0] for a in assets], purpose="Cross-modal synthesis", parameters={}))
                intent = "Optical + SAR cross-modal analysis"
            else:
                steps.append(AgentPlanStep(tool_id="bitemporal_change", input_asset_ids=[a[0] for a in assets], purpose="Analyze temporal change", parameters={}))
                intent = "Bi-temporal change detection"
                
        return AgentExecutionPlan(intent=intent, steps=steps)

    def synthesize_answer(self, query: str, tool_results: List[ToolResult]) -> str:
        if not tool_results:
            return "Analysis yielded no tool results."
            
        res = tool_results[0]
        if res.tool_id == "visual_language_specialist":
            return res.outputs.get("answer", "VLM returned no text.")
            
        if res.tool_id == "bitemporal_change":
            m = res.metrics
            pct = m.get("change_fraction", 0.0) * 100
            return f"Bi-temporal analysis detected change across {pct:.2f}% of the scene ({m.get('changed_pixels', 0)} pixels changed). {len(res.spatial_artifacts)} distinct change regions were identified."
            
        if res.tool_id == "cross_modal_evidence":
            return f"Cross-modal synthesis completed. Agreement class: {res.outputs.get('relationship', 'UNKNOWN')}. {res.outputs.get('synthesis', '')}"
            
        if res.tool_id == "sar_analyzer":
            m = res.metrics
            return f"SAR analysis identified an average backscatter of {m.get('mean_backscatter', 0.0):.2f} dB, with {m.get('high_scatter_fraction', 0.0)*100:.1f}% high-scatter pixels."

        return f"Analysis completed successfully using {res.tool_id}."
''')
