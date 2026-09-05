# SatQuery AI — Judge Q&A Preparation Guide
SIH 2026 | PS 26167

---

**Q1: Why not just use ChatGPT or Gemini directly on the image?**
A: General-purpose LLMs hallucinate spatial statistics. SatQuery routes the query through deterministic raster analytics first — change counts, SAR backscatter percentiles, area measurements — and only sends verified evidence to the VLM for interpretation. The model cannot invent pixel counts.

**Q2: What makes this agentic?**
A: The system receives a natural language query, inspects asset modalities, and autonomously selects the appropriate specialist tool (bi-temporal change, SAR analysis, cross-modal fusion, or VQA). The routing is deterministic and rule-based today; the architecture supports plugging in an LLM planner (GeminiProvider) for free-form planning when an API key is available.

**Q3: What is deterministic vs AI-generated in the output?**
A: Deterministic: changed_pixel_count, change_fraction, SAR p99 dB, bounding-box IoU, region centroids, area (if projected CRS). AI-generated: the natural-language summary, scene description, and interpretation of the evidence.

**Q4: How do you prevent hallucinated numbers?**
A: The VLM never performs arithmetic. Numerical values are computed by rasterio + scipy + numpy and placed directly into the structured result. The VLM only receives the text summary of evidence, not raw pixel values.

**Q5: How does SAR analysis work?**
A: We read the SAR raster via rasterio, detect polarization from band descriptions (VV/VH), optionally convert to log-scale dB (10*log10), clip to 2-98 percentile to handle speckle, then compute robust statistics (mean, median, p99). Bright-return regions are extracted via connected-component labeling above a threshold.

**Q6: How do you combine optical and SAR?**
A: We run change analysis on optical T1/T2 to extract change regions, run SAR analysis to extract high-backscatter regions, then compute the Bounding-Box Intersection over Union (bbox_iou) between their spatial extents. The result is classified as AGREEMENT, COMPLEMENTARY, or DISAGREEMENT.

**Q7: Is bbox_iou the same as pixel-level IoU?**
A: No. We explicitly use bounding-box envelope intersection, not raster mask overlap. We label it "bbox_iou" throughout the code and UI to be transparent. Pixel-mask IoU would require more compute and is a roadmap item.

**Q8: What is the role of Qwen?**
A: Qwen2-VL-2B-Instruct is the vision-language model used for single-image captioning/VQA and for synthesizing deterministic analytics into natural language. It does not perform spatial measurement.

**Q9: What did you fine-tune?**
A: We applied LoRA (Low-Rank Adaptation) fine-tuning to Qwen2-VL-2B-Instruct. LoRA parameters: r=8, alpha=16, targeting q_proj, k_proj, v_proj, o_proj attention matrices. The adapter is ~8.75 MB and is separate from the 4+ GB base model.

**Q10: What dataset did you use for adaptation?**
A: UCM-Captions — an aerial/remote-sensing image captioning dataset. Accessed via HuggingFace (cpratikaki/UCMcaptions_finetuning). 500 samples (450 train, 50 validation). Dataset license provenance requires formal verification; used for research/academic purposes under fair-use during development.

**Q11: Why LoRA?**
A: LoRA is parameter-efficient — we fine-tune less than 1% of model parameters, avoiding catastrophic forgetting while adapting to RS vocabulary. It is also practical: training ran in ~12 minutes on a free T4 Colab GPU. The adapter can be swapped or updated independently of the base model.

**Q12: What happens without a GPU?**
A: The system falls back to CPU inference automatically (torch device_map="cpu"). Inference is slower (~60-90 seconds per query) but produces identical results. All deterministic analytics run at normal speed since they use numpy/rasterio, not torch.

**Q13: How does the system validate inputs?**
A: InputValidator reads raster metadata via rasterio: checks CRS presence, bounds, band count, band descriptions, and GDAL tags to determine modality (RGB, Multispectral, SAR, Grayscale). It returns capability flags: can_ndvi, can_change_analysis, can_area_measurement. Invalid inputs return structured error responses (HTTP 422) with actionable messages.

**Q14: How is confidence calculated?**
A: Tool-level heuristic signals: DETERMINISTIC (1.0) for raster math, MODEL_CONFIDENCE (-1.0 placeholder) for VLM output since VLM confidence is not calibrated. We do not claim statistical probability. In the UI this is labeled as "Heuristic confidence."

**Q15: What is your provenance mechanism?**
A: Every tool result includes a provenance list: computation method, adapter used, dataset source, alignment provenance, region statistics. This traces answer ? claim ? evidence ? tool ? input asset ? computation.

**Q16: What happens on hidden ISRO/SAC data?**
A: The system processes any standard GeoTIFF/TIFF raster. It does not assume benchmark-specific structure. We cannot validate on hidden data we do not possess — this is honestly stated as "NOT VALIDATED" in the compliance matrix.

**Q17: Have you evaluated VRSBench/RSVQA/CDVQA?**
A: We have implemented dataset adapters for all three in backend/evaluation/. However, the datasets are not locally available, so we report status = NOT RUN. We do NOT fabricate scores.

**Q18: What are the current limitations?**
A: (1) CPU inference latency (~60-90s for VQA). (2) Cross-modal uses bbox_iou, not pixel-mask IoU. (3) Demo SAR is semi-synthetic. (4) Benchmark datasets not evaluated locally. (5) Agentic routing is deterministic (rule-based), not open-ended LLM planning.

**Q19: How would this scale to real ISRO deployment?**
A: Replace CPU inference with GPU server, plug in production HuggingFace or internal model endpoint, connect to ISRO SDP data lake for asset ingestion, and scale FastAPI with multiple workers. The architecture is stateless and horizontally scalable.

**Q20: Why is this better than conventional GIS tools?**
A: Conventional GIS (QGIS, ArcGIS) requires expert users, manual workflow setup, and cannot answer natural language questions. SatQuery provides: (1) natural language interface, (2) automatic specialist routing, (3) VLM-powered interpretation, (4) combined optical+SAR cross-modal reasoning, (5) fully auditable evidence chain — all in one system.
