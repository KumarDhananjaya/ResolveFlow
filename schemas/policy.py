"""Pydantic v2 schemas for Policy Matrix evaluation, risk scoring, and resolution proposals."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RecommendedAction(str, Enum):
    """Action recommended by Risk & Policy Agent or approved by Human-in-the-Loop."""
    FULL_REFUND = "FULL_REFUND"
    PARTIAL_REFUND = "PARTIAL_REFUND"
    REJECT = "REJECT"
    REQUEST_MORE_INFO = "REQUEST_MORE_INFO"
    ESCALATE_TO_LEGAL = "ESCALATE_TO_LEGAL"


class PolicyRuleMatch(BaseModel):
    """Rule evaluated during the policy matrix execution."""
    rule_id: str
    rule_name: str
    passed: bool
    risk_impact: int  # Points added or subtracted from risk score (-100 to +100)
    description: str


class PolicyEvaluationResult(BaseModel):
    """Comprehensive output of the Risk & Policy Evaluator Agent."""
    risk_score: int = Field(ge=0, le=100, description="Composite risk score from 0 (Safe) to 100 (High Fraud Risk)")
    recommended_action: RecommendedAction
    refund_amount_aud: float = 0.0
    reasoning: str
    rule_matches: List[PolicyRuleMatch] = Field(default_factory=list)
    requires_human_approval: bool = False
    hitl_trigger_reasons: List[str] = Field(default_factory=list)
    policy_version: str = "2026.1-AU"


class HumanReviewDecision(BaseModel):
    """Decision captured when human manager interacts via Slack or Dashboard."""
    decision: RecommendedAction
    reviewer_id: str
    reviewer_name: Optional[str] = None
    override_amount_aud: Optional[float] = None
    notes: Optional[str] = None
    reviewed_at: str
