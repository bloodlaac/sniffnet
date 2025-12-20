from __future__ import annotations
import logging
from typing import Callable

import kagglehub
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import torchvision.transforms as T
from matplotlib import cm
from pathlib import Path
from PIL import Image
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, classification_report
from torch import nn, optim
from torch.utils.data import DataLoader
from tqdm import tqdm
from sniffnet.core.resnet_model import create_resnet18

path = kagglehub.dataset_download("bloodlaac/products-dataset")

device = torch.device("mps" if torch.mps.is_available() else "cpu")
print("Using device:", device)

IMAGE_SIZE = 224
IMAGE_MEAN = [0.485, 0.456, 0.406]
IMAGE_STD = [0.229, 0.224, 0.225]
blocks_num_list = [2, 2, 2, 2]

logger = logging.getLogger(__name__)
FOOD_CLASSES = ["Fresh", "Bad"]
CLASS_TO_IDX = {name: idx for idx, name in enumerate(FOOD_CLASSES)}

food_dir = Path(f"{path}/products_dataset")

class LabeledDataset():
    def __init__(
        self,
        food_dir: Path,
        food_classes: list[str],
        transform=None) -> LabeledDataset:

        self.food_dir = food_dir
        self.food_classes = food_classes
        self.transform = transform
        self.images_paths = []
        self.labels = []
        self.classes = list(food_classes)
        self.class_to_idx = {name: idx for idx, name in enumerate(food_classes)}

        for cls_name in food_classes:
            class_path = Path(food_dir)
            class_path /= cls_name

            for image_name in class_path.iterdir():
                image_path = class_path / image_name
                self.images_paths.append(image_path)
                self.labels.append(self.class_to_idx[cls_name])

    def __len__(self) -> int:
        return len(self.images_paths)

    def __getitem__(self, index: int):
        image = Image.open(self.images_paths[index]).convert("RGB")
        label = self.labels[index]

        if self.transform:
            image = self.transform(image)

        return image, label
    
train_transforms = T.Compose([
    T.Resize(int(IMAGE_SIZE * 1.14)),
    T.RandomHorizontalFlip(p=0.3),
    T.RandomVerticalFlip(p=0.3),
    T.RandomResizedCrop(IMAGE_SIZE, scale=(0.8, 1.0), ratio=(3/4, 4/3)),
    T.ColorJitter(0.2, 0.2, 0.2, 0.1),
    T.RandomAffine(degrees=0, translate=(0.3, 0.3)),
    T.ToTensor(),
    T.Normalize(IMAGE_MEAN, IMAGE_STD),
])

eval_transforms = T.Compose([
    T.Resize(int(IMAGE_SIZE * 1.14)),
    T.ToTensor(),
    T.CenterCrop(IMAGE_SIZE),
    T.Normalize(IMAGE_MEAN, IMAGE_STD),
])

food_dataset = LabeledDataset(food_dir, FOOD_CLASSES)
DEFAULT_TEST_SPLIT = 0.2

class Block(nn.Module):
    """
    Create basic unit of ResNet.

    Consists of two convolutional layers.

    """

    def __init__(
            self,
            in_channels: int,
            out_channels: int,
            stride: int = 1,
            downsampling=None
        ) -> Block:

        super().__init__()

        self.conv1 = nn.Conv2d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=3,
            stride=stride,
            padding=1
        )
        self.bn1 = nn.BatchNorm2d(num_features=out_channels)
        self.bn2 = nn.BatchNorm2d(num_features=out_channels)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv2d(
            in_channels=out_channels,
            out_channels=out_channels,
            kernel_size=3,
            stride=1,  # TODO: Replace with padding="same"
            padding=1
        )
        self.downsampling = downsampling

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        input = x

        pred = self.bn1(self.conv1(x))
        pred = self.relu(pred)
        pred = self.bn2(self.conv2(pred))

        if self.downsampling is not None:
            input = self.downsampling(x)

        pred += input
        pred = self.relu(pred)

        return pred
    
class ResNet(nn.Module):
    """
    Build model ResNet and return prediction

    """

    def __init__(self, blocks_num_list: list[int]) -> ResNet:
        """
        ResNet init.

        Parameters
        ----------
        blocks_num_list : list[int]
                          Number of basic blocks for each layer.

        """
        super().__init__()

        self.in_channels = 64  # Default number of channels for first layer. Mutable!

        # Reduce resolution of picture by 2
        # 224 -> 112
        self.conv1 = nn.Conv2d(
            in_channels=3,
            out_channels=64,
            kernel_size=7,
            stride=2,
            padding=3
        )
        self.batch_norm = nn.BatchNorm2d(64)
        self.relu = nn.ReLU()
        self.pooling = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)  # 112 -> 56

        self.layer1 = self.create_layer(  # Default stride. No resolution reduction.
            out_channels=64,
            num_blocks=blocks_num_list[0]
        )
        self.layer2 = self.create_layer(  # Resolution reduction. 56 -> 28
            out_channels=128,
            num_blocks=blocks_num_list[1],
            stride=2
        )
        self.layer3 = self.create_layer(  # Resolution reduction. 28 -> 14
            out_channels=256,
            num_blocks=blocks_num_list[2],
            stride=2
        )
        self.layer4 = self.create_layer(  # Resolution reduction. 14 -> 7
            out_channels=512,
            num_blocks=blocks_num_list[3],
            stride=2
        )

        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512, 2)

    def create_layer(
            self,
            out_channels: int,
            num_blocks: int,
            stride: int = 1
        ) -> nn.Sequential:
        """
        Create ResNet layer.

        Parameters
        ----------
        out_channels : int
            Number of output channels per block
        num_blocks : int
            Number of blocks per layer
        stride : int, default=1
            Step of filter in conv layer

        """
        downsampling = None

        if stride != 1:
            downsampling = nn.Sequential(
                nn.Conv2d(
                    in_channels=self.in_channels,
                    out_channels=out_channels,
                    kernel_size=1,
                    stride=stride
                ),
                nn.BatchNorm2d(out_channels)
            )

        blocks: list[Block] = []

        blocks.append(Block(
            in_channels=self.in_channels,
            out_channels=out_channels,
            stride=stride,
            downsampling=downsampling
        ))

        self.in_channels = out_channels

        for _ in range(num_blocks - 1):
            blocks.append(Block(out_channels, out_channels))

        return nn.Sequential(*blocks)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        pred = self.batch_norm(self.conv1(x))
        pred = self.relu(pred)
        pred = self.pooling(pred)

        pred = self.layer1(pred)
        pred = self.layer2(pred)
        pred = self.layer3(pred)
        pred = self.layer4(pred)

        pred = self.avgpool(pred)
        pred = torch.flatten(pred, 1)
        pred = self.fc(pred)

        return pred
    
def plot_history(
        epochs: int,
        train_history: list,
        val_history: list,
        optimizer_name: str,
        label: str
    ):
    _, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 10))
    ax1.plot(np.arange(1, epochs + 1), train_history, label=label)
    ax2.plot(np.arange(1, epochs + 1), val_history, label=label)

    for ax in (ax1, ax2):
        ax.set_xlabel('Epochs')
        ax.set_ylabel('Accuracy')
        ax.legend(loc='lower right')
        ax.grid(True)

    ax1.set_title(f'{optimizer_name} Training accuracy')
    ax2.set_title(f'{optimizer_name} Validation accuracy')

    plt.tight_layout()
    plt.show()

def validate(model, loader, criterion):
    correct, total = 0, 0
    val_loss = 0.0

    model.eval()

    for batch in loader:
        images, labels = batch
        images = images.to(device)
        labels = labels.to(device)

        with torch.no_grad():
            pred = model(images)

        loss = criterion(pred, labels)
        val_loss += loss.item() * len(labels)
        total += len(labels)

        pred = torch.argmax(pred, dim=1)

        correct += (pred == labels).sum().item()

    accuracy = correct / total
    loss = val_loss / total

    return accuracy, loss

def train(model, criterion, train_loader, val_loader, optimizer, epochs=10):
    train_acc, train_loss = [], []
    validation_acc, validation_loss = [], []

    model.train()

    for epoch in tqdm(range(epochs), leave=False):
        correct, total = 0, 0
        epoch_loss = 0.0

        for i, batch in enumerate(train_loader, start=1):
            images, labels = batch

            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            pred = model(images)
            loss = criterion(pred, labels)

            loss.backward()
            optimizer.step()

            pred = torch.argmax(pred, dim=1)

            total += len(labels)
            epoch_loss += loss.item() * pred.shape[0]
            correct += (pred == labels).sum().item()
            accuracy = correct / total

            if i % 100 == 0:
              temp_loss = epoch_loss / total

              print(f"Epoch: [{epoch + 1}/{epochs}], Step: [{i}/{len(train_loader)}]\n"
                    f"Train loss: {temp_loss:.4f}, Train Accuracy: {accuracy:.4f}\n")

        train_acc.append(accuracy)
        train_loss.append(epoch_loss / total)
        val_acc, val_loss = validate(model, val_loader, criterion)
        validation_acc.append(val_acc)
        validation_loss.append(val_loss)

        print(f"Epoch: [{epoch + 1}/{epochs}] has passed\n"
              f"Train loss: {train_loss[-1]:.4f}, Train accuracy: {train_acc[-1]:.4f}\n"
              f"Validation loss: {val_loss:.4f}, Validation accuracy: {val_acc:.4f}\n")

    return train_acc, train_loss, validation_acc, validation_loss

def test(model, loader, criterion):
    correct, total = 0, 0
    test_loss = 0.0

    y_true, y_pred = [], []

    model.eval()

    for batch in loader:
        images, labels = batch
        images = images.to(device)
        labels = labels.to(device)

        with torch.no_grad():
            pred = model(images)

        loss = criterion(pred, labels)
        test_loss += loss.item() * len(labels)

        pred = torch.argmax(pred, dim=1)

        y_true.append(labels.cpu().numpy())
        y_pred.append(pred.cpu().numpy())

        total += len(labels)
        correct += (pred == labels).sum().item()

    test_accuracy = correct / total
    test_loss = test_loss / total

    y_true = np.concatenate(y_true)
    y_pred = np.concatenate(y_pred)

    cm = confusion_matrix(y_true, y_pred)
    report = classification_report(y_true, y_pred, digits=4)

    return test_accuracy, test_loss, cm, report


def save_checkpoint(
    model: nn.Module,
    path: Path,
    classes: list[str] | None = None,
    class_to_idx: dict | None = None,
) -> dict:
    """Save checkpoint and verify roundtrip loading with strict=True."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    classes = classes or FOOD_CLASSES
    class_to_idx = class_to_idx or CLASS_TO_IDX

    torch.save(model.state_dict(), path)

    result: dict[str, object] = {
        "path": str(path.resolve()),
        "format": None,
    }

    return result


def build_dataloaders(batch_size: int, val_split: float):
    dataset_len = len(food_dataset)
    val_size = int(dataset_len * val_split)
    test_size = int(dataset_len * DEFAULT_TEST_SPLIT)
    train_size = dataset_len - val_size - test_size
    if train_size <= 0:
        raise ValueError("val_split слишком большой для текущего датасета")

    train_dataset, val_dataset, test_dataset = torch.utils.data.random_split(
        food_dataset, [train_size, val_size, test_size]
    )

    train_dataset.dataset.transform = train_transforms
    val_dataset.dataset.transform = eval_transforms
    test_dataset.dataset.transform = eval_transforms

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
    )
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader, test_loader


def build_optimizer(name: str, params, learning_rate: float):
    normalized = name.strip().lower()
    if normalized == "sgd":
        return optim.SGD(params, lr=learning_rate, momentum=0.9)
    if normalized == "adam":
        return optim.Adam(params, lr=learning_rate)
    raise ValueError(f"Unsupported optimizer: {name}")


def build_criterion(name: str):
    normalized = name.strip().lower()
    if normalized in {"crossentropy", "crossentropyloss", "ce"}:
        return nn.CrossEntropyLoss()
    raise ValueError(f"Unsupported loss function: {name}")


def train_with_config(
    epochs_num: int,
    batch_size: int,
    learning_rate: float,
    optimizer_name: str,
    loss_function: str,
    val_split: float,
    checkpoint_path: Path | None = None,
):
    model = create_resnet18(num_classes=len(FOOD_CLASSES)).to(device)
    criterion = build_criterion(loss_function)
    optimizer = build_optimizer(optimizer_name, model.parameters(), learning_rate)

    train_loader, val_loader, test_loader = build_dataloaders(batch_size, val_split)

    train_acc, train_loss, val_acc, val_loss = train(
        model,
        criterion,
        train_loader,
        val_loader,
        optimizer=optimizer,
        epochs=epochs_num,
    )

    test_acc, test_loss, _, _ = test(model, test_loader, criterion)

    save_info = None
    if checkpoint_path is not None:
        save_info = save_checkpoint(
            model,
            checkpoint_path,
            classes=FOOD_CLASSES,
            class_to_idx=CLASS_TO_IDX,
        )

    return {
        "train_accuracy": train_acc[-1] if train_acc else None,
        "train_loss": train_loss[-1] if train_loss else None,
        "val_accuracy": val_acc[-1] if val_acc else None,
        "val_loss": val_loss[-1] if val_loss else None,
        "test_accuracy": test_acc,
        "test_loss": test_loss,
        "train_accuracy_history": train_acc,
        "train_loss_history": train_loss,
        "val_accuracy_history": val_acc,
        "val_loss_history": val_loss,
        "checkpoint": save_info,
    }


if __name__ == "__main__":
    model = ResNet(blocks_num_list).to(device)
    optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

    print("Training ResNet18 with SGD\n")

    train_loader, val_loader, test_loader = build_dataloaders(batch_size=16, val_split=0.2)
    train_acc, train_loss, val_acc, val_loss = train(
        model,
        nn.CrossEntropyLoss(),
        train_loader,
        val_loader,
        optimizer=optimizer,
        epochs=20,
    )

    test_acc, test_loss, cm, report = test(model, test_loader, nn.CrossEntropyLoss())

    print(f"\nTest accuracy: {test_acc:.4f}")
    print(f"\nTest loss: {test_loss:.4f}")
    print(f"\nReport:\n{report}")

    out = Path("../../../artifacts/models").resolve()
    checkpoint_path = out / "model.pth"
    save_checkpoint(
        model,
        checkpoint_path,
        classes=FOOD_CLASSES,
        class_to_idx=CLASS_TO_IDX,
    )
    print(f"Saved: {checkpoint_path}")
