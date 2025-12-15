import os
from pathlib import Path

DEFAULT_WEIGHTS_PATH = Path(__file__).resolve().parents[3] / "artifacts" / "models" / "model.pth"

MODEL_WEIGHTS_PATH = Path(os.getenv("MODEL_WEIGHTS_PATH", DEFAULT_WEIGHTS_PATH))
MODEL_DEVICE = os.getenv("MODEL_DEVICE", "cpu")
