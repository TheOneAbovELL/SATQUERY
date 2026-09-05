import sys
with open('backend/app/agent/providers.py', 'r') as f:
    text = f.read()

text = text.replace('tool_id="bitemporal_change"', 'tool_id="bi_temporal_change_analysis"')
text = text.replace('res.tool_id == "bitemporal_change"', 'res.tool_id == "bi_temporal_change_analysis"')
text = text.replace('tool_id="sar_analyzer"', 'tool_id="sar_analysis"')
text = text.replace('res.tool_id == "sar_analyzer"', 'res.tool_id == "sar_analysis"')
text = text.replace('"SAR" in mods', '("SAR" in mods or "Grayscale" in mods)')

with open('backend/app/agent/providers.py', 'w') as f:
    f.write(text)
