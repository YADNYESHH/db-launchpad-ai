"""Firestore Store implementation used by the deployed Cloud Run service.
Collections: profiles, payment_profiles, pain_point_profiles, signals,
score_records, recommendations, audit_log, weight_configs, users.
"""
from typing import Optional

from google.cloud import firestore

from ..models import (
    AuditEvent,
    ExpansionSignal,
    PainPointProfile,
    PaymentProfile,
    RecommendationRecord,
    ScoreRecord,
    StartupProfile,
    User,
    WeightConfig,
)
from .base import Store


class FirestoreStore(Store):
    def __init__(self, project_id: str) -> None:
        self._db = firestore.Client(project=project_id)

    def save_profile(self, profile: StartupProfile) -> None:
        self._db.collection("profiles").document(profile.startup_id).set(profile.model_dump(mode="json"))

    def get_profile(self, startup_id: str) -> Optional[StartupProfile]:
        doc = self._db.collection("profiles").document(startup_id).get()
        return StartupProfile.model_validate(doc.to_dict()) if doc.exists else None

    def list_profiles(self) -> list[StartupProfile]:
        return [StartupProfile.model_validate(d.to_dict()) for d in self._db.collection("profiles").stream()]

    def save_payment_profile(self, payment: PaymentProfile) -> None:
        self._db.collection("payment_profiles").document(payment.startup_id).set(payment.model_dump(mode="json"))

    def get_payment_profile(self, startup_id: str) -> Optional[PaymentProfile]:
        doc = self._db.collection("payment_profiles").document(startup_id).get()
        return PaymentProfile.model_validate(doc.to_dict()) if doc.exists else None

    def save_pain_point_profile(self, pain: PainPointProfile) -> None:
        self._db.collection("pain_point_profiles").document(pain.startup_id).set(pain.model_dump(mode="json"))

    def get_pain_point_profile(self, startup_id: str) -> Optional[PainPointProfile]:
        doc = self._db.collection("pain_point_profiles").document(startup_id).get()
        return PainPointProfile.model_validate(doc.to_dict()) if doc.exists else None

    def save_signals(self, startup_id: str, signals: list[ExpansionSignal]) -> None:
        self._db.collection("signals").document(startup_id).set(
            {"signals": [s.model_dump(mode="json") for s in signals]}
        )

    def get_signals(self, startup_id: str) -> list[ExpansionSignal]:
        doc = self._db.collection("signals").document(startup_id).get()
        if not doc.exists:
            return []
        return [ExpansionSignal.model_validate(s) for s in doc.to_dict().get("signals", [])]

    def save_score_record(self, record: ScoreRecord, score_id: str) -> None:
        self._db.collection("score_records").document(score_id).set(record.model_dump(mode="json"))

    def get_score_record(self, score_id: str) -> Optional[ScoreRecord]:
        doc = self._db.collection("score_records").document(score_id).get()
        return ScoreRecord.model_validate(doc.to_dict()) if doc.exists else None

    def get_latest_score_record(self, startup_id: str) -> Optional[tuple[str, ScoreRecord]]:
        query = (
            self._db.collection("score_records")
            .where("startup_id", "==", startup_id)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(1)
        )
        docs = list(query.stream())
        if not docs:
            return None
        return docs[0].id, ScoreRecord.model_validate(docs[0].to_dict())

    def save_recommendation(self, rec: RecommendationRecord) -> None:
        self._db.collection("recommendations").document(rec.recommendation_id).set(rec.model_dump(mode="json"))

    def get_recommendation(self, recommendation_id: str) -> Optional[RecommendationRecord]:
        doc = self._db.collection("recommendations").document(recommendation_id).get()
        return RecommendationRecord.model_validate(doc.to_dict()) if doc.exists else None

    def append_audit_event(self, event: AuditEvent) -> None:
        self._db.collection("audit_log").document(event.audit_id).set(event.model_dump(mode="json"))

    def get_audit_trail(self, startup_id: str) -> list[AuditEvent]:
        query = (
            self._db.collection("audit_log")
            .where("startup_id", "==", startup_id)
            .order_by("timestamp", direction=firestore.Query.ASCENDING)
        )
        return [AuditEvent.model_validate(d.to_dict()) for d in query.stream()]

    def save_weight_config(self, config: WeightConfig) -> None:
        self._db.collection("weight_configs").document(config.version_id).set(config.model_dump(mode="json"))

    def get_active_weight_config(self) -> Optional[WeightConfig]:
        query = self._db.collection("weight_configs").where("active", "==", True)
        configs = [WeightConfig.model_validate(d.to_dict()) for d in query.stream()]
        if not configs:
            return None
        return sorted(configs, key=lambda c: c.created_date)[-1]

    def list_weight_configs(self) -> list[WeightConfig]:
        return [WeightConfig.model_validate(d.to_dict()) for d in self._db.collection("weight_configs").stream()]

    def get_user_by_email(self, email: str) -> Optional[User]:
        doc = self._db.collection("users").document(email).get()
        return User.model_validate(doc.to_dict()) if doc.exists else None

    def save_user(self, user: User) -> None:
        self._db.collection("users").document(user.email).set(user.model_dump(mode="json"))
