import logging
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

import torch
from torchvision import transforms

from sniffnet.core.resnet_model import create_resnet18

_MODEL = None
_TRANSFORM = None
_DEFAULT_CLASSES = ["Fresh", "Bad"]
_DEFAULT_CLASS_TO_IDX = {"Fresh": 0, "Bad": 1}
_CLASSES = list(_DEFAULT_CLASSES)
_CLASS_TO_IDX = dict(_DEFAULT_CLASS_TO_IDX)
_LOAD_THREAD = None
_LOAD_ERROR = None
_MODEL_HEALTH = None
_LOCK = threading.Lock()
_LOGGER = logging.getLogger(__name__)


def extract_state_dict(checkpoint) -> tuple[dict, str]:
    """Normalize checkpoint formats to a state_dict and return its source tag."""
    if isinstance(checkpoint, dict):
        if "model_state" in checkpoint:
            return checkpoint["model_state"], "model_state"
        if "state_dict" in checkpoint:
            return checkpoint["state_dict"], "state_dict"
        return checkpoint, "state_dict_direct"
    raise RuntimeError("Unsupported checkpoint format: expected dict or state_dict")


def start_load(weights_path: str, device: str) -> bool:
    """Kick off background weight loading if not already in progress or loaded."""
    global _LOAD_THREAD, _LOAD_ERROR
    with _LOCK:
        if _MODEL is not None:
            return False
        if _LOAD_THREAD is not None and _LOAD_THREAD.is_alive():
            return False

        _LOAD_ERROR = None
        _LOAD_THREAD = threading.Thread(
            target=_load_worker, args=(weights_path, device), daemon=True
        )
        _LOAD_THREAD.start()
        return True


def _load_worker(weights_path: str, device: str) -> None:
    """Load model weights and preprocessing pipeline in a background thread."""
    global _MODEL, _TRANSFORM, _LOAD_ERROR, _MODEL_HEALTH
    try:
        torch_device = torch.device(device)
        weights_file = Path(weights_path).expanduser().resolve()

        model = create_resnet18(num_classes=2)
        checkpoint = torch.load(weights_file, map_location=torch_device)

        state_dict, checkpoint_format = extract_state_dict(checkpoint)
        _LOGGER.info("Checkpoint format detected: %s", checkpoint_format)

        classes = None
        class_to_idx = None
        if isinstance(checkpoint, dict):
            classes = checkpoint.get("classes")
            class_to_idx = checkpoint.get("class_to_idx")
            if classes is not None and not isinstance(classes, list):
                _LOGGER.warning("Invalid classes type in checkpoint (%s); ignoring", type(classes))
                classes = None
            if class_to_idx is not None and not isinstance(class_to_idx, dict):
                _LOGGER.warning("Invalid class_to_idx type in checkpoint (%s); ignoring", type(class_to_idx))
                class_to_idx = None

        try:
            model.load_state_dict(state_dict, strict=True)
        except Exception as exc:
            raise RuntimeError(f"load_state_dict failed with strict=True: {exc}") from exc
        model.to(torch_device)
        model.eval()

        loaded_classes = classes if classes else list(_DEFAULT_CLASSES)
        loaded_class_to_idx = class_to_idx if class_to_idx else dict(_DEFAULT_CLASS_TO_IDX)
        if classes is None:
            _LOGGER.warning("classes not found in checkpoint; using fallback order %s", loaded_classes)
        if class_to_idx is None:
            _LOGGER.warning("class_to_idx not found in checkpoint; using fallback mapping %s", loaded_class_to_idx)

        transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

        with _LOCK:
            _MODEL = model
            _TRANSFORM = transform
            _LOAD_ERROR = None
            _CLASSES = loaded_classes
            _CLASS_TO_IDX = loaded_class_to_idx

    except Exception:
        _LOGGER.exception("Failed to load model from %s", weights_path)
        with _LOCK:
            _MODEL = None
            _TRANSFORM = None
            _LOAD_ERROR = traceback.format_exc()


def get_model_blocking(timeout: float | None = None) -> Tuple[torch.nn.Module, transforms.Compose, List[str]]:
    """Wait for model to finish loading (up to timeout) and return it."""
    thread = None
    with _LOCK:
        thread = _LOAD_THREAD
        model_ready = _MODEL is not None

    if not model_ready and thread is not None and thread.is_alive():
        thread.join(timeout=timeout)

    with _LOCK:
        if _LOAD_ERROR:
            raise RuntimeError(_LOAD_ERROR)

        if _MODEL is None:
            if _LOAD_THREAD is not None and _LOAD_THREAD.is_alive():
                raise RuntimeError("loading in progress")
            raise RuntimeError("model not loaded")

        return _MODEL, _TRANSFORM, _CLASSES


def is_loaded() -> bool:
    with _LOCK:
        return _MODEL is not None


def is_loading() -> bool:
    with _LOCK:
        return _LOAD_THREAD is not None and _LOAD_THREAD.is_alive()


def get_model_health() -> dict:
    with _LOCK:
        if _LOAD_ERROR:
            raise RuntimeError(_LOAD_ERROR)
        if _MODEL is None or _MODEL_HEALTH is None:
            if _LOAD_THREAD is not None and _LOAD_THREAD.is_alive():
                raise RuntimeError("loading in progress")
            raise RuntimeError("model not loaded")
        return dict(_MODEL_HEALTH)


def get_classes() -> List[str]:
    with _LOCK:
        return list(_CLASSES)


def get_class_to_idx() -> dict:
    with _LOCK:
        return dict(_CLASS_TO_IDX)
