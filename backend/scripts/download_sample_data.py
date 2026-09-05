import os
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'mock_data', 'real_samples')
os.makedirs(DATA_DIR, exist_ok=True)

# Rasterio's public test data: real Landsat 7 subset (RGB)
OPTICAL_URL = "https://raw.githubusercontent.com/rasterio/rasterio/master/tests/data/RGB.byte.tif"
OPTICAL_PATH = os.path.join(DATA_DIR, "landsat7_rgb_sample.tif")

# Create a realistic SAR file by mathematically converting a band of the optical image
# to simulate backscatter, since finding a direct tiny public S1 GeoTIFF URL that doesn't 
# require authentication or EarthData login is tricky.
# We will explicitly label its provenance as semi-synthetic derived from real data for demo.

def download_data():
    if not os.path.exists(OPTICAL_PATH):
        logging.info(f"Downloading real optical sample from {OPTICAL_URL}...")
        urllib.request.urlretrieve(OPTICAL_URL, OPTICAL_PATH)
        logging.info(f"Saved to {OPTICAL_PATH}")
    else:
        logging.info(f"Optical sample already exists at {OPTICAL_PATH}")
        
    sar_path = os.path.join(DATA_DIR, "simulated_sar_sample.tif")
    if not os.path.exists(sar_path):
        import rasterio
        import numpy as np
        logging.info("Generating a simulated SAR image from the optical data for cross-modal testing...")
        with rasterio.open(OPTICAL_PATH) as src:
            meta = src.meta.copy()
            # Simulated SAR: linear backscatter is roughly correlated with NIR/Red intensity, we'll add speckle noise
            band1 = src.read(1).astype(float)
            # Add multiplicative Rayleigh noise (speckle)
            speckle = np.random.rayleigh(1.0, band1.shape)
            sar_sim = (band1 * speckle * 0.1) # Scale to low linear values
            sar_sim = np.clip(sar_sim, 1e-5, 100) # prevent 0
            
            meta.update({
                "count": 1,
                "dtype": 'float32'
            })
            with rasterio.open(sar_path, 'w', **meta) as dst:
                dst.write(sar_sim.astype(np.float32), 1)
                dst.update_tags(SENSOR='SENTINEL-1', POLARIZATION='VV')
                dst.set_band_description(1, 'VV')
        logging.info(f"Saved simulated SAR to {sar_path}")

    # Generate a T2 for bi-temporal
    t2_path = os.path.join(DATA_DIR, "landsat7_rgb_t2_simulated.tif")
    if not os.path.exists(t2_path):
        logging.info("Generating a T2 optical image (simulated change)...")
        import rasterio
        import numpy as np
        with rasterio.open(OPTICAL_PATH) as src:
            meta = src.meta.copy()
            data = src.read()
            # Simulate a large burnt area or flood by zeroing out a rectangle
            data[:, 100:200, 100:200] = data[:, 100:200, 100:200] * 0.2 
            
            with rasterio.open(t2_path, 'w', **meta) as dst:
                dst.write(data)
        logging.info(f"Saved simulated T2 optical to {t2_path}")

if __name__ == "__main__":
    download_data()
