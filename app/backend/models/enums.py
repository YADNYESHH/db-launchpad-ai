from enum import Enum


class Role(str, Enum):
    RM = "relationship_manager"
    PRODUCT_OWNER = "product_owner"
    CONTROL_REVIEWER = "control_reviewer"
    ADMIN = "admin"


class PriorityBand(str, Enum):
    HIGH_PRIORITY = "high_priority"
    MONITOR = "monitor"
    VALIDATE = "validate"
    NO_ACTION = "no_immediate_action"


class ApprovalStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    REVISED = "revised"
    REJECTED = "rejected"
    VALIDATION_REQUIRED = "validation_required"


class DataSourceType(str, Enum):
    SYNTHETIC = "synthetic"
    PUBLIC_MANUAL = "public_manual"


class ConfidenceBand(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


SUB_SCORE_TYPES = (
    "revenue_potential",
    "client_pain_point_intensity",
    "strategic_fit",
    "early_signal_detectability",
    "rm_actionability",
    "data_availability_explainability",
    "control_implementation_feasibility",
)
