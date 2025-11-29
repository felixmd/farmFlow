"""
Emergency Case Manager for Human-in-the-Loop Livestock Veterinary Review

This module manages the state of emergency livestock cases that require
expert veterinarian review. It provides persistent storage and state management
using Google Cloud Firestore.

State Flow: pending_review → awaiting_vet → vet_responded → completed
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from google.cloud import firestore
import google.auth.exceptions

logger = logging.getLogger(__name__)

class EmergencyCaseManager:
    """Manages emergency livestock cases requiring vet review using Firestore"""

    def __init__(self, collection_name: str = "emergency_cases"):
        """
        Initialize the case manager with Firestore
        
        Args:
            collection_name: Firestore collection name
        """
        self.collection_name = collection_name
        try:
            self.db = firestore.Client()
            logger.info(f"Firestore initialized. Collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}. Ensure GOOGLE_APPLICATION_CREDENTIALS is set.")
            self.db = None

    def create_case(
        self,
        farmer_user_id: str,
        farmer_name: str,
        session_id: str,
        query: str,
        detected_disease: str,
        severity: str,
        image_data: Optional[bytes] = None,
        image_telegram_file_id: Optional[str] = None
    ) -> str:
        """Create a new emergency case"""
        if not self.db:
            logger.error("Firestore not available, cannot create case")
            return "ERROR_NO_DB"

        case_id = str(uuid.uuid4())[:8].upper()  # Short, readable ID

        case = {
            "case_id": case_id,
            "farmer_user_id": farmer_user_id,
            "farmer_name": farmer_name,
            "session_id": session_id,
            "query": query,
            "detected_disease": detected_disease,
            "severity": severity,
            "image_telegram_file_id": image_telegram_file_id,
            "status": "pending_review",
            "created_at": datetime.now().isoformat(),
            "vet_response": None,
            "vet_name": None,
            "vet_responded_at": None,
            "completed_at": None,
            "vet_message_id": None
        }

        try:
            self.db.collection(self.collection_name).document(case_id).set(case)
            logger.info(f"[EmergencyCase] Created case {case_id} for user {farmer_user_id}")
            return case_id
        except Exception as e:
            logger.error(f"Failed to create case in Firestore: {e}", exc_info=True)
            return "ERROR_DB_WRITE"

    def get_case(self, case_id: str) -> Optional[Dict]:
        """Get case by ID"""
        if not self.db:
            return None
            
        try:
            doc = self.db.collection(self.collection_name).document(case_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Failed to get case {case_id}: {e}", exc_info=True)
            return None

    def update_case_status(self, case_id: str, status: str):
        """Update case status"""
        if not self.db:
            return

        try:
            self.db.collection(self.collection_name).document(case_id).update({"status": status})
            logger.info(f"[EmergencyCase] Case {case_id} status updated: {status}")
        except Exception as e:
            logger.error(f"Failed to update status for {case_id}: {e}", exc_info=True)

    def mark_vet_posted(self, case_id: str, vet_message_id: int):
        """Mark that case was posted to vet group"""
        if not self.db:
            return

        try:
            self.db.collection(self.collection_name).document(case_id).update({
                "status": "awaiting_vet",
                "vet_message_id": vet_message_id
            })
            logger.info(f"[EmergencyCase] Case {case_id} posted to vet group (msg_id: {vet_message_id})")
        except Exception as e:
            logger.error(f"Failed to mark vet posted for {case_id}: {e}", exc_info=True)

    def mark_vet_response(
        self,
        case_id: str,
        vet_response: str,
        vet_name: str,
        vet_user_id: str
    ):
        """Mark that vet has responded"""
        if not self.db:
            return

        try:
            self.db.collection(self.collection_name).document(case_id).update({
                "status": "vet_responded",
                "vet_response": vet_response,
                "vet_name": vet_name,
                "vet_user_id": vet_user_id,
                "vet_responded_at": datetime.now().isoformat()
            })
            logger.info(f"[EmergencyCase] Case {case_id} received vet response")
        except Exception as e:
            logger.error(f"Failed to mark vet response for {case_id}: {e}", exc_info=True)

    def mark_completed(self, case_id: str):
        """Mark case as completed"""
        if not self.db:
            return

        try:
            self.db.collection(self.collection_name).document(case_id).update({
                "status": "completed",
                "completed_at": datetime.now().isoformat()
            })
            logger.info(f"[EmergencyCase] Case {case_id} marked completed")
        except Exception as e:
            logger.error(f"Failed to mark completed for {case_id}: {e}", exc_info=True)

    def get_pending_farmer_notifications(self) -> List[Dict]:
        """Get cases that have vet response but farmer hasn't been notified yet"""
        if not self.db:
            return []

        try:
            docs = self.db.collection(self.collection_name).where("status", "==", "vet_responded").stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Failed to get pending notifications: {e}", exc_info=True)
            return []

    def get_case_by_vet_message(self, vet_message_id: int) -> Optional[Dict]:
        """Find case by the vet group message ID"""
        if not self.db:
            return None

        try:
            docs = self.db.collection(self.collection_name).where("vet_message_id", "==", vet_message_id).limit(1).stream()
            for doc in docs:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Failed to find case by message ID {vet_message_id}: {e}", exc_info=True)
            return None

# Global instance
_case_manager = None

def get_case_manager() -> EmergencyCaseManager:
    """Get singleton instance of case manager"""
    global _case_manager
    if _case_manager is None:
        _case_manager = EmergencyCaseManager()
    return _case_manager
