# 🛰️ SatQuery AI

> ### **An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries**

<p align="center">
  <strong>SIH 2026 · Problem Statement 26167 · ISRO / Department of Space</strong>
</p>

<p align="center">
  <em>Ask questions about satellite imagery in natural language. Get deterministic measurements, visual evidence, model interpretation, and an auditable execution trace.</em>
</p>

![SatQuery AI system architecture](./SatQuery_AI_Architecture_Diagram%20(1).png)

---

## 🚀 At a Glance

| | |
|---|---|
| **Project** | SatQuery AI |
| **SIH Problem Statement** | 26167 |
| **Domain** | Multimodal Remote Sensing · Vision-Language AI · Geospatial Analytics |
| **Primary modalities** | Optical / Multispectral / SAR |
| **VLM** | Qwen2-VL-2B-Instruct |
| **RS adaptation** | PEFT LoRA adapter |
| **Backend** | FastAPI + Python |
| **Frontend** | Next.js 16 + React |
| **Geospatial stack** | Rasterio + Shapely + NumPy + SciPy |
| **Current state** | 🟢 **Feature Frozen / Working Prototype** |
| **Benchmark status** | ⚠️ Not run locally |
| **Hidden ISRO/SAC validation** | ⚠️ Not available for local validation |

### ✨ What makes SatQuery different?

SatQuery is designed around a simple but important separation:

**AI interprets imagery and evidence. Deterministic geospatial tools perform the measurements.**

That means a query such as:

> **“What changed between these two satellite images, and where?”**

can result in a response built from:

**Natural-language query → validation → capability routing → remote-sensing computation → spatial evidence → VLM interpretation → grounded answer**

rather than asking a language model to invent spatial measurements.

---

## 🎯 Core Product Experience

SatQuery is intended to feel like **“ChatGPT for satellite imagery, with specialist remote-sensing tools behind it.”**

## 🖥️ Web Page Preview

The web experience uses a dark, space-inspired visual language with bright satellite imagery, subtle gradients, and compact mission-control styling.

### Landing page mockup

This first mockup is the product landing page: a cinematic Earth background, strong headline, product positioning, and the primary **Start Analyzing** call to action. It frames SatQuery AI as a geospatial intelligence assistant for understanding Earth from imagery.

![SatQuery AI landing page](./frontend/public/earth-hero.jpg)

### Chat interface mockup

This second mockup represents the chat interface used after the landing page. It keeps the dark mission-control aesthetic, centers the conversation on imagery and prompts, and shows how an analyst can upload an image, ask a question, and work from a guided chat-style workflow.

![SatQuery AI chat interface](./frontend/public/chat-bg.jpg)

A typical analyst workflow is:

```text
┌──────────────────────┐
│  Upload satellite    │
│  imagery             │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Ask in natural       │
│ language              │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Validate imagery +   │
│ identify capabilities │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Select specialist    │
│ analysis tool/model  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Deterministic RS     │
│ computation          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Evidence + spatial   │
│ artifacts + metrics  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Qwen2-VL interprets  │
│ and synthesizes      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Answer + visual      │
│ evidence + trace     │
└──────────────────────┘
🧭 README Navigation
Quick Start
How the System Thinks
Architecture at a Glance
Data Flow
Scientific Guardrails
Team Handoff
Demo Checklist
Original Detailed Project Documentation
⚡ Quick Start
Windows
git clone <YOUR_REPOSITORY_URL>
cd SATQUERY

cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

cd ..\frontend
npm install

cd ..\backend
python scripts\download_sample_data.py

cd ..
verify_demo.bat
run_demo.bat

Then open:

Frontend: http://localhost:3000
Backend: http://127.0.0.1:8000
Health: http://127.0.0.1:8000/health
macOS
git clone <YOUR_REPOSITORY_URL>
cd SATQUERY

cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_sample_data.py

cd ../frontend
npm install

cd ../backend
source .venv/bin/activate
python -m uvicorn main:app --port 8000

In a second terminal:

cd SATQUERY/frontend
npm run dev

Then open http://localhost:3000.

First-run note: the Qwen2-VL base model is downloaded from Hugging Face when needed. The repository contains the lightweight RS LoRA adapter, not the multi-GB base model weights.

🧠 How the System Thinks

SatQuery does not treat every question as a generic VLM prompt.

The query and input imagery determine which capabilities are relevant.

User intent	Typical execution path
Single-image question	VLM / visual-language specialist
Scene description	Qwen2-VL + RS LoRA
Two-image change question	Bi-temporal deterministic analysis
SAR observation	SAR specialist
Optical + SAR comparison	Cross-modal evidence tool
Numerical question	Deterministic analytics first
Spatial evidence question	Deterministic artifact generation + synthesis

The current implementation uses a deterministic/heuristic router for reliability. The repository also exposes abstraction boundaries intended to support richer LLM planning in future work.

🏗️ Architecture at a Glance
                    ┌─────────────────────┐
                    │      Web GUI        │
                    │  Next.js / React    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   FastAPI Backend   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Input Validation &  │
                    │ Modality Detection │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Agent / Router      │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
 ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
 │ Single-image   │   │ Bi-temporal    │   │ SAR specialist │
 │ VLM path       │   │ change path    │   │ path           │
 └───────┬────────┘   └───────┬────────┘   └───────┬────────┘
         │                    │                    │
         ▼                    ▼                    ▼
 ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
 │ Qwen2-VL +     │   │ NumPy/SciPy +  │   │ SAR statistics │
 │ RS LoRA        │   │ Rasterio       │   │ + thresholds   │
 └───────┬────────┘   └───────┬────────┘   └───────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
                    ┌─────────────────────┐
                    │ Evidence / Spatial  │
                    │ Artifacts / Metrics │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ VLM / LLM Synthesis  │
                    └──────────┬──────────┘
                               │
                               ▼
             ┌────────────────────────────────────┐
             │ Answer + Evidence + Trace + Visual │
             └────────────────────────────────────┘
🔄 Data Flow
Single image
Image
  ↓
GeoTIFF / image validation
  ↓
Modality detection
  ↓
VLM adapter
  ↓
Qwen2-VL + RS LoRA
  ↓
Semantic interpretation
  ↓
Grounded response
Bi-temporal imagery
T1 + T2
  ↓
CRS / transform / bounds validation
  ↓
Spatial overlap / alignment
  ↓
NoData masking
  ↓
Pixel differencing
  ↓
Thresholding
  ↓
Change mask
  ↓
Connected regions
  ↓
Counts / fractions / metrics
  ↓
Visual evidence
  ↓
VLM interpretation
Optical + SAR
Optical evidence ───────┐
                        ├──► Cross-modal evidence
SAR evidence ───────────┘
                              ↓
                         Spatial comparison
                              ↓
                         bbox_iou
                              ↓
                 Agreement / complementary /
                    disagreement / inconclusive
                              ↓
                         Final synthesis
🛡️ Scientific Guardrails

SatQuery intentionally follows several scientific safeguards:

1. Measurements are not generated by the language model

Values such as:

changed pixel count
change fraction
area
NDVI
NDWI
NDBI
SAR statistics
percentile thresholds
bbox IoU

come from deterministic computational paths where supported.

2. Evidence is not ground truth

Optical and SAR agreement is treated as spatial corroboration/evidence, not absolute truth.

3. SAR returns are interpreted cautiously

A high-backscatter region is an observation. It is not automatically declared to be a building, vehicle, concrete structure, or metal object.

4. Confidence is not presented as calibrated probability

The current implementation uses heuristic confidence signals and explicitly documents this limitation.

5. Benchmark claims are evidence-based

VRSBench, RSVQA, CDVQA, and hidden ISRO/SAC results are not claimed unless actually executed and validated.

👥 Team Handoff — Quick Reference

A new teammate should be able to:

Clone the repository.
Read this README.
Install backend dependencies.
Install frontend dependencies.
Generate demo imagery.
Start the backend.
Start the frontend.
Run the verification suite.
Upload the demo imagery.
Execute the four documented flows.
Run the full pytest suite before making changes.
Before changing code
Read README
   ↓
Inspect relevant subsystem
   ↓
Run baseline tests
   ↓
Make the smallest necessary change
   ↓
Run targeted tests
   ↓
Run full tests
   ↓
Build frontend
   ↓
Run demo verification
   ↓
Update documentation if behavior changed
Repository hygiene

Keep source code and the lightweight adapter in Git, but do not commit:

node_modules/
.next/
.venv/
__pycache__/
.pytest_cache/
.env
API keys
downloaded Hugging Face base-model caches
temporary uploads
generated temporary artifacts
Colab-specific temporary files
🎬 Demo Checklist

Before a presentation:

 Repository cloned and clean
 Backend environment active
 Frontend dependencies installed
 Sample data generated
 Qwen model available/cached
 LoRA adapter detected
 Backend health endpoint responds
 Frontend loads
 python -m pytest -q passes
 verify_demo.bat passes on Windows
 Four demo flows rehearsed
 CPU inference timing understood
 Scientific limitations understood
 No unsupported benchmark claims are made
Recommended judge narrative

“SatQuery separates interpretation from measurement. The VLM understands the imagery and natural-language intent, while deterministic remote-sensing tools calculate the numbers. Every answer can therefore be accompanied by the evidence and execution trace that produced it.”

📌 Important Status Interpretation

This repository should be understood as a working, feature-frozen SIH prototype.

That means:

The core software runs.
The main demonstration workflows work.
The system has been tested.
The repository can be handed to teammates.
The implementation should not be casually redesigned before the SIH demo.

It does not mean:

official benchmark scores already exist,
hidden ISRO/SAC data has been validated,
every research-grade remote-sensing limitation has been solved,
heuristic confidence is calibrated probability,
bbox IoU is exact mask IoU.

Those distinctions are intentionally documented below.

1. Project Status

FEATURE FREEZE (SIH 2026)

The core implementation is locked and verified. The system successfully executes single-image VQA, bi-temporal change detection, SAR analysis, and optical+SAR cross-modal reasoning.

2. SIH 2026 Context
Problem Statement: 26167 - "An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries."
Organization: ISRO / Department of Space
Goal: Enable users to interrogate remote-sensing imagery (Optical, SAR) via natural language, retrieving deterministic, scientifically grounded numerical answers backed by VLM-synthesized interpretations.
3. Executive Summary

SatQuery AI bridges the gap between expert GIS tools and accessible natural language AI. Instead of manually selecting algorithms, a user uploads satellite imagery and asks a question (e.g., "What changed here?" or "Compare the optical and SAR observations."). The system's agentic router analyzes the inputs, selects appropriate deterministic geospatial tools (rasterio, shapely, scipy), computes precise numerical measurements, and feeds this structured evidence to a fine-tuned Vision-Language Model (Qwen2-VL with a custom RS LoRA adapter). The result is a scientifically honest, auditable answer where the AI interprets the scene but never fabricates the underlying spatial mathematics.

4. Key Capabilities
Capability	Status	Implementation	Notes
Single-image VQA	PASS	Qwen2-VL-2B + LoRA	Analyzes single RGB/Multispectral images via text query.
Image Captioning	PASS	Qwen2-VL-2B + LoRA	Can describe the overall scene.
Spatial Grounding	PARTIAL	Architectural	Core bounding boxes supported; strict pixel-level grounding VLM not implemented.
Bi-temporal Change	PASS	Deterministic Raster Diff	Co-registered array differencing; extracts changed_pixel_count.
Change VQA	PASS	Agentic Routing	Routes queries about change to deterministic tool, VLM synthesizes.
Optical/Multispectral	PASS	rasterio / Validator	Handles standard RGB and multi-band data (NDVI fallback).
SAR Analysis	PASS	Deterministic Stats	Detects VV/VH, dB conversion, robust stats (p99, mean).
Optical + SAR Fusion	PASS	Bounding-Box IoU	Cross-modal spatial validation using bbox_iou (not pixel-mask).
Agent/Tool Routing	STRUCTURAL	Heuristic Router	Deterministic modality-aware routing currently utilized.
Input Validation	PASS	InputValidator	Strict CRS, transform, bounds, and tag extraction.
Provenance/Trace	PASS	Execution Trace	End-to-end audit trail of tools, parameters, and evidence.
Confidence	PARTIAL	Heuristic	Hardcoded heuristic signals (1.0 for math); no calibrated probability.
GUI	PASS	Next.js 16 App Router	Full map-centric, responsive React dashboard.
VRSBench / RSVQA	NOT RUN	Adapter Stubs	Adapters implemented in backend/evaluation/; data not evaluated.
Hidden ISRO Data	NOT VALIDATED	N/A	Architecturally supported but impossible to validate without data.
5. High-Level Architecture
6. Scientific Design Principle

"LLMs interpret evidence; deterministic remote-sensing computations produce numerical measurements."

SatQuery AI prevents hallucination by strictly decoupling spatial mathematics from language generation.

Deterministic: Area, NDVI, changed pixel counts, change fractions, p99 backscatter, and bbox_iou are calculated mathematically using numpy, scipy, and rasterio. The LLM cannot invent these values.
Interpretation: The VLM (Qwen2-VL) receives this deterministic numerical evidence as structured text and uses it to synthesize the final natural-language response. It provides semantic understanding, qualitative descriptions, and contextualizes the numbers without performing arithmetic itself.
7. Repository Structure
SATQUERY/
+-- backend/                        # FastAPI Python backend
¦   +-- app/
¦   ¦   +-- agent/                  # Orchestrator, tool registry, routing (providers.py)
¦   ¦   +-- analytics/              # Core RS tools, Qwen2VL adapter loader
¦   ¦   +-- api/                    # FastAPI routes
¦   ¦   +-- domain/                 # Pydantic data models
¦   +-- evaluation/                 # Benchmark adapter framework (VRSBench, etc.)
¦   +-- mock_data/                  # Generated demo sample data
¦   +-- scripts/                    # Utilities (e.g., download_sample_data.py)
¦   +-- tests/                      # Pytest suite (unit, integration, regression)
+-- docs/                           # Extended documentation, demo scripts, Q&A
+-- frontend/                       # Next.js 16 React frontend
¦   +-- src/
¦   ¦   +-- app/                    # App router pages
¦   ¦   +-- components/             # React UI components (chat, map, asset viewer)
+-- models/                         # Local weights and adapters
¦   +-- rs_lora_adapter/            # The trained PEFT LoRA adapter (tracked in Git)
+-- run_demo.bat                    # Windows master launch script
+-- verify_demo.bat                 # Pre-flight environment checker
+-- README.md                       # This file
8. Complete Windows Installation

Prerequisites: Windows 10/11, Python 3.11+, Node.js 18+, Git, ~6GB disk space.

1. Clone the repository:

git clone <YOUR_REPOSITORY_URL>
cd SATQUERY

2. Backend Setup:

cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

3. Frontend Setup:

cd ..\frontend
npm install

4. Generate Demo Data:

cd ..\backend
python scripts\download_sample_data.py

(This generates landsat7_rgb_sample.tif, landsat7_rgb_t2_simulated.tif, and simulated_sar_sample.tif in backend/mock_data/real_samples/)

5. Model Behavior (First Run):

The system uses Qwen/Qwen2-VL-2B-Instruct. On the first analysis request, Hugging Face will download the ~4GB base weights to your local cache (~/.cache/huggingface/hub). The custom LoRA adapter is already included in models/rs_lora_adapter/ and will be loaded dynamically using PEFT. If CUDA is unavailable, inference automatically falls back to CPU (~60-90 seconds per VLM query).

6. Verification & Run:

cd ..
verify_demo.bat
run_demo.bat

This launches the backend on http://127.0.0.1:8000 and the frontend on http://localhost:3000.

9. Complete macOS Installation

(Note: Apple Silicon / MPS hardware acceleration for Qwen2-VL has not been extensively tested. CPU inference is the supported fallback.)

Prerequisites: macOS (Intel/M-series), Python 3.11+, Node.js 18+, Git.

1. Clone & Backend Setup:

git clone <YOUR_REPOSITORY_URL>
cd SATQUERY/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_sample_data.py

2. Frontend Setup:

cd ../frontend
npm install

3. Run (Manual):

Terminal 1 (Backend):

cd backend
source .venv/bin/activate
python -m uvicorn main:app --port 8000

Terminal 2 (Frontend):

cd frontend
npm run dev
10. Model Architecture

Base Model: Qwen2-VL-2B-Instruct

Chosen for its strong multimodal reasoning and relatively small 2B parameter size, allowing reasonable local execution. It handles single-image qualitative analysis and synthesizes deterministic outputs into natural language.

RS LoRA Adapter:

Located in models/rs_lora_adapter/.

Method: PEFT 0.11.1
Rank (r): 8, Alpha: 16
Target Modules: q_proj, k_proj, v_proj, o_proj
Size: ~8.75 MB
Behavior: Modifies the attention mechanism for remote-sensing vocabulary without catastrophically forgetting general reasoning. Loaded alongside the base model at runtime.
11. Training / Adaptation
Dataset: UCM-Captions (500 samples: 450 train, 50 val)
Source: HuggingFace (cpratikaki/UCMcaptions_finetuning)
Hardware: Google Colab T4 GPU
Hyperparameters: LR=0.0002, Epochs=3, Batch=1, Grad Accum=8, Seq Len=512.
Loss: Final validation loss ~0.908.
Note: The UCM-Captions dataset was used for development adaptation, not as a proxy for the actual SIH evaluation sets (VRSBench, etc.). License provenance for UCM-Captions requires formal verification prior to commercial deployment.
12. Remote Sensing Pipeline

Geospatial ingestion uses Rasterio. When a GeoTIFF is uploaded, the InputValidator inspects the Coordinate Reference System (CRS), Affine transform, bounding box, resolution, and band descriptions.

Metadata (e.g., SENSOR="SENTINEL-1", band tags "VV", "VH") determines the AssetModality (RGB, Multispectral, SAR, Grayscale).
If a valid projected CRS exists, physical area calculations are enabled.
Invalid files are rejected with a structured HTTP 422 error.
13. Single Image Intelligence

Path: User Query → Input Validator → Modality = RGB → visual_language_specialist Tool → Qwen2-VL + LoRA → Answer.

The VLM handles open-ended VQA and captioning. Note: Strict pixel-coordinate spatial grounding (drawing accurate bounding boxes purely via LLM coordinates) is architecturally acknowledged but heavily limited by the 2B model size.

14. Bi-Temporal Change Intelligence

Path: User Query → Two Optical Assets → bi_temporal_change_analysis Tool.

Validates CRS and spatial overlap.
Performs exact array differencing (masking nodata).
Applies thresholding to detect significant pixel shifts.
Extracts changed_pixel_count and mathematically calculates change_fraction.
Groups changed pixels into spatial regions (connected components).
VLM synthesizes these deterministic facts into a natural language response. (e.g., "Change detected across 1.88% of the scene...").
15. SAR Specialist

Path: User Query → SAR Asset → sar_analysis Tool.

Detects VV/VH polarization. Converts linear backscatter to decibels (10*log10). Applies robust statistics (mean, median, p99) while clipping outliers (2nd-98th percentile) to handle SAR speckle.

Scientific wording constraint: High returns are extracted via thresholding and labeled as "high-backscatter regions" or "candidate reflective targets"—the system never assumes they are definitively "buildings" or "vehicles" without corroborating evidence.
16. Optical + SAR Cross-Modal Analysis

Path: User Query → Optical Asset + SAR Asset → cross_modal_evidence Tool.

Runs change detection on the optical pair and backscatter thresholding on the SAR pair. Extracts the spatial bounding box envelopes of the resulting evidence regions.

Calculates Bounding-Box Intersection over Union (bbox_iou).
Classifies relationship: AGREEMENT, DISAGREEMENT, COMPLEMENTARY.
Important Constraint: This is bounding-box envelope overlap, not exact pixel-mask IoU. "Agreement" signifies spatial corroboration, not absolute ground-truth confirmation.
17. Agent / Tool System

The routing logic (backend/app/agent/providers.py) uses a deterministic, heuristic router based on asset modality counts (e.g., 2 optical = change analysis; 1 SAR = SAR analysis; 1 optical = VQA). The architecture defines abstract interfaces (BaseLLMProvider) designed to support open-ended LLM planning (e.g., Gemini/GPT-4), but defaults to the heuristic router for offline reliability.

18. Evidence System

Evidence is a first-class citizen.

Input → Computation (Tool) → Evidence (Numerical/Spatial) → Claim → Final Answer

The system generates structured metric dictionaries and spatial artifact references (GeoTIFF masks, PNGs) passed upward to the UI and the VLM.

19. Provenance & Execution Trace

Every request generates a 5-stage Execution Trace (Tool Requested, Input Validated, Execution Started, Execution Completed, Result Validated). The frontend displays this audit log, ensuring the judge or analyst can trace precisely which deterministic tool produced a metric. Internal LLM chain-of-thought is not exposed.

20. Confidence

Confidence is currently heuristic. Deterministic tool executions return a hardcoded confidence of 1.0. VLM generations return a placeholder (-1.0). The system does not claim statistically calibrated probability.

21. Frontend

Built with Next.js 16. The GUI is a map-centric, responsive dashboard featuring:

Asset upload panel (GeoTIFF, PNG, JPEG).
Interactive image canvas.
Natural language query bar.
Timeline execution trace and evidence drawer.
22. API Overview

Key routes (http://127.0.0.1:8000/api/v1):

GET /health : API availability.
POST /upload : Multipart form upload. Returns structured ImageAsset.
POST /analyze : Accepts {"query": "...", "asset_ids": ["uuid"]}. Returns structured AnalysisResult.
GET /assets/{id}/thumbnail : Serves display-ready PNGs of raw GeoTIFFs.
23. Testing

Execute in backend/:

python -m pytest -q

Current Status: 54 passed, 1 skipped, 0 failed. (The skipped test is a regression fixture requiring missing benchmark data).

24. Evaluation

Framework implemented in backend/evaluation/ (Adapters for VRSBench, RSVQA, CDVQA).

Status: NOT RUN. Benchmark datasets are not available locally. The system gracefully returns a "Not Available" status. No scores are fabricated. Validation against hidden ISRO/SAC data is architecturally supported but impossible to verify locally.

25. Sample Demo Data

Run python scripts/download_sample_data.py (in backend/) to generate:

landsat7_rgb_sample.tif (Real RGB)
landsat7_rgb_t2_simulated.tif (Derived T2 with simulated change)
simulated_sar_sample.tif (Semi-synthetic derived SAR simulation, tagged as Sentinel-1. Used purely to demonstrate the processing pipeline offline).
26. Complete Demo Guide (4 Verified Flows)
Upload all three demo TIFFs.
Flow 1 (VQA): Select landsat7_rgb_sample. Query: "What does this satellite image show?" (Points out VLM interpretation, takes ~60-90s on CPU).
Flow 2 (Change): Select landsat7_rgb_sample and landsat7_rgb_t2_simulated. Query: "What changed between these two images?" (Points out exact pixel counts and fractions).
Flow 3 (SAR): Select simulated_sar_sample. Query: "What are the strongest backscatter regions?" (Points out p99 dB metrics, emphasizes cautious language).
Flow 4 (Cross-Modal): Select optical T1 and SAR. Query: "Compare the optical and SAR evidence." (Points out bbox_iou and Agreement classification).
27. Troubleshooting
Symptom	Cause	Fix
python not found	Python not in PATH	Install Python 3.11+, check "Add to PATH"
Backend missing packages	Venv not active	.venv\Scripts\activate then pip install -r requirements.txt
npm not found	Node.js not installed	Install Node 18 LTS
VLM inference times out	Slow CPU / large image	Wait up to 120s, or use a CUDA-enabled GPU
Modality incorrect	Missing GeoTIFF tags	Use the generated demo TIFFs which have correct metadata
Test collection fails	Root scripts collected	Fixed via pyproject.toml testpaths=["tests"]
28. Performance

Deterministic analytics (Change, SAR, Metrics) are very fast (< 1 second). VLM interpretation (Qwen2-VL) on a CPU is the primary bottleneck (~60-90 seconds). GPU inference is highly recommended for live presentations. The Next.js frontend and FastAPI backend exhibit near-zero latency.

29. Team / GitHub Handoff

To use this repository:

Clone and follow the installation guide exactly.
DO NOT COMMIT: node_modules, pycache, .venv, .env, downloaded base model caches (~/.cache/huggingface), or temporary uploads.
DO COMMIT: The LoRA adapter in models/rs_lora_adapter/ (it is explicitly allowed in .gitignore).
30. Instructions for an AI Coding Agent Taking Over This Repository
Read this README first.
Inspect the repository before changing anything.
Preserve the architecture: Do not let an LLM invent numerical measurements.
Do not invent capabilities or claim benchmark scores without actual dataset runs.
Do not claim hidden ISRO validation.
Run python -m pytest -q in backend/ before and after modifications.
Maintain the clear separation between deterministic tools (backend/app/analytics/) and the VLM synthesizers.
Keep the LoRA adapter modular. Do not merge base weights into the repo.
Recommended workflow: Inspect → Baseline tests → Minimal change → Target tests → Full tests → Update docs.
31. Scientific Limitations
Cross-modal spatial comparison relies on Bounding-Box IoU (bbox_iou), not pixel-level mask overlap.
SAR demonstration data is semi-synthetic to ensure offline demo viability.
Heuristic confidence scoring only; no calibrated probabilistic uncertainty.
Agentic routing is deterministic/heuristic, not open-ended LLM planning.
Datasets (VRSBench, RSVQA, CDVQA, hidden ISRO) have not been formally evaluated locally.
Dataset licensing (UCM-Captions) requires formal verification for non-academic use.
32. SIH Compliance Matrix
SIH Requirement	Current Implementation	Status
Single-image VQA / Captioning	Qwen2-VL + LoRA	PASS
Bi-temporal change	Deterministic Array Diff	PASS
Optical / Multispectral support	rasterio ingest	PASS
SAR imagery	Metadata + dB stats	PASS
Optical + SAR cross-modal	Bounding-Box IoU	PASS
Agentic tool selection	Heuristic Router	STRUCTURAL
Evidence / Provenance	Execution Trace	PASS
VLM adaptation	LoRA adapter	PASS
Benchmark / ISRO Data Evaluation	Adapters built	NOT RUN / NOT VALIDATED
33. Future Work
Exact pixel-mask cross-modal IoU.
Unrestricted LLM planning (dynamic agentic routing).
Integration with official Sentinel-1 / ISRO datasets.
Scalable GPU workers for fast VLM throughput.
34. Final Status

The repository is currently feature-frozen. It is suitable for demonstration, development handoff, and SIH presentation. No fabricated benchmark data or hidden-dataset validation is claimed. All implemented flows are strictly verifiable.
