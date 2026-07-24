export type Role = 'relationship_manager' | 'product_owner' | 'control_reviewer' | 'admin'

export type PriorityBand = 'high_priority' | 'monitor' | 'validate' | 'no_immediate_action'

export type ApprovalStatus = 'draft' | 'approved' | 'revised' | 'rejected' | 'validation_required'

export interface UserPublic {
  user_id: string
  email: string
  name: string
  role: Role
}

export interface StartupProfile {
  startup_id: string
  name: string
  sector: string
  hq_country: string
  current_countries: string[]
  target_countries: string[]
  growth_stage: string
  funding_stage: string
  annual_revenue_eur: number
  expansion_timeline_months: number | null
  synthetic_flag: boolean
  data_source_type: string
}

export interface PaymentProfile {
  startup_id: string
  annual_cross_border_payment_value_eur: number
  monthly_payment_count_inbound: number
  monthly_payment_count_outbound: number
  currencies: string[]
  payment_corridors: string[]
  collection_model: string
  expected_growth_rate: number
  current_payment_provider: string
}

export interface PainPointProfile {
  startup_id: string
  payment_delay_issue: boolean
  failed_payment_count_monthly: number
  reconciliation_effort_hours_weekly: number
  cash_visibility_gap: boolean
  number_of_bank_accounts: number
  number_of_providers: number
  cost_pressure: boolean
  cfo_urgency: boolean
  provider_switch_risk: boolean
}

export interface ExpansionSignal {
  signal_id: string
  startup_id: string
  signal_type: string
  country: string | null
  signal_date: string
  source_type: string
  source_label: string
  confidence: number
  evidence_note: string
}

export interface ProfileBundle {
  profile: StartupProfile
  payment: PaymentProfile | null
  pain: PainPointProfile | null
  signals: ExpansionSignal[]
}

export interface DriverScore {
  driver_name: string
  weight: number
  raw_score: number
  weighted_score: number
  rationale: string
  missing_data: boolean
}

export interface SubScore {
  sub_score_type: string
  score_value: number
  weight_config_version: string
  driver_scores: DriverScore[]
  top_drivers: string[]
  missing_data_flags: string[]
  confidence_band: 'high' | 'medium' | 'low'
  rationale: string
}

export interface ScoreRecord {
  startup_id: string
  sub_scores: SubScore[]
  final_score: number
  priority_band: PriorityBand
  weight_config_version: string
  missing_data_flags: string[]
  threshold_detail: Record<string, unknown>
  created_at: string
}

export interface RecommendationRecord {
  recommendation_id: string
  startup_id: string
  score_record_id: string
  final_score: number
  priority_band: PriorityBand
  client_summary: string
  why_now: string
  top_drivers: string[]
  missing_drivers: string[]
  evidence_used: string[]
  suggested_questions: string[]
  product_themes: string[]
  caveats: string[]
  what_not_to_claim: string[]
  approval_status: ApprovalStatus
  approver: string | null
  approved_at: string | null
  generated_at: string
  llm_used: boolean
  guardrail_flags: string[]
  evidence_confidence: 'high' | 'medium' | 'low'
  validation_notes: string[]
}

export interface AuditEvent {
  audit_id: string
  startup_id: string
  event_type: string
  payload: Record<string, unknown>
  actor: string
  timestamp: string
}

export interface WeightConfig {
  version_id: string
  owner: string
  created_date: string
  approved_date: string | null
  active: boolean
  change_reason: string
}

export const SUB_SCORE_LABELS: Record<string, string> = {
  revenue_potential: 'Revenue potential',
  client_pain_point_intensity: 'Client pain-point intensity',
  strategic_fit: 'Strategic fit',
  early_signal_detectability: 'Early-signal detectability',
  rm_actionability: 'RM actionability',
  data_availability_explainability: 'Data availability & explainability',
  control_implementation_feasibility: 'Control & implementation feasibility',
}

export const PRIORITY_BAND_LABELS: Record<PriorityBand, string> = {
  high_priority: 'High priority',
  monitor: 'Monitor',
  validate: 'Validate',
  no_immediate_action: 'No immediate action',
}
