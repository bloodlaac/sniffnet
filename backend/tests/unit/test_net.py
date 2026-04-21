from __future__ import annotations

import pytest
import torch
from torch import nn
from torch.optim import Adam, SGD

from sniffnet.core.net import _split_indices, build_criterion, build_optimizer, save_checkpoint


def test_split_indices_is_deterministic_and_covers_dataset() -> None:
    train, val, test = _split_indices(dataset_len=10, train_split=0.6, val_split=0.2, seed=42)

    assert len(train) == 6
    assert len(val) == 2
    assert len(test) == 2
    assert sorted(train + val + test) == list(range(10))
    assert (train, val, test) == _split_indices(dataset_len=10, train_split=0.6, val_split=0.2, seed=42)


def test_split_indices_rejects_invalid_split_configurations() -> None:
    cases = [
        ({"dataset_len": 0, "train_split": 0.6, "val_split": 0.2, "seed": 1}, "Dataset is empty"),
        ({"dataset_len": 4, "train_split": 0.8, "val_split": 0.2, "seed": 1}, "must be less than 1"),
        ({"dataset_len": 3, "train_split": 0.6, "val_split": 0.2, "seed": 1}, "empty subset"),
    ]

    for kwargs, message in cases:
        with pytest.raises(ValueError, match=message):
            _split_indices(**kwargs)


def test_build_optimizer_and_criterion_support_expected_names() -> None:
    params = nn.Linear(4, 2).parameters()

    assert isinstance(build_optimizer("sgd", params, 0.01), SGD)
    assert isinstance(build_optimizer("Adam", nn.Linear(4, 2).parameters(), 0.01), Adam)
    assert build_criterion("CrossEntropyLoss").__class__.__name__ == "CrossEntropyLoss"

    with pytest.raises(ValueError, match="Unsupported optimizer"):
        build_optimizer("RMSProp", nn.Linear(4, 2).parameters(), 0.01)
    with pytest.raises(ValueError, match="Unsupported loss function"):
        build_criterion("MSELoss")


def test_save_checkpoint_persists_metadata_in_tmp_path(tmp_path) -> None:
    checkpoint_path = tmp_path / "checkpoints" / "model.pth"
    model = nn.Linear(4, 2)

    info = save_checkpoint(model, checkpoint_path, classes=["Fresh", "Bad"], class_to_idx={"Fresh": 0, "Bad": 1})
    payload = torch.load(checkpoint_path, map_location="cpu")

    assert checkpoint_path.exists() is True
    assert info["format"] == "checkpoint_dict"
    assert payload["classes"] == ["Fresh", "Bad"]
    assert payload["class_to_idx"] == {"Fresh": 0, "Bad": 1}
    assert payload["num_classes"] == 2
