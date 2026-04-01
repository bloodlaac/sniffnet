from __future__ import annotations

import copy
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, confusion_matrix
from torch import nn, optim
from torch.utils.data import DataLoader, Dataset, Subset
from tqdm import tqdm

from sniffnet.core.resnet_model import (
    IMAGE_MEAN,
    IMAGE_SIZE,
    IMAGE_STD,
    build_eval_transforms,
    build_train_transforms,
    create_resnet18,
)

LOGGER = logging.getLogger(__name__)
FOOD_CLASSES = ["Fresh", "Bad"]
CLASS_TO_IDX = {name: idx for idx, name in enumerate(FOOD_CLASSES)}
DEFAULT_TRAIN_SPLIT = 0.6
DEFAULT_VAL_SPLIT = 0.2
DEFAULT_SEED = 42
DEFAULT_DATASET_DIR = (Path(__file__).resolve().parents[5] / "datasets" / "v3").resolve()

torch.manual_seed(DEFAULT_SEED)
np.random.seed(DEFAULT_SEED)


def get_default_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


device = get_default_device()


class LabeledDataset(Dataset):
    def __init__(
        self,
        food_dir: Path,
        food_classes: list[str],
        transform=None,
    ) -> None:
        self.food_dir = Path(food_dir)
        self.food_classes = list(food_classes)
        self.transform = transform
        self.images_paths: list[Path] = []
        self.labels: list[int] = []
        self.classes = list(food_classes)
        self.class_to_idx = {name: idx for idx, name in enumerate(food_classes)}

        for cls_name in self.food_classes:
            class_path = self.food_dir / cls_name
            if not class_path.exists():
                raise FileNotFoundError(f"Class directory not found: {class_path}")

            for image_path in sorted(class_path.iterdir()):
                if image_path.is_file():
                    self.images_paths.append(image_path)
                    self.labels.append(self.class_to_idx[cls_name])

    def __len__(self) -> int:
        return len(self.images_paths)

    def __getitem__(self, index: int):
        image = Image.open(self.images_paths[index]).convert("RGB")
        label = self.labels[index]

        if self.transform is not None:
            image = self.transform(image)

        return image, label


def resolve_food_dir(food_dir: Path | str | None = None) -> Path:
    resolved = Path(food_dir or DEFAULT_DATASET_DIR).expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Dataset directory not found: {resolved}")
    missing_classes = [cls_name for cls_name in FOOD_CLASSES if not (resolved / cls_name).exists()]
    if missing_classes:
        raise FileNotFoundError(
            f"Dataset directory {resolved} is missing class folders: {', '.join(missing_classes)}"
        )
    return resolved


def _split_indices(
    dataset_len: int,
    train_split: float,
    val_split: float,
    seed: int,
) -> tuple[list[int], list[int], list[int]]:
    if dataset_len <= 0:
        raise ValueError("Dataset is empty.")
    if not (0 < train_split < 1):
        raise ValueError("train_split must be between 0 and 1.")
    if not (0 < val_split < 1):
        raise ValueError("val_split must be between 0 and 1.")
    if train_split + val_split >= 1:
        raise ValueError("train_split + val_split must be less than 1.")

    test_split = 1.0 - train_split - val_split
    train_size = int(train_split * dataset_len)
    val_size = int(val_split * dataset_len)
    test_size = dataset_len - train_size - val_size

    if min(train_size, val_size, test_size) <= 0:
        raise ValueError(
            "Split configuration leaves an empty subset. "
            f"train={train_size}, val={val_size}, test={test_size}"
        )

    generator = torch.Generator().manual_seed(seed)
    indices = torch.randperm(dataset_len, generator=generator).tolist()

    train_indices = indices[:train_size]
    val_indices = indices[train_size : train_size + val_size]
    test_indices = indices[train_size + val_size :]
    
    return train_indices, val_indices, test_indices


def build_dataloaders(
    food_dir: Path | str | None = None,
    batch_size: int = 16,
    train_split: float = DEFAULT_TRAIN_SPLIT,
    val_split: float = DEFAULT_VAL_SPLIT,
    seed: int = DEFAULT_SEED,
    num_workers: int = 0,
    pin_memory: bool | None = None,
):
    resolved_food_dir = resolve_food_dir(food_dir)

    base_dataset = LabeledDataset(resolved_food_dir, FOOD_CLASSES, transform=None)
    train_indices, val_indices, test_indices = _split_indices(
        len(base_dataset),
        train_split=train_split,
        val_split=val_split,
        seed=seed,
    )

    train_dataset = Subset(
        LabeledDataset(
            resolved_food_dir,
            FOOD_CLASSES,
            transform=build_train_transforms(),
        ),
        train_indices,
    )
    val_dataset = Subset(
        LabeledDataset(
            resolved_food_dir,
            FOOD_CLASSES,
            transform=build_eval_transforms(),
        ),
        val_indices,
    )
    test_dataset = Subset(
        LabeledDataset(
            resolved_food_dir,
            FOOD_CLASSES,
            transform=build_eval_transforms(),
        ),
        test_indices,
    )

    if pin_memory is None:
        pin_memory = device.type == "cuda"

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=max(batch_size, 64),
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=max(batch_size, 64),
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )

    return train_loader, val_loader, test_loader


def plot_history(
    epochs: int,
    train_history: list[float],
    val_history: list[float],
    optimizer_name: str,
    label: str,
) -> None:
    _, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 10))
    ax1.plot(np.arange(1, epochs + 1), train_history, label=label)
    ax2.plot(np.arange(1, epochs + 1), val_history, label=label)

    for axis in (ax1, ax2):
        axis.set_xlabel("Epochs")
        axis.set_ylabel("Accuracy")
        axis.legend(loc="lower right")
        axis.grid(True)

    ax1.set_title(f"{optimizer_name} Training accuracy")
    ax2.set_title(f"{optimizer_name} Validation accuracy")
    plt.tight_layout()
    plt.show()


def validate(model, loader, criterion):
    correct, total = 0, 0
    val_loss = 0.0

    model.eval()

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        with torch.no_grad():
            logits = model(images)

        loss = criterion(logits, labels)
        val_loss += loss.item() * len(labels)
        total += len(labels)

        predictions = torch.argmax(logits, dim=1)
        correct += (predictions == labels).sum().item()

    accuracy = correct / total
    loss = val_loss / total
    return accuracy, loss


def train(
    model,
    criterion,
    train_loader,
    val_loader,
    optimizer,
    epochs: int = 10,
    patience: int = 5,
    min_delta: float = 0.0,
):
    train_acc, train_loss = [], []
    validation_acc, validation_loss = [], []

    best_val_loss = float("inf")
    best_model_state = copy.deepcopy(model.state_dict())
    epochs_without_improvement = 0

    for epoch in tqdm(range(epochs), leave=False):
        model.train()

        correct, total = 0, 0
        epoch_loss = 0.0

        for step, (images, labels) in enumerate(train_loader, start=1):
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)

            loss.backward()
            optimizer.step()

            predictions = torch.argmax(logits, dim=1)

            total += len(labels)
            epoch_loss += loss.item() * len(labels)
            correct += (predictions == labels).sum().item()
            accuracy = correct / total

            if step % 100 == 0:
                temp_loss = epoch_loss / total
                print(
                    f"Epoch: [{epoch + 1}/{epochs}], "
                    f"Step: [{step}/{len(train_loader)}]\n"
                    f"Train loss: {temp_loss:.4f}, "
                    f"Train Accuracy: {accuracy:.4f}\n"
                )

        train_acc.append(accuracy)
        train_loss.append(epoch_loss / total)

        val_acc, val_loss = validate(model, val_loader, criterion)
        validation_acc.append(val_acc)
        validation_loss.append(val_loss)

        print(
            f"Epoch: [{epoch + 1}/{epochs}] has passed\n"
            f"Train loss: {train_loss[-1]:.4f}, "
            f"Train accuracy: {train_acc[-1]:.4f}\n"
            f"Validation loss: {val_loss:.4f}, "
            f"Validation accuracy: {val_acc:.4f}\n"
        )

        if val_loss < best_val_loss - min_delta:
            best_val_loss = val_loss
            best_model_state = copy.deepcopy(model.state_dict())
            epochs_without_improvement = 0
            print(
                f"Validation loss improved to {best_val_loss:.4f}. "
                "Best model updated.\n"
            )
        else:
            epochs_without_improvement += 1
            print(
                f"No improvement for {epochs_without_improvement} epoch(s). "
                f"Patience: {patience}\n"
            )

            if epochs_without_improvement >= patience:
                print(f"Early stopping triggered at epoch {epoch + 1}\n")
                break

    model.load_state_dict(best_model_state)
    return train_acc, train_loss, validation_acc, validation_loss


def test(model, loader, criterion):
    correct, total = 0, 0
    test_loss = 0.0
    y_true, y_pred = [], []

    model.eval()

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        with torch.no_grad():
            logits = model(images)

        loss = criterion(logits, labels)
        test_loss += loss.item() * len(labels)

        predictions = torch.argmax(logits, dim=1)

        y_true.append(labels.cpu().numpy())
        y_pred.append(predictions.cpu().numpy())

        total += len(labels)
        correct += (predictions == labels).sum().item()

    test_accuracy = correct / total
    test_loss = test_loss / total

    y_true = np.concatenate(y_true)
    y_pred = np.concatenate(y_pred)

    cm = confusion_matrix(y_true, y_pred)
    report = classification_report(y_true, y_pred, digits=4)

    return test_accuracy, test_loss, cm, report


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


def save_checkpoint(
    model: nn.Module,
    path: Path | str,
    classes: list[str] | None = None,
    class_to_idx: dict[str, int] | None = None,
) -> dict:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    classes = classes or FOOD_CLASSES
    class_to_idx = class_to_idx or CLASS_TO_IDX

    checkpoint = {
        "model_state": model.state_dict(),
        "classes": classes,
        "class_to_idx": class_to_idx,
        "num_classes": len(classes),
        "image_size": IMAGE_SIZE,
        "image_mean": list(IMAGE_MEAN),
        "image_std": list(IMAGE_STD),
    }
    torch.save(checkpoint, path)

    return {
        "path": str(path.resolve()),
        "format": "checkpoint_dict",
    }


def train_with_config(
    epochs_num: int,
    batch_size: int,
    learning_rate: float,
    optimizer_name: str,
    loss_function: str,
    val_split: float,
    checkpoint_path: Path | None = None,
    food_dir: Path | str | None = None,
    patience: int = 5,
    min_delta: float = 0.001,
):
    train_split = 1.0 - val_split - 0.2
    if train_split <= 0:
        raise ValueError("val_split is too large for the fixed 20% test split.")

    model = create_resnet18(num_classes=len(FOOD_CLASSES)).to(device)
    params_num = sum(param.numel() for param in model.parameters())
    criterion = build_criterion(loss_function)
    optimizer = build_optimizer(optimizer_name, model.parameters(), learning_rate)

    train_loader, val_loader, test_loader = build_dataloaders(
        food_dir=food_dir,
        batch_size=batch_size,
        train_split=train_split,
        val_split=val_split,
    )

    train_acc, train_loss, val_acc, val_loss = train(
        model,
        criterion,
        train_loader,
        val_loader,
        optimizer=optimizer,
        epochs=epochs_num,
        patience=patience,
        min_delta=min_delta,
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
        "params_num": params_num,
        "test_accuracy": test_acc,
        "test_loss": test_loss,
        "train_accuracy_history": train_acc,
        "train_loss_history": train_loss,
        "val_accuracy_history": val_acc,
        "val_loss_history": val_loss,
        "checkpoint": save_info,
    }


def predict_image(model, image_path: str | Path):
    image = Image.open(image_path).convert("RGB")
    x = build_eval_transforms()(image).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(x)
        probs = F.softmax(logits, dim=1)

    pred_idx = torch.argmax(probs, dim=1).item()
    pred_class = FOOD_CLASSES[pred_idx]
    pred_conf = probs[0, pred_idx].item()

    all_probs = {
        FOOD_CLASSES[i]: float(probs[0, i].item())
        for i in range(len(FOOD_CLASSES))
    }

    return {
        "predicted_class": pred_class,
        "confidence": pred_conf,
        "probabilities": all_probs,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Using device:", device)

    model = create_resnet18(num_classes=len(FOOD_CLASSES)).to(device)
    optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
    criterion = nn.CrossEntropyLoss()

    train_loader, val_loader, test_loader = build_dataloaders(batch_size=16)

    print("Training ResNet18 v3 with SGD\n")
    train_acc, train_loss, val_acc, val_loss = train(
        model,
        criterion,
        train_loader,
        val_loader,
        optimizer=optimizer,
        epochs=20,
        patience=5,
        min_delta=0.001,
    )

    test_acc, test_loss, cm, report = test(model, test_loader, criterion)

    print(f"\nTest accuracy: {test_acc:.4f}")
    print(f"\nTest loss: {test_loss:.4f}")
    print(f"\nReport:\n{report}")

    fig, ax = plt.subplots(figsize=(12, 12))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=FOOD_CLASSES)
    disp.plot(ax=ax, cmap=plt.cm.Blues, colorbar=False)
    ax.set_title("Confusion Matrix")
    plt.tight_layout()
    plt.show()

    checkpoint_path = Path("model_v3.pth")
    save_info = save_checkpoint(
        model,
        checkpoint_path,
        classes=FOOD_CLASSES,
        class_to_idx=CLASS_TO_IDX,
    )
    print(f"Saved: {save_info['path']}")
