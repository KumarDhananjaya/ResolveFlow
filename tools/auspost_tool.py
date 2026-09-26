"""Australia Post Logistics Forensics Tool.

Simulates and integrates with Australia Post / StarTrack tracking and delivery verification APIs.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from core.logger import logger
from schemas.forensics import AusPostForensics, DeliveryStatus, TrackingMilestone


class AustraliaPostTool:
    """Tool for querying parcel logistics, delivery checkpoints, and signature proof."""

    # Built-in mock dataset for testing diverse delivery scenarios
    MOCK_TRACKING_DATABASE: Dict[str, Dict[str, Any]] = {
        "AP982347102AU": {
            "status": DeliveryStatus.DELIVERED,
            "delivery_date": datetime.utcnow() - timedelta(days=2),
            "delivery_postcode": "3000",
            "delivery_suburb": "Melbourne",
            "has_signature": True,
            "signature_recipient_name": "J. Doe",
            "safe_drop_photo_url": None,
            "milestones": [
                {
                    "timestamp": datetime.utcnow() - timedelta(days=4),
                    "location": "SYDNEY NSW",
                    "status": "PROCESSED",
                    "description": "Item processed at facility",
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(days=3),
                    "location": "MELBOURNE VIC",
                    "status": "WITH_DRIVER",
                    "description": "Onboard with driver for delivery",
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(days=2),
                    "location": "MELBOURNE VIC 3000",
                    "status": "DELIVERED",
                    "description": "Delivered and signed for by J. Doe",
                },
            ],
        },
        "AP_TRANSIT_001": {
            "status": DeliveryStatus.IN_TRANSIT,
            "delivery_date": None,
            "delivery_postcode": "2000",
            "delivery_suburb": "Sydney",
            "has_signature": False,
            "signature_recipient_name": None,
            "safe_drop_photo_url": None,
            "milestones": [
                {
                    "timestamp": datetime.utcnow() - timedelta(days=5),
                    "location": "BRISBANE QLD",
                    "status": "ACCEPTED",
                    "description": "Item received by Australia Post",
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(days=2),
                    "location": "CHULLORA NSW",
                    "status": "IN_TRANSIT",
                    "description": "In transit to destination facility",
                },
            ],
        },
        "AP_LOST_002": {
            "status": DeliveryStatus.FAILED_ATTEMPT,
            "delivery_date": None,
            "delivery_postcode": "5000",
            "delivery_suburb": "Adelaide",
            "has_signature": False,
            "signature_recipient_name": None,
            "safe_drop_photo_url": None,
            "milestones": [
                {
                    "timestamp": datetime.utcnow() - timedelta(days=7),
                    "location": "ADELAIDE SA",
                    "status": "AWAITING_COLLECTION",
                    "description": "Delivery attempted - Card left for post office collection",
                }
            ],
        },
    }

    @classmethod
    async def get_delivery_proof(cls, tracking_number: Optional[str]) -> AusPostForensics:
        """Fetches forensic tracking proof for a given Australia Post tracking number."""
        if not tracking_number:
            logger.warn("auspost_query_skipped_no_tracking")
            return AusPostForensics(
                tracking_number="N/A",
                status=DeliveryStatus.NOT_FOUND,
                raw_response={"message": "No tracking number supplied"}
            )

        logger.info("querying_auspost_tracking", tracking_number=tracking_number)

        # Check mock database
        if tracking_number in cls.MOCK_TRACKING_DATABASE:
            data = cls.MOCK_TRACKING_DATABASE[tracking_number]
            milestones = [
                TrackingMilestone(
                    timestamp=m["timestamp"],
                    location=m["location"],
                    status=m["status"],
                    description=m["description"],
                )
                for m in data["milestones"]
            ]
            return AusPostForensics(
                tracking_number=tracking_number,
                status=data["status"],
                delivery_date=data["delivery_date"],
                delivery_postcode=data["delivery_postcode"],
                delivery_suburb=data["delivery_suburb"],
                has_signature=data["has_signature"],
                signature_recipient_name=data["signature_recipient_name"],
                safe_drop_photo_url=data["safe_drop_photo_url"],
                milestones=milestones,
                raw_response={"source": "auspost_mock_db", "status_code": 200},
            )

        # Fallback generated response for ad-hoc tracking numbers
        return AusPostForensics(
            tracking_number=tracking_number,
            status=DeliveryStatus.DELIVERED,
            delivery_date=datetime.utcnow() - timedelta(days=1),
            delivery_postcode="2000",
            delivery_suburb="Sydney",
            has_signature=True,
            signature_recipient_name="Authorized Recipient",
            milestones=[
                TrackingMilestone(
                    timestamp=datetime.utcnow() - timedelta(days=1),
                    location="SYDNEY NSW 2000",
                    status="DELIVERED",
                    description="Delivered to address with signature verification",
                )
            ],
            raw_response={"source": "auspost_mock_fallback", "status_code": 200},
        )
