"""Stripe Financial Rails and Payment Forensics Tool."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from core.logger import logger
from schemas.forensics import StripeForensics, PaymentStatus


class StripePaymentTool:
    """Tool for querying Stripe payment intents, dispute statuses, and executing refunds."""

    # Built-in mock dataset
    MOCK_TRANSACTIONS: Dict[str, Dict[str, Any]] = {
        "ch_3N8au82eZvKYlo2C1g9X8xYz": {
            "amount_aud": 285.00,
            "payment_status": PaymentStatus.SUCCEEDED,
            "card_brand": "Visa",
            "card_last4": "4242",
            "card_funding": "credit",
            "risk_level": "normal",
            "disputed": False,
            "refunded": False,
            "created_at": datetime.utcnow() - timedelta(days=5),
            "customer_id": "cus_9942",
        },
        "ch_SAFE_UNDER_100": {
            "amount_aud": 49.95,
            "payment_status": PaymentStatus.SUCCEEDED,
            "card_brand": "Mastercard",
            "card_last4": "1111",
            "card_funding": "debit",
            "risk_level": "normal",
            "disputed": False,
            "refunded": False,
            "created_at": datetime.utcnow() - timedelta(days=2),
            "customer_id": "cus_1234",
        },
        "ch_HIGH_RISK_FRAUD": {
            "amount_aud": 850.00,
            "payment_status": PaymentStatus.SUCCEEDED,
            "card_brand": "American Express",
            "card_last4": "0005",
            "card_funding": "credit",
            "risk_level": "highest",
            "disputed": True,
            "refunded": False,
            "created_at": datetime.utcnow() - timedelta(days=1),
            "customer_id": "cus_8888",
        },
    }

    @classmethod
    async def get_transaction_status(cls, transaction_id: str) -> StripeForensics:
        """Fetches payment intent details, card metadata, and risk profile from Stripe."""
        logger.info("querying_stripe_transaction", transaction_id=transaction_id)

        if transaction_id in cls.MOCK_TRANSACTIONS:
            data = cls.MOCK_TRANSACTIONS[transaction_id]
            return StripeForensics(
                transaction_id=transaction_id,
                amount_aud=data["amount_aud"],
                currency="AUD",
                payment_status=data["payment_status"],
                card_brand=data["card_brand"],
                card_last4=data["card_last4"],
                card_funding=data["card_funding"],
                risk_level=data["risk_level"],
                disputed=data["disputed"],
                refunded=data["refunded"],
                created_at=data["created_at"],
                customer_id=data["customer_id"],
                metadata={"gateway": "stripe_mock_vault"},
            )

        # Fallback dynamic mock for arbitrary transaction IDs
        return StripeForensics(
            transaction_id=transaction_id,
            amount_aud=150.00,
            currency="AUD",
            payment_status=PaymentStatus.SUCCEEDED,
            card_brand="Visa",
            card_last4="4000",
            card_funding="credit",
            risk_level="normal",
            disputed=False,
            refunded=False,
            created_at=datetime.utcnow() - timedelta(days=3),
            customer_id=f"cus_{transaction_id[-4:]}",
            metadata={"gateway": "stripe_dynamic_mock"},
        )

    @classmethod
    async def execute_refund(
        cls,
        transaction_id: str,
        amount_aud: float,
        reason: str = "requested_by_customer",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Executes a refund on Stripe payment rails with idempotency."""
        logger.info(
            "executing_stripe_refund",
            transaction_id=transaction_id,
            amount_aud=amount_aud,
            reason=reason,
            idempotency_key=idempotency_key,
        )

        refund_id = f"re_{transaction_id[-8:]}_{int(datetime.utcnow().timestamp())}"
        
        # Mark local transaction mock as refunded if exists
        if transaction_id in cls.MOCK_TRANSACTIONS:
            cls.MOCK_TRANSACTIONS[transaction_id]["refunded"] = True

        return {
            "refund_id": refund_id,
            "status": "succeeded",
            "amount_refunded_aud": amount_aud,
            "currency": "AUD",
            "transaction_id": transaction_id,
            "created_at": datetime.utcnow().isoformat(),
        }
