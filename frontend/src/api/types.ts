/**
 * Data contracts shared across every feature. Traced 1:1 from the OpenExec Python domain
 * model (AgentReport in openexec/agents/interface.py, event dataclasses in openexec/events.py,
 * and the JSON records under decisions/) so the shapes here match what a real backend will
 * eventually serve. See /Users/vedantpople/.claude/plans/curious-orbiting-shore.md Section 4.
 */

export type CXOName = 'ceo' | 'cfo' | 'cto' | 'cmo'

export interface Agent {
  name: CXOName
  role: string
  focus: string
  hasSystemPrompt: boolean
}

export interface Specialist {
  name: string
  parentCXO: CXOName
}

export type TeamStructure = Record<CXOName, Specialist[]>

export interface AgentReport {
  title: string
  summary: string
  key_findings: string[]
  recommendations: string[]
  risks: string[]
  alignment_score: number // 0.0-1.0
  round_number: number // 0 = Phase-2 blind report, 1-5+ = deliberation round
  is_fallback: boolean // LLM failure stub - must render visibly

  verdict?: string | null // strategic | financial | technical | market
  contingencies: string[]

  // Round-only fields (present when round_number > 0)
  agreements: string[]
  conflicts: string[]
  required_changes: string[]
  revised_recommendations: string[]
  challenged_by: string[]

  // CEO round-1 only
  challenges_for_cfo?: string[]
  challenges_for_cto?: string[]
  challenges_for_cmo?: string[]

  // CEO round-5 only
  board_decision?: BoardDecision | null

  extra_fields?: Record<string, unknown>
}

export interface BoardDecision {
  consensus_points: string[]
  dissent_points: string[]
  final_priority_actions: string[] // "[Action] | Owner: X | Timeframe: Y" - parse client-side
  dissenting_opinions: string[]
  contingencies: string[]
  summary?: string
  status?: 'converged' | string
}

export type DeliberationEventType =
  | 'simulation_initialized'
  | 'inception_started'
  | 'inception_completed'
  | 'analysis_started'
  | 'agent_report_generated'
  | 'analysis_completed'
  | 'team_analysis_started'
  | 'specialist_report_generated'
  | 'team_analysis_completed'
  | 'deliberation_started'
  | 'deliberation_round_started'
  | 'agent_speaking' // gap vs. today's backend - frontend degrades gracefully if absent
  | 'deliberation_round_completed'
  | 'deliberation_completed'
  | 'synthesis_started'
  | 'synthesis_completed'
  | 'error_occurred'

interface DeliberationEventBase {
  event_id: string
  timestamp: string // ISO 8601
  aggregate_id: string // = runId / simulation_id
  type: DeliberationEventType
}

export interface SimulationInitializedEvent extends DeliberationEventBase {
  type: 'simulation_initialized'
  core_prompt: string
  decision_point: string | null
  agent_names: string[]
}

export interface PhaseBoundaryEvent extends DeliberationEventBase {
  type:
    | 'inception_started'
    | 'inception_completed'
    | 'analysis_started'
    | 'analysis_completed'
    | 'team_analysis_started'
    | 'team_analysis_completed'
    | 'deliberation_started'
    | 'deliberation_completed'
    | 'synthesis_started'
}

export interface AgentSpeakingEvent extends DeliberationEventBase {
  type: 'agent_speaking'
  agent_name: string
  round_number?: number
}

export interface AgentReportGeneratedEvent extends DeliberationEventBase {
  type: 'agent_report_generated' | 'specialist_report_generated'
  agent_name: string
  parent_cxo?: string // present for specialist_report_generated
  report_data: AgentReport
}

export interface DeliberationRoundStartedEvent extends DeliberationEventBase {
  type: 'deliberation_round_started'
  round_number: number
}

export interface DeliberationRoundCompletedEvent extends DeliberationEventBase {
  type: 'deliberation_round_completed'
  round_number: number
  reports: Record<string, AgentReport>
}

export interface SynthesisCompletedEvent extends DeliberationEventBase {
  type: 'synthesis_completed'
  final_report: DecisionDetail
}

export interface ErrorOccurredEvent extends DeliberationEventBase {
  type: 'error_occurred'
  error_message: string
  phase: string
  agent_name?: string
}

export type DeliberationEvent =
  | SimulationInitializedEvent
  | PhaseBoundaryEvent
  | AgentSpeakingEvent
  | AgentReportGeneratedEvent
  | DeliberationRoundStartedEvent
  | DeliberationRoundCompletedEvent
  | SynthesisCompletedEvent
  | ErrorOccurredEvent

export interface DecisionSummary {
  runId: string
  timestamp: string // ISO 8601
  prompt: string
  decisionPoint?: string
  executiveSummary?: string
  actionItemCount: number
  topRisks: string[]
  agentAlignment: Partial<Record<CXOName, number>>
  parentRunId?: string // set only when this run was started via "Continue this decision"
  hasChildren?: boolean // denormalized so HistoryItem can render BranchIndicator without a join
}

export interface ActionItem {
  priority: 'HIGH' | 'MEDIUM' | 'LOW'
  task: string
  owner: string
  due_date: string
}

export interface DecisionDetail {
  runId: string
  timestamp: string
  prompt: string
  decision_point: string | null
  executive_summary: string
  parentRunId?: string
  agent_reports: Record<string, AgentReport>
  deliberation_rounds: Record<number, Record<string, AgentReport>>
  board_decision: BoardDecision
  action_items: ActionItem[]
  overall_risk_assessment: string[]
  synthesized_recommendations: string[]
  fallback_warnings: string[]
}

export interface AgentScoreDelta {
  agent: string
  old: number | null
  new: number | null
  delta: number | null
}

export interface CompareResult {
  old_prompt: string
  new_prompt: string
  same_prompt: boolean
  old_summary: string
  new_summary: string
  consensus_added: string[]
  consensus_removed: string[]
  dissent_added: string[]
  dissent_removed: string[]
  actions_added: string[]
  actions_removed: string[]
  risks_added: string[]
  risks_removed: string[]
  agent_scores: AgentScoreDelta[]
}

export interface RegisterSummary {
  total_decisions: number
  distinct_prompts: number
  total_action_items: number
  high_priority_actions: number
  top_risks: { text: string; count: number }[]
  agent_alignment: Record<string, { mean: number; samples: number }>
  per_month: { month: string; count: number }[]
  most_recent: string
}
