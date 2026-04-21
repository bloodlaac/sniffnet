from __future__ import annotations

import pytest
from pydantic import ValidationError

from sniffnet.schemas.contracts import ClassificationFilters, ExperimentCreateRequest, TrainingConfigRequest


def test_experiment_create_request_requires_config_id_or_payload() -> None:
    with pytest.raises(ValidationError, match="configId or config payload is required"):
        ExperimentCreateRequest(datasetId=1)

    request = ExperimentCreateRequest(datasetId=1, configId=2)
    assert request.configId == 2


def test_training_config_request_validates_numeric_bounds() -> None:
    invalid_payloads = [
        {"epochsNum": 0, "batchSize": 8, "learningRate": 0.01, "optimizer": "Adam", "lossFunction": "CrossEntropyLoss", "validationSplit": 0.2},
        {"epochsNum": 1, "batchSize": 0, "learningRate": 0.01, "optimizer": "Adam", "lossFunction": "CrossEntropyLoss", "validationSplit": 0.2},
        {"epochsNum": 1, "batchSize": 8, "learningRate": 0.0, "optimizer": "Adam", "lossFunction": "CrossEntropyLoss", "validationSplit": 0.2},
        {"epochsNum": 1, "batchSize": 8, "learningRate": 0.01, "optimizer": "Adam", "lossFunction": "CrossEntropyLoss", "validationSplit": 1.0},
    ]

    for payload in invalid_payloads:
        with pytest.raises(ValidationError):
            TrainingConfigRequest(**payload)


def test_classification_filters_validate_date_range() -> None:
    filters = ClassificationFilters(from_date="2026-04-20", to_date="2026-04-20")
    assert filters.from_date == filters.to_date

    with pytest.raises(ValidationError, match="to must be greater than or equal to from"):
        ClassificationFilters(from_date="2026-04-21", to_date="2026-04-20")
