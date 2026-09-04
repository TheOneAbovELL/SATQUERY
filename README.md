# SatQuery AI Platform

An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis.

## Overview
This repository contains the monorepo for SatQuery AI (SIH 2026 Problem Statement 26167).

## Architecture
- **Frontend:** Next.js application shell (UI, Chat, Geospatial Map).
- **Backend:** Python + FastAPI handling agent orchestration, tool registries, and deterministic raster analytics.

## Setup
### Backend (Python)
1. `cd backend`
2. `uv venv`
3. `uv pip install -e .`
4. Run server: `uvicorn main:app --reload`

### Frontend (Next.js)
1. `cd frontend`
2. `npm install`
3. `npm run dev`

## Job Architecture
Analysis executes as asynchronous jobs. The orchestrator receives natural language queries, maps them to specialist tools, validates outputs, and calculates deterministic analytics.
