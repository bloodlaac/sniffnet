from __future__ import annotations

import pytest

from sniffnet.core.model_loader import _extract_metadata, extract_state_dict


def test_extract_state_dict_supports_supported_checkpoint_shapes() -> None:
    assert extract_state_dict({"model_state": {"layer.weight": 1}}) == ({"layer.weight": 1}, "model_state")
    assert extract_state_dict({"state_dict": {"layer.weight": 1}}) == ({"layer.weight": 1}, "state_dict")
    assert extract_state_dict({"layer.weight": 1}) == ({"layer.weight": 1}, "state_dict_direct")

    with pytest.raises(RuntimeError, match="Unsupported checkpoint format"):
        extract_state_dict(["bad-format"])


def test_extract_metadata_ignores_invalid_values_and_returns_valid_metadata() -> None:
    assert _extract_metadata(
        {"classes": ["Fresh", "Bad"], "class_to_idx": {"Fresh": 0, "Bad": 1}, "num_classes": 2}
    ) == (["Fresh", "Bad"], {"Fresh": 0, "Bad": 1}, 2)
    assert _extract_metadata({"classes": "bad", "class_to_idx": [], "num_classes": "2"}) == (None, None, None)
