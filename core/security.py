"""Data Privacy & PII Sanitization module for Australian Privacy Principles (APP) compliance."""

import re
from typing import Any, Dict


class PIISanitizer:
    """Sanitizes Personally Identifiable Information (PII) before LLM ingestion.
    
    Complies with Australian Privacy Principles (APP 11 - Security of personal information).
    """

    # Regex patterns for sensitive financial and identity data
    CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
    CVV_PATTERN = re.compile(r"\b\d{3,4}\b")
    AU_PHONE_PATTERN = re.compile(r"\b(?:\+?61|0)[2-478](?:[ -]?[0-9]){8}\b")
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    @classmethod
    def mask_credit_card(cls, text: str) -> str:
        """Masks 13-19 digit card numbers, keeping only the last 4 digits."""
        def repl(match: re.Match) -> str:
            raw_digits = re.sub(r"\D", "", match.group(0))
            if 13 <= len(raw_digits) <= 19:
                return f"[CARD-ENDING-IN-{raw_digits[-4:]}]"
            return match.group(0)

        return cls.CREDIT_CARD_PATTERN.sub(repl, text)

    @classmethod
    def mask_phone_number(cls, text: str) -> str:
        """Masks Australian phone numbers."""
        return cls.AU_PHONE_PATTERN.sub("[PHONE-REDACTED]", text)

    @classmethod
    def sanitize_text(cls, text: str, mask_email: bool = False) -> str:
        """Sanitizes freeform text from dispute emails/tickets."""
        if not text:
            return ""

        sanitized = cls.mask_credit_card(text)
        sanitized = cls.mask_phone_number(sanitized)

        if mask_email:
            sanitized = cls.EMAIL_PATTERN.sub("[EMAIL-REDACTED]", sanitized)

        return sanitized

    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitizes dictionary fields containing text strings."""
        sanitized_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Never expose full raw card fields if passed as dict keys
                if any(sensitive in key.lower() for sensitive in ["card_number", "pan", "cvv", "security_code"]):
                    sanitized_data[key] = f"[MASKED-{key.upper()}]"
                else:
                    sanitized_data[key] = cls.sanitize_text(value)
            elif isinstance(value, dict):
                sanitized_data[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized_data[key] = [
                    cls.sanitize_dict(item) if isinstance(item, dict)
                    else (cls.sanitize_text(item) if isinstance(item, str) else item)
                    for item in value
                ]
            else:
                sanitized_data[key] = value
        return sanitized_data
