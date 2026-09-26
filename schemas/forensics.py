"""Pydantic v2 schemas for evidence collected by the Forensics Agent from external APIs."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DeliveryStatus(str, Enum):
    """Australia Post parcel delivery statuses."""
    DELIVERED = "DELIVERED"
    IN_TRANSIT = "IN_TRANSIT"
    FAILED_ATTEMPT = "FAILED_ATTEMPT"
    RETURNED_TO_SENDER = "RETURNED_TO_SENDER"
    LABEL_CREATED = "LABEL_CREATED"
    NOT_FOUND = "NOT_FOUND"


class TrackingMilestone(BaseModel):
    """Individual checkpoint scan from Australia Post / carrier."""
    timestamp: datetime
    location: str
    status: str
    description: str


class AusPostForensics(BaseModel):
    """Forensic package retrieved from Australia Post API."""
    tracking_number: str
    status: DeliveryStatus
    delivery_date: Optional[datetime] = None
    delivery_postcode: Optional[str] = None
    delivery_suburb: Optional[str] = None
    has_signature: bool = False
    signature_recipient_name: Optional[str] = None
    safe_drop_photo_url: Optional[str] = None
    milestones: List[TrackingMilestone] = Field(default_factory=list)
    raw_response: Dict[str, Any] = Field(default_factory=dict)


class PaymentStatus(str, Enum):
    """Payment Gateway transaction status."""
    SUCCEEDED = "SUCCEEDED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    DISPUTED = "DISPUTED"


class StripeForensics(BaseModel):
    """Forensic evidence gathered from Stripe Payment Rails."""
    transaction_id: str
    amount_aud: float
    currency: str = "AUD"
    payment_status: PaymentStatus
    card_brand: Optional[str] = None
    card_last4: Optional[str] = None
    card_funding: Optional[str] = None  # credit, debit, prepaid
    risk_level: Optional[str] = "normal"  # normal, elevated, highest
    disputed: bool = False
    refunded: bool = False
    created_at: datetime
    customer_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CustomerLedgerForensics(BaseModel):
    """Customer profile and behavioral dispute history."""
    customer_id: str
    email: str
    name: str
    lifetime_value_aud: float
    total_orders_count: int
    chargeback_count_60d: int
    trust_score: float  # 0.0 to 1.0
    account_created_at: datetime
    vip_status: bool = False


class ComprehensiveForensicsEvidence(BaseModel):
    """Aggregated forensics artifact compiled by the Forensics Agent."""
    ticket_id: str
    auspost_data: Optional[AusPostForensics] = None
    stripe_data: Optional[StripeForensics] = None
    customer_data: Optional[CustomerLedgerForensics] = None
    investigation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    anomalies_detected: List[str] = Field(default_factory=list)
