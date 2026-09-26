"""SQLAlchemy database models for Customer, Dispute records, and Audit logs."""

import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    Enum,
    Text,
    ForeignKey,
    JSON,
    Boolean,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DisputeStatusEnum(str, enum.Enum):
    """Dispute Lifecycle Statuses."""
    INGESTED = "INGESTED"
    TRIAGED = "TRIAGED"
    INVESTIGATING = "INVESTIGATING"
    PENDING_HUMAN_APPROVAL = "PENDING_HUMAN_APPROVAL"
    APPROVED_FOR_SETTLEMENT = "APPROVED_FOR_SETTLEMENT"
    REJECTED = "REJECTED"
    SETTLED = "SETTLED"
    CLOSED = "CLOSED"


class DisputeClaimTypeEnum(str, enum.Enum):
    """Types of Dispute Claims."""
    ITEM_NOT_RECEIVED = "ITEM_NOT_RECEIVED"
    UNAUTHORIZED_TRANSACTION = "UNAUTHORIZED_TRANSACTION"
    DAMAGED_GOODS = "DAMAGED_GOODS"
    DUPLICATE_CHARGE = "DUPLICATE_CHARGE"
    INCORRECT_AMOUNT = "INCORRECT_AMOUNT"
    SUBSCRIPTION_CANCELLED = "SUBSCRIPTION_CANCELLED"


class Customer(Base):
    """Customer profile and financial history."""
    __tablename__ = "customers"

    id = Column(String(64), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    lifetime_value_aud = Column(Float, default=0.0)
    total_orders_count = Column(Integer, default=0)
    chargeback_count_60d = Column(Integer, default=0)
    trust_score = Column(Float, default=1.0)  # 0.0 to 1.0
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    disputes = relationship("DisputeRecord", back_populates="customer")


class DisputeRecord(Base):
    """Dispute case entity capturing lifecycle, forensics, and human decisions."""
    __tablename__ = "disputes"

    id = Column(String(64), primary_key=True, index=True)
    thread_id = Column(String(128), unique=True, index=True, nullable=False)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=True)
    customer_email = Column(String(255), nullable=False)
    transaction_id = Column(String(128), index=True, nullable=False)
    tracking_number = Column(String(128), nullable=True)

    claim_type = Column(Enum(DisputeClaimTypeEnum), nullable=False)
    amount_aud = Column(Float, nullable=False)
    currency = Column(String(3), default="AUD")
    status = Column(Enum(DisputeStatusEnum), default=DisputeStatusEnum.INGESTED, index=True)

    # Risk assessment
    risk_score = Column(Integer, default=0)  # 0 - 100
    recommended_action = Column(String(64), nullable=True)
    policy_reasoning = Column(Text, nullable=True)

    # Human-in-the-loop audit
    requires_human_approval = Column(Boolean, default=False)
    human_decision = Column(String(64), nullable=True)  # APPROVE, REJECT, MODIFY
    reviewer_notes = Column(Text, nullable=True)
    reviewer_id = Column(String(128), nullable=True)

    # Raw / Evidence payloads
    evidence_data = Column(JSON, default=dict)
    sanitized_complaint_text = Column(Text, nullable=True)

    # Resolution
    refund_id = Column(String(128), nullable=True)
    resolution_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="disputes")
    audit_logs = relationship("AuditTrailLog", back_populates="dispute", cascade="all, delete-orphan")


class AuditTrailLog(Base):
    """Audit log capturing every agent transition, tool execution, and human action."""
    __tablename__ = "audit_trail_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dispute_id = Column(String(64), ForeignKey("disputes.id"), index=True, nullable=False)
    step_name = Column(String(128), nullable=False)
    agent_name = Column(String(128), nullable=False)
    action_type = Column(String(64), nullable=False)
    input_payload = Column(JSON, default=dict)
    output_payload = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    dispute = relationship("DisputeRecord", back_populates="audit_logs")
