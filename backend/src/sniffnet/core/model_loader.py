from __future__ import annotations

import logging
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from sniffnet.core.resnet_model import build_eval_transforms, create_resnet18

import torch


_MODEL = None
_TRANSFORM = None
_DEFAULT_CLASSES = ["Fresh", "Bad"]
_DEFAULT_CLASS_TO_IDX = {"Fresh": 0, "Bad": 1}
_CLASSES = list(_DEFAULT_CLASSES)
_CLASS_TO_IDX = dict(_DEFAULT_CLASS_TO_IDX)
_LOAD_THREAD = None
_LOAD_ERROR = None
_MODEL_HEALTH = None
_CURRENT_WEIGHTS_PATH = None
_LOCK = threading.Lock()
_LOGGER = logging.getLogger(__name__)


def extract_state_dict(checkpoint: Any) -> tuple[dict[str, Any], str]:
    """Normalize checkpoint formats to a state_dict and return its source tag."""
    if isinstance(checkpoint, dict):
        if "model_state" in checkpoint:
            return checkpoint["model_state"], "model_state"
        if "state_dict" in checkpoint:
            return checkpoint["state_dict"], "state_dict"
        return checkpoint, "state_dict_direct"
    raise RuntimeError("Unsupported checkpoint format: expected dict or state_dict")


def _extract_metadata(checkpoint: Any) -> tuple[list[str] | None, dict[str, int] | None, int | None]:
    if not isinstance(checkpoint, dict):
        return None, None, None

    classes = checkpoint.get("classes")
    class_to_idx = checkpoint.get("class_to_idx")
    num_classes = checkpoint.get("num_classes")

    if classes is not None and not isinstance(classes, list):
        _LOGGER.warning("Invalid classes type in checkpoint (%s); ignoring", type(classes))
        classes = None

    if class_to_idx is not None and not isinstance(class_to_idx, dict):
        _LOGGER.warning(
            "Invalid class_to_idx type in checkpoint (%s); ignoring",
            type(class_to_idx),
        )
        class_to_idx = None

    if num_classes is not None and not isinstance(num_classes, int):
        _LOGGER.warning("Invalid num_classes type in checkpoint (%s); ignoring", type(num_classes))
        num_classes = None

    return classes, class_to_idx, num_classes


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
            target=_load_worker,
            args=(weights_path, device),
            daemon=True,
        )
        _LOAD_THREAD.start()
        return True


def _load_model(weights_path: str, device: str):
    torch_device = torch.device(device)
    weights_file = Path(weights_path).expanduser().resolve()
    checkpoint = torch.load(weights_file, map_location=torch_device)

    classes, class_to_idx, checkpoint_num_classes = _extract_metadata(checkpoint)
    resolved_classes = classes if classes else list(_DEFAULT_CLASSES)
    resolved_class_to_idx = class_to_idx if class_to_idx else dict(_DEFAULT_CLASS_TO_IDX)
    num_classes = checkpoint_num_classes or len(resolved_classes)

    model = create_resnet18(num_classes=num_classes)
    state_dict, checkpoint_format = extract_state_dict(checkpoint)
    _LOGGER.info("Checkpoint format detected: %s", checkpoint_format)

    try:
        model.load_state_dict(state_dict, strict=True)
    except Exception as exc:
        raise RuntimeError(f"load_state_dict failed with strict=True: {exc}") from exc

    model.to(torch_device)
    model.eval()
    transform = build_eval_transforms()

    health = {
        "weights_path": str(weights_file),
        "device": str(torch_device),
        "loaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "checkpoint_format": checkpoint_format,
        "num_classes": num_classes,
        "classes": list(resolved_classes),
    }

    return model, transform, resolved_classes, resolved_class_to_idx, health


def _load_worker(weights_path: str, device: str) -> None:
    """Load model weights and preprocessing pipeline in a background thread."""
    global _MODEL, _TRANSFORM, _CLASSES, _CLASS_TO_IDX
    global _LOAD_ERROR, _MODEL_HEALTH, _CURRENT_WEIGHTS_PATH

    try:
        model, transform, classes, class_to_idx, health = _load_model(weights_path, device)

        with _LOCK:
            _MODEL = model
            _TRANSFORM = transform
            _CLASSES = classes
            _CLASS_TO_IDX = class_to_idx
            _MODEL_HEALTH = health
            _LOAD_ERROR = None
            _CURRENT_WEIGHTS_PATH = str(Path(weights_path).expanduser().resolve())
    except Exception:
        _LOGGER.exception("Failed to load model from %s", weights_path)
        with _LOCK:
            _MODEL = None
            _TRANSFORM = None
            _CLASSES = list(_DEFAULT_CLASSES)
            _CLASS_TO_IDX = dict(_DEFAULT_CLASS_TO_IDX)
            _MODEL_HEALTH = None
            _LOAD_ERROR = traceback.format_exc()
            _CURRENT_WEIGHTS_PATH = None


def get_model_blocking(timeout: float | None = None):
    """Wait for model to finish loading (up to timeout) and return it."""
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

        return _MODEL, _TRANSFORM, list(_CLASSES)


def load_model_for_weights(weights_path: str, device: str):
    global _MODEL, _TRANSFORM, _CLASSES, _CLASS_TO_IDX
    global _LOAD_ERROR, _MODEL_HEALTH, _CURRENT_WEIGHTS_PATH

    resolved = str(Path(weights_path).expanduser().resolve())

    with _LOCK:
        if _MODEL is not None and _CURRENT_WEIGHTS_PATH == resolved:
            return _MODEL, _TRANSFORM, list(_CLASSES)

    model, transform, classes, class_to_idx, health = _load_model(resolved, device)

    with _LOCK:
        _MODEL = model
        _TRANSFORM = transform
        _CLASSES = classes
        _CLASS_TO_IDX = class_to_idx
        _MODEL_HEALTH = health
        _LOAD_ERROR = None
        _CURRENT_WEIGHTS_PATH = resolved

    return model, transform, list(classes)


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


def get_classes() -> list[str]:
    with _LOCK:
        return list(_CLASSES)


def get_class_to_idx() -> dict[str, int]:
    with _LOCK:
        return dict(_CLASS_TO_IDX)
