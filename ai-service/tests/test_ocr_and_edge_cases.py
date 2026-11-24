import pytest
import os
import asyncio
import tempfile
import numpy as np
import cv2
from fastapi.testclient import TestClient
from app.main import app
from app.services.ocr_service import ocr_service
from app.services.split_service import split_service
from app.schemas.split import GroupMemberSchema, SplitInterpretRequest

client = TestClient(app)
HEADERS = {"X-Internal-Secret": "splitwise-ai-internal-secret-2026"}

def test_ocr_preprocessing_with_synthetic_image():
    """Verify OpenCV preprocessing on a synthetic black-and-white image."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Create a 200x200 test image with a white rectangle on black background
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        cv2.putText(img, "TEST RECEIPT", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imwrite(tmp_path, img)

        processed = ocr_service.preprocess_image(tmp_path)
        assert isinstance(processed, np.ndarray)
        assert processed.shape == (200, 200)
        # OTSU threshold should result in binary values (0 or 255)
        unique_vals = set(np.unique(processed))
        assert unique_vals.issubset({0, 255})
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_ocr_extract_text_fallback_on_image():
    """Verify fallback behavior when tesseract executable is missing."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(tmp_path, img)

        text, confidence = ocr_service.extract_text(tmp_path)
        assert isinstance(text, str)
        assert len(text) > 0
        assert 0.0 <= confidence <= 1.0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_ocr_nonexistent_file_raises():
    """Verify FileNotFoundError on missing file."""
    with pytest.raises(FileNotFoundError):
        ocr_service.extract_text("non_existent_receipt_99999.png")

def test_ocr_text_file_direct_read():
    """Verify text dump files are read directly with confidence 1.0."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tmp:
        tmp.write("Cafe Coffee Day\nTotal: 250.00")
        tmp_path = tmp.name

    try:
        text, conf = ocr_service.extract_text(tmp_path)
        assert "Cafe Coffee Day" in text
        assert conf == 1.0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_split_ambiguous_instructions_fallback():
    """Verify handling of vague or unparseable natural language prompts."""
    members = [GroupMemberSchema(id=1, name="Alice"), GroupMemberSchema(id=2, name="Bob")]
    req = SplitInterpretRequest(
        instruction="some random text with no numbers or names",
        group_members=members
    )
    res = asyncio.run(split_service.interpret_split(req))
    assert res is not None
    assert 0.0 <= res.confidence <= 1.0

def test_receipt_extraction_empty_text():
    """Verify endpoint gracefully handles empty raw text with fallback."""
    payload = {"raw_ocr_text": ""}
    response = client.post("/internal/v1/receipts/extract", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
