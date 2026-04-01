from __future__ import annotations

from collections.abc import Sequence

import torch
import torchvision.transforms as T
from torch import nn
from torchvision.transforms import InterpolationMode

IMAGE_SIZE = 224
IMAGE_MEAN = [0.485, 0.456, 0.406]
IMAGE_STD = [0.229, 0.224, 0.225]
DEFAULT_BLOCKS_NUM = (2, 2, 2, 2)


def build_fill_value(image_mean: Sequence[float] = IMAGE_MEAN) -> tuple[int, int, int]:
    return tuple(int(255 * value) for value in image_mean)


def build_train_transforms(
    image_size: int = IMAGE_SIZE,
    image_mean: Sequence[float] = IMAGE_MEAN,
    image_std: Sequence[float] = IMAGE_STD,
) -> T.Compose:
    fill = build_fill_value(image_mean)

    return T.Compose(
        [
            T.Resize(
                int(image_size * 1.20),
                interpolation=InterpolationMode.BILINEAR,
            ),
            T.RandomApply(
                [
                    T.RandomRotation(
                        degrees=180,
                        interpolation=InterpolationMode.BILINEAR,
                        expand=True,
                        fill=fill,
                    )
                ],
                p=0.7,
            ),
            T.RandomResizedCrop(
                image_size,
                scale=(0.80, 1.00),
                ratio=(0.90, 1.10),
                interpolation=InterpolationMode.BILINEAR,
                antialias=True,
            ),
            T.RandomHorizontalFlip(p=0.3),
            T.RandomApply(
                [
                    T.RandomPerspective(
                        distortion_scale=0.12,
                        p=1.0,
                        interpolation=InterpolationMode.BILINEAR,
                        fill=fill,
                    )
                ],
                p=0.15,
            ),
            T.ColorJitter(
                brightness=0.15,
                contrast=0.15,
                saturation=0.10,
                hue=0.03,
            ),
            T.RandomAffine(
                degrees=0,
                translate=(0.08, 0.08),
                scale=(0.95, 1.05),
                shear=(-4, 4),
                interpolation=InterpolationMode.BILINEAR,
                fill=fill,
            ),
            T.ToTensor(),
            T.Normalize(image_mean, image_std),
        ]
    )


def build_eval_transforms(
    image_size: int = IMAGE_SIZE,
    image_mean: Sequence[float] = IMAGE_MEAN,
    image_std: Sequence[float] = IMAGE_STD,
) -> T.Compose:
    return T.Compose(
        [
            T.Resize(
                (image_size, image_size),
                interpolation=InterpolationMode.BILINEAR,
            ),
            T.ToTensor(),
            T.Normalize(image_mean, image_std),
        ]
    )


class Block(nn.Module):
    """Basic residual block with optional downsampling."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        stride: int = 1,
        downsampling: nn.Module | None = None,
    ) -> None:
        super().__init__()

        self.conv1 = nn.Conv2d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=3,
            stride=stride,
            padding=1,
        )
        self.bn1 = nn.BatchNorm2d(num_features=out_channels)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv2d(
            in_channels=out_channels,
            out_channels=out_channels,
            kernel_size=3,
            stride=1,
            padding=1,
        )
        self.bn2 = nn.BatchNorm2d(num_features=out_channels)
        self.downsampling = downsampling

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        shortcut = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsampling is not None:
            shortcut = self.downsampling(x)

        out += shortcut
        out = self.relu(out)
        return out


class ResNet(nn.Module):
    """ResNet architecture extracted from net_v3.html and cleaned into a module."""

    def __init__(
        self,
        blocks_num_list: Sequence[int] = DEFAULT_BLOCKS_NUM,
        num_classes: int = 2,
    ) -> None:
        super().__init__()

        self.in_channels = 64

        self.conv1 = nn.Conv2d(
            in_channels=3,
            out_channels=64,
            kernel_size=7,
            stride=2,
            padding=3,
        )
        self.batch_norm = nn.BatchNorm2d(64)
        self.relu = nn.ReLU()
        self.pooling = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        self.layer1 = self.create_layer(out_channels=64, num_blocks=blocks_num_list[0])
        self.layer2 = self.create_layer(
            out_channels=128,
            num_blocks=blocks_num_list[1],
            stride=2,
        )
        self.layer3 = self.create_layer(
            out_channels=256,
            num_blocks=blocks_num_list[2],
            stride=2,
        )
        self.layer4 = self.create_layer(
            out_channels=512,
            num_blocks=blocks_num_list[3],
            stride=2,
        )

        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512, num_classes)

    def create_layer(
        self,
        out_channels: int,
        num_blocks: int,
        stride: int = 1,
    ) -> nn.Sequential:
        downsampling = None

        if stride != 1:
            downsampling = nn.Sequential(
                nn.Conv2d(
                    in_channels=self.in_channels,
                    out_channels=out_channels,
                    kernel_size=1,
                    stride=stride,
                ),
                nn.BatchNorm2d(out_channels),
            )

        blocks: list[Block] = [
            Block(
                in_channels=self.in_channels,
                out_channels=out_channels,
                stride=stride,
                downsampling=downsampling,
            )
        ]

        self.in_channels = out_channels

        for _ in range(num_blocks - 1):
            blocks.append(Block(out_channels, out_channels))

        return nn.Sequential(*blocks)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.conv1(x)
        out = self.batch_norm(out)
        out = self.relu(out)
        out = self.pooling(out)

        out = self.layer1(out)
        out = self.layer2(out)
        out = self.layer3(out)
        out = self.layer4(out)

        out = self.avgpool(out)
        out = torch.flatten(out, 1)
        out = self.fc(out)
        return out


def create_resnet18(num_classes: int = 2) -> ResNet:
    return ResNet(DEFAULT_BLOCKS_NUM, num_classes=num_classes)


__all__ = [
    "IMAGE_SIZE",
    "IMAGE_MEAN",
    "IMAGE_STD",
    "DEFAULT_BLOCKS_NUM",
    "build_fill_value",
    "build_train_transforms",
    "build_eval_transforms",
    "Block",
    "ResNet",
    "create_resnet18",
]
