from __future__ import annotations

from datetime import datetime, timezone

from sniffnet.api.mappers import to_classification_response, to_experiment_response
from sniffnet.database.db_models import ClassificationRequest, Dataset, Experiment, Metric, Model, Role, TrainingConfig, UploadedImage, User


def test_mappers_build_experiment_and_classification_contracts() -> None:
    now = datetime.now(timezone.utc)
    role = Role(id=1, code="ROLE_USER", name="User")
    user = User(id=2, username="demo", email="demo@sniffnet.local", password="hash", role=role, created_at=now)
    dataset = Dataset(id=3, name="Products Dataset", classes_num=2, source="/tmp/dataset")
    config = TrainingConfig(
        id=4,
        epochs_num=5,
        batch_size=8,
        learning_rate=0.01,
        optimizer="Adam",
        loss_function="CrossEntropyLoss",
        validation_split=0.2,
        layers_num=2,
        neurons_num=32,
    )
    experiment = Experiment(id=5, dataset_id=dataset.id, config_id=config.id, user_id=user.id, status="COMPLETED", start_time=now)
    experiment.dataset = dataset
    experiment.config = config
    experiment.user = user

    model = Model(
        id=6,
        name="model6",
        dataset_id=dataset.id,
        config_id=config.id,
        experiment_id=experiment.id,
        params_num=123,
        training_time_seconds=10,
        available_for_inference=True,
        weights_path="model6.pth",
        created_at=now,
    )
    model.dataset = dataset
    model.config = config
    model.experiment = experiment

    metric = Metric(
        id=7,
        dataset_id=dataset.id,
        config_id=config.id,
        train_accuracy=0.91,
        train_loss=0.12,
        validation_accuracy=0.89,
        validation_loss=0.21,
        details_json='{"source":"test"}',
    )
    image = UploadedImage(
        id=8,
        user_id=user.id,
        original_filename="sample.png",
        stored_filename="uuid.png",
        content_type="image/png",
        size_bytes=10,
        storage_path="/tmp/sample.png",
        uploaded_at=now,
    )
    image.user = user

    request = ClassificationRequest(
        id=9,
        user_id=user.id,
        model_id=model.id,
        image_id=image.id,
        status="COMPLETED",
        created_at=now,
        completed_at=now,
        predicted_class="Fresh",
        confidence=0.98,
        probabilities_json='{"Fresh":"0.98","Bad":"0.02"}',
    )
    request.model = model
    request.image = image

    experiment_response = to_experiment_response(experiment, model, metric)
    classification_response = to_classification_response(request)

    assert experiment_response.model is not None
    assert experiment_response.model.datasetName == "Products Dataset"
    assert experiment_response.metrics is not None
    assert experiment_response.metrics.trainAccuracy == 0.91
    assert classification_response.imagePath == "/tmp/sample.png"
    assert classification_response.probabilities == {"Fresh": 0.98, "Bad": 0.02}
