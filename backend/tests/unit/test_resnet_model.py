from __future__ import annotations

import torch
from torchvision.transforms import Normalize, Resize

from sniffnet.core.resnet_model import build_eval_transforms, build_fill_value, create_resnet18


def test_resnet_helpers_and_forward_produce_expected_shapes() -> None:
    transforms = build_eval_transforms()
    model = create_resnet18(num_classes=2)
    output = model(torch.randn(2, 3, 224, 224))

    assert build_fill_value([0.5, 0.25, 0.0]) == (127, 63, 0)
    assert isinstance(transforms.transforms[0], Resize)
    assert isinstance(transforms.transforms[-1], Normalize)
    assert tuple(output.shape) == (2, 2)
