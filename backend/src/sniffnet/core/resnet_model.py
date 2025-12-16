import torch
from torch import nn


class Block(nn.Module):
    """Basic residual block with optional downsampling."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        stride: int = 1,
        downsampling=None,
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
        self.bn2 = nn.BatchNorm2d(num_features=out_channels)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv2d(
            in_channels=out_channels,
            out_channels=out_channels,
            kernel_size=3,
            stride=1,
            padding=1,
        )
        self.downsampling = downsampling

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        shortcut = x

        out = self.bn1(self.conv1(x))
        out = self.relu(out)
        out = self.bn2(self.conv2(out))

        if self.downsampling is not None:
            shortcut = self.downsampling(x)

        out += shortcut
        out = self.relu(out)

        return out


class ResNet(nn.Module):
    """Minimal ResNet implementation tailored for 224x224 inputs."""

    def __init__(self, blocks_num_list: list[int], num_classes: int = 2) -> None:
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
        self.layer2 = self.create_layer(out_channels=128, num_blocks=blocks_num_list[1], stride=2)
        self.layer3 = self.create_layer(out_channels=256, num_blocks=blocks_num_list[2], stride=2)
        self.layer4 = self.create_layer(out_channels=512, num_blocks=blocks_num_list[3], stride=2)

        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512, num_classes)

    def create_layer(self, out_channels: int, num_blocks: int, stride: int = 1) -> nn.Sequential:
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
        out = self.batch_norm(self.conv1(x))
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
    """Factory for a ResNet-18 style model."""
    return ResNet([2, 2, 2, 2], num_classes=num_classes)
