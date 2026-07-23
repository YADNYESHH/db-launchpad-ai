"""Repository interface. Two implementations exist: an in-memory store used
for local development/tests (no GCP credentials required), and a Firestore
store used in the deployed Cloud Run service. Both implement the same
interface so the API layer and orchestrator never know which one is active.
"""
from abc import ABC, abstractmethod
from typing import Optional

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


class Store(ABC):
    # -- profiles --------------------------------------------------------
    @abstractmethod
    def save_profile(self, profile: StartupProfile) -> None: ...

    @abstractmethod
    def get_profile(self, startup_id: str) -> Optional[StartupProfile]: ...

    @abstractmethod
    def list_profiles(self) -> list[StartupProfile]: ...

    @abstractmethod
    def save_payment_profile(self, payment: PaymentProfile) -> None: ...

    @abstractmethod
    def get_payment_profile(self, startup_id: str) -> Optional[PaymentProfile]: ...

    @abstractmethod
    def save_pain_point_profile(self, pain: PainPointProfile) -> None: ...

    @abstractmethod
    def get_pain_point_profile(self, startup_id: str) -> Optional[PainPointProfile]: ...

    @abstractmethod
    def save_signals(self, startup_id: str, signals: list[ExpansionSignal]) -> None: ...

    @abstractmethod
    def get_signals(self, startup_id: str) -> list[ExpansionSignal]: ...

    # -- scoring ----------------------------------------------------------
    @abstractmethod
    def save_score_record(self, record: ScoreRecord, score_id: str) -> None: ...

    @abstractmethod
    def get_score_record(self, score_id: str) -> Optional[ScoreRecord]: ...

    @abstractmethod
    def get_latest_score_record(self, startup_id: str) -> Optional[tuple[str, ScoreRecord]]: ...

    # -- recommendations ---------------------------------------------------
    @abstractmethod
    def save_recommendation(self, rec: RecommendationRecord) -> None: ...

    @abstractmethod
    def get_recommendation(self, recommendation_id: str) -> Optional[RecommendationRecord]: ...

    # -- audit --------------------------------------------------------------
    @abstractmethod
    def append_audit_event(self, event: AuditEvent) -> None: ...

    @abstractmethod
    def get_audit_trail(self, startup_id: str) -> list[AuditEvent]: ...

    # -- weight config --------------------------------------------------------
    @abstractmethod
    def save_weight_config(self, config: WeightConfig) -> None: ...

    @abstractmethod
    def get_active_weight_config(self) -> Optional[WeightConfig]: ...

    @abstractmethod
    def list_weight_configs(self) -> list[WeightConfig]: ...

    # -- users --------------------------------------------------------------
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    def save_user(self, user: User) -> None: ...
