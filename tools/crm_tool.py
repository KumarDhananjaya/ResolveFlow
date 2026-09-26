"""CRM and Customer Ledger History Tool.

Retrieves historical purchasing metrics, chargeback frequency, and calculates customer trust scores.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from core.logger import logger
from schemas.forensics import CustomerLedgerForensics


class CRMLedgerTool:
    """Tool for querying internal CRM records and transaction history."""

    MOCK_CUSTOMERS: Dict[str, Dict[str, Any]] = {
        "jane.doe@example.com.au": {
            "customer_id": "cus_9942",
            "name": "Jane Doe",
            "lifetime_value_aud": 3450.00,
            "total_orders_count": 18,
            "chargeback_count_60d": 0,
            "trust_score": 0.95,
            "account_created_at": datetime.utcnow() - timedelta(days=730),
            "vip_status": True,
        },
        "bad.actor@fraudster.net": {
            "customer_id": "cus_8888",
            "name": "Bob Scammer",
            "lifetime_value_aud": 120.00,
            "total_orders_count": 2,
            "chargeback_count_60d": 4,
            "trust_score": 0.10,
            "account_created_at": datetime.utcnow() - timedelta(days=15),
            "vip_status": False,
        },
        "new.customer@gmail.com": {
            "customer_id": "cus_1234",
            "name": "Alex Smith",
            "lifetime_value_aud": 49.95,
            "total_orders_count": 1,
            "chargeback_count_60d": 0,
            "trust_score": 0.80,
            "account_created_at": datetime.utcnow() - timedelta(days=5),
            "vip_status": False,
        },
    }

    @classmethod
    async def get_customer_history(cls, email: str, customer_id: Optional[str] = None) -> CustomerLedgerForensics:
        """Queries customer profile, historical order volume, and chargeback velocity."""
        logger.info("querying_crm_customer_history", email=email, customer_id=customer_id)

        # Lookup by email
        if email in cls.MOCK_CUSTOMERS:
            data = cls.MOCK_CUSTOMERS[email]
            return CustomerLedgerForensics(
                customer_id=data["customer_id"],
                email=email,
                name=data["name"],
                lifetime_value_aud=data["lifetime_value_aud"],
                total_orders_count=data["total_orders_count"],
                chargeback_count_60d=data["chargeback_count_60d"],
                trust_score=data["trust_score"],
                account_created_at=data["account_created_at"],
                vip_status=data["vip_status"],
            )

        # Default profile for unknown/first-time customer
        return CustomerLedgerForensics(
            customer_id=customer_id or "cus_anonymous",
            email=email,
            name="Valued Customer",
            lifetime_value_aud=150.00,
            total_orders_count=1,
            chargeback_count_60d=0,
            trust_score=0.75,
            account_created_at=datetime.utcnow() - timedelta(days=30),
            vip_status=False,
        )
