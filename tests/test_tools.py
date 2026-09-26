"""Unit tests for Australia Post, Stripe, and CRM tools."""

import pytest
from tools.auspost_tool import AustraliaPostTool
from tools.stripe_tool import StripePaymentTool
from tools.crm_tool import CRMLedgerTool
from schemas.forensics import DeliveryStatus, PaymentStatus


@pytest.mark.asyncio
async def test_auspost_tool_delivered_with_signature():
    forensics = await AustraliaPostTool.get_delivery_proof("AP982347102AU")
    assert forensics.tracking_number == "AP982347102AU"
    assert forensics.status == DeliveryStatus.DELIVERED
    assert forensics.has_signature is True
    assert forensics.signature_recipient_name == "J. Doe"
    assert forensics.delivery_postcode == "3000"
    assert len(forensics.milestones) == 3


@pytest.mark.asyncio
async def test_auspost_tool_in_transit():
    forensics = await AustraliaPostTool.get_delivery_proof("AP_TRANSIT_001")
    assert forensics.status == DeliveryStatus.IN_TRANSIT
    assert forensics.has_signature is False


@pytest.mark.asyncio
async def test_stripe_tool_transaction_lookup():
    stripe_data = await StripePaymentTool.get_transaction_status("ch_3N8au82eZvKYlo2C1g9X8xYz")
    assert stripe_data.amount_aud == 285.00
    assert stripe_data.payment_status == PaymentStatus.SUCCEEDED
    assert stripe_data.card_brand == "Visa"
    assert stripe_data.card_last4 == "4242"


@pytest.mark.asyncio
async def test_stripe_tool_execute_refund():
    refund_res = await StripePaymentTool.execute_refund(
        transaction_id="ch_SAFE_UNDER_100",
        amount_aud=49.95,
        reason="customer_item_damaged"
    )
    assert refund_res["status"] == "succeeded"
    assert refund_res["amount_refunded_aud"] == 49.95
    assert "re_" in refund_res["refund_id"]


@pytest.mark.asyncio
async def test_crm_tool_vip_customer():
    crm_data = await CRMLedgerTool.get_customer_history("jane.doe@example.com.au")
    assert crm_data.name == "Jane Doe"
    assert crm_data.lifetime_value_aud == 3450.00
    assert crm_data.vip_status is True
    assert crm_data.chargeback_count_60d == 0


@pytest.mark.asyncio
async def test_crm_tool_bad_actor():
    crm_data = await CRMLedgerTool.get_customer_history("bad.actor@fraudster.net")
    assert crm_data.chargeback_count_60d == 4
    assert crm_data.trust_score <= 0.20
    assert crm_data.vip_status is False
