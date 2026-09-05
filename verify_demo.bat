@echo off
echo ============================================================
echo SatQuery AI - Demo Environment Verification
echo ============================================================
echo.

:: Python check
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Python not found. Install Python 3.11+.
    goto :end
)
echo [PASS] Python found.

:: Node check
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Node.js not found. Install Node 18+.
    goto :end
)
echo [PASS] Node.js found.

:: Backend dependencies
echo [CHECK] Verifying core backend imports...
python -c "import fastapi, rasterio, numpy, shapely, PIL, scipy; print('[PASS] Core backend packages OK')"
if %errorlevel% neq 0 (
    echo [FAIL] Missing backend packages. Run: pip install -r backend/requirements.txt
    goto :end
)

:: LoRA adapter check
if exist "models\rs_lora_adapter\adapter_model.safetensors" (
    echo [PASS] LoRA adapter found.
) else (
    echo [WARN] LoRA adapter not found at models\rs_lora_adapter\
    echo        Inference will use Qwen2-VL base model only.
)

:: Demo data check
if exist "backend\mock_data\real_samples\landsat7_rgb_sample.tif" (
    echo [PASS] Demo optical data found.
) else (
    echo [WARN] Demo data not found. Run: cd backend && python scripts/download_sample_data.py
)

:: Frontend packages
if exist "frontend\node_modules" (
    echo [PASS] Frontend node_modules present.
) else (
    echo [WARN] Run: cd frontend && npm install
)

echo.
echo ============================================================
echo Verification complete.  Run run_demo.bat to launch.
echo ============================================================
:end
