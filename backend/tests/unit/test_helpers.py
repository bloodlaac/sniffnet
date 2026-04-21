from __future__ import annotations

from types import SimpleNamespace

import pytest

from sniffnet.api.config import MAX_IMAGE_SIZE_BYTES
from sniffnet.api.errors import BadRequestException
from sniffnet.api.helpers import remove_path, validate_upload


def test_validate_upload_accepts_supported_png_file() -> None:
    file = SimpleNamespace(filename="sample.png", content_type="image/png", size=128)

    validate_upload(file)


def test_validate_upload_rejects_invalid_files() -> None:
    cases = [
        (SimpleNamespace(filename="", content_type="image/png", size=1), "Image file is required"),
        (SimpleNamespace(filename="sample.gif", content_type="image/gif", size=1), "Unsupported image content type"),
        (SimpleNamespace(filename="sample.gif", content_type="image/png", size=1), "Unsupported image extension"),
        (
            SimpleNamespace(filename="sample.png", content_type="image/png", size=MAX_IMAGE_SIZE_BYTES + 1),
            "Image file is too large",
        ),
    ]

    for file, message in cases:
        with pytest.raises(BadRequestException, match=message):
            validate_upload(file)


def test_remove_path_deletes_existing_file_and_ignores_missing_path(tmp_path) -> None:
    path = tmp_path / "image.png"
    path.write_bytes(b"data")

    remove_path(str(path))
    remove_path(str(path))
    remove_path(None)

    assert path.exists() is False
