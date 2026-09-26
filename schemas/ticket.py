"""Pydantic v2 schemas for dispute ticket intake, extraction, and validation."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, field_validator


class ClaimType(str, Enum):
    """Supported dispute claim types."""
    ITEM_NOT_RECEIVED = "ITEM_NOT_RECEIVED"
    UNAUTHORIZED_TRANSACTION = "UNAUTHORIZED_TRANSACTION"
    DAMAGED_GOODS = "DAMAGED_GOODS"
    DUPLICATE_CHARGE = "DUPLICATE_CHARGE"
    INCORRECT_AMOUNT = "INCORRECT_AMOUNT"
    SUBSCRIPTION_CANCELLED = "SUBSCRIPTION_CANCELLED"
    OTHER = "OTHER"


class DisputeTicketInput(BaseModel):
    """Raw input payload when ingesting customer complaint or webhook."""
    customer_email: EmailStr = Field(description="Customer contact email address")
    transaction_id: str = Field(description="Stripe or gateway payment transaction ID (e.g., ch_123 or pi_123)")
    tracking_number: Optional[str] = Field(default=None, description="Australia Post / carrier tracking number")
    amount_aud: float = Field(gt=0, description="Amount disputed in Australian Dollars (AUD)")
    claim_type: ClaimType = Field(default=ClaimType.ITEM_NOT_RECEIVED, description="Category of claim")
    evidence_notes: str = Field(description="Customer raw description of the issue")
    customer_name: Optional[str] = Field(default="Customer", description="Customer full name if provided")

    @field_validator("amount_aud")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        return round(v, 2)


class DisputeTicket(BaseModel):
    """Structured and validated dispute ticket object after triage and PII sanitization."""
    ticket_id: str = Field(description="Unique internal ticket identifier (e.g., DISP-8492)")
    thread_id: str = Field(description="Deterministic conversation/checkpoint thread ID")
    customer_email: EmailStr
    customer_name: str
    transaction_id: str
    tracking_number: Optional[str] = None
    amount_aud: float
    currency: str = "AUD"
    claim_type: ClaimType
    sanitized_notes: str = Field(description="Notes with PII masked per Australian Privacy Principles")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
