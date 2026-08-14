export type Variant = 'control' | 'guided'

export type StepKey =
  | 'workspace_created'
  | 'integration_connected'
  | 'data_imported'
  | 'campaign_created'

export interface Session {
  visitor_id: string
  company_name: string
  business_type: string
  variant: Variant
  completed_steps: StepKey[]
  progress_percent: number
  is_activated: boolean
  customer_count: number
  integration: { provider: string; external_store_id: string } | null
  campaign_count: number
  created_at: string
  activated_at: string | null
}

export interface VariantMetric {
  variant: Variant
  label: string
  sessions: number
  activated: number
  activation_rate: number
}

export interface FunnelMetric {
  step: StepKey
  label: string
  count: number
  rate: number
  by_variant: Record<Variant, { count: number; rate: number }>
}

export interface ExperimentStats {
  difference_pp: number
  relative_uplift_percent: number
  z_score: number
  p_value: number
  significant_at_95: boolean
  ci_95_difference_pp: [number, number]
  sample_ratio_mismatch: {
    chi_square: number
    p_value: number
    flagged: boolean
  }
}

export interface Metrics {
  sessions: number
  activated: number
  activation_rate: number
  average_time_to_activation_minutes: number
  variants: VariantMetric[]
  experiment: ExperimentStats
  funnel: FunnelMetric[]
  event_counts: Record<string, number>
  import_summary: Record<string, number>
}

export interface ImportJob {
  id: number
  source_filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_rows: number
  imported_rows: number
  failed_rows: number
  error_message: string
  created_at: string
  finished_at: string | null
}

export interface CopilotRecommendation {
  title: string
  reason: string
  action: string
  risk: string
}

export interface CopilotResponse {
  provider: 'rules' | 'openai' | 'rules_fallback'
  recommendations: CopilotRecommendation[]
}
