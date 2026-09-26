"""Tests for Australian Privacy Principles (APP) PII Sanitization Engine."""

import pytest
from core.security import PIISanitizer


def test_credit_card_masking():
    raw_text = "My Visa card 4532 1122 3344 5566 was charged twice by mistake."
    sanitized = PIISanitizer.mask_credit_card(raw_text)
    assert "4532 1122 3344 5566" not in sanitized
    assert "[CARD-ENDING-IN-5566]" in sanitized


def test_phone_number_masking():
    raw_text = "Please call me at 0412 345 678 or +61 2 9876 5432 regarding my dispute."
    sanitized = PIISanitizer.mask_phone_number(raw_text)
    assert "0412 345 678" not in sanitized
    assert "[PHONE-REDACTED]" in sanitized


def test_nested_dict_sanitization():
    payload = {
        "customer": {
            "name": "Jane Doe",
            "notes": "Charged $200 on card 5412-7512-3412-3456",
        },
        "pan": "4000123456789010",
        "amount": 200.0,
    }
    sanitized = PIISanitizer.sanitize_dict(payload)
    assert "[CARD-ENDING-IN-3456]" in sanitized["customer"]["notes"]
    assert sanitized["pan"] == "[MASKED-PAN]"
    assert sanitized["amount"] == 200.0
