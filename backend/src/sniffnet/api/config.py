from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODELS_DIR = PROJECT_ROOT / "artifacts/models"
DEFAULT_IMAGE_STORAGE_DIR = PROJECT_ROOT / "../data/images"

MODEL_WEIGHTS_DIR = Path(os.getenv("MODEL_WEIGHTS_DIR", DEFAULT_MODELS_DIR))
MODEL_DEVICE = os.getenv("MODEL_DEVICE", "cpu")
IMAGE_STORAGE_DIR = Path(os.getenv("IMAGE_STORAGE_DIR", DEFAULT_IMAGE_STORAGE_DIR))
MAX_IMAGE_SIZE_BYTES = int(os.getenv("MAX_IMAGE_SIZE_BYTES", str(5 * 1024 * 1024)))

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "0123456789012345678901234567890123456789012345678901234567890123",
)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "12"))

APP_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
