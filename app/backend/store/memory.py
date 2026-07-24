"""In-memory Store implementation: used for local development, tests, and
CI — anywhere Firestore credentials are not available or not wanted."""

from ..models import (
    AuditEvent,
    ChatMessage,
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


class InMemoryStore(Store):
    def __init__(self) -> None:
        self._profiles: dict[str, StartupProfile] = {}
        self._payments: dict[str, PaymentProfile] = {}
        self._pains: dict[str, PainPointProfile] = {}
        self._signals: dict[str, list[ExpansionSignal]] = {}
        self._scores: dict[str, ScoreRecord] = {}
        self._scores_by_startup: dict[str, list[str]] = {}
        self._recommendations: dict[str, RecommendationRecord] = {}
        self._audit: dict[str, list[AuditEvent]] = {}
        self._weight_configs: dict[str, WeightConfig] = {}
        self._users: dict[str, User] = {}
        self._chat: dict[str, list[ChatMessage]] = {}

    def save_profile(self, profile: StartupProfile) -> None:
        self._profiles[profile.startup_id] = profile

    def get_profile(self, startup_id: str) -> StartupProfile | None:
        return self._profiles.get(startup_id)

    def list_profiles(self) -> list[StartupProfile]:
        return list(self._profiles.values())

    def save_payment_profile(self, payment: PaymentProfile) -> None:
        self._payments[payment.startup_id] = payment

    def get_payment_profile(self, startup_id: str) -> PaymentProfile | None:
        return self._payments.get(startup_id)

    def save_pain_point_profile(self, pain: PainPointProfile) -> None:
        self._pains[pain.startup_id] = pain

    def get_pain_point_profile(self, startup_id: str) -> PainPointProfile | None:
        return self._pains.get(startup_id)

    def save_signals(self, startup_id: str, signals: list[ExpansionSignal]) -> None:
        self._signals[startup_id] = list(signals)

    def get_signals(self, startup_id: str) -> list[ExpansionSignal]:
        return list(self._signals.get(startup_id, []))

    def save_score_record(self, record: ScoreRecord, score_id: str) -> None:
        self._scores[score_id] = record
        self._scores_by_startup.setdefault(record.startup_id, []).append(score_id)

    def get_score_record(self, score_id: str) -> ScoreRecord | None:
        return self._scores.get(score_id)

    def get_latest_score_record(self, startup_id: str) -> tuple[str, ScoreRecord] | None:
        ids = self._scores_by_startup.get(startup_id, [])
        if not ids:
            return None
        latest_id = ids[-1]
        return latest_id, self._scores[latest_id]

    def save_recommendation(self, rec: RecommendationRecord) -> None:
        self._recommendations[rec.recommendation_id] = rec

    def get_recommendation(self, recommendation_id: str) -> RecommendationRecord | None:
        return self._recommendations.get(recommendation_id)

    def append_audit_event(self, event: AuditEvent) -> None:
        self._audit.setdefault(event.startup_id, []).append(event)

    def get_audit_trail(self, startup_id: str) -> list[AuditEvent]:
        return list(self._audit.get(startup_id, []))

    def save_weight_config(self, config: WeightConfig) -> None:
        self._weight_configs[config.version_id] = config

    def get_active_weight_config(self) -> WeightConfig | None:
        active = [c for c in self._weight_configs.values() if c.active]
        if not active:
            return None
        return max(active, key=lambda c: c.created_date)

    def list_weight_configs(self) -> list[WeightConfig]:
        return list(self._weight_configs.values())

    def get_user_by_email(self, email: str) -> User | None:
        return self._users.get(email)

    def save_user(self, user: User) -> None:
        self._users[user.email] = user

    def append_chat_message(self, message: ChatMessage) -> None:
        self._chat.setdefault(message.startup_id, []).append(message)

    def get_chat_history(self, startup_id: str) -> list[ChatMessage]:
        return list(self._chat.get(startup_id, []))
