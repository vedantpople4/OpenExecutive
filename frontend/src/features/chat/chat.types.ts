import type { AgentReport, BoardDecision } from '../../api/types'

export interface AgentReportEntry {
  agentName: string
  report: AgentReport
  parentCXO?: string
}

export interface SpeakingEntry {
  agentName: string
}

export type PhaseKind = 'inception' | 'analysis' | 'team_analysis' | 'deliberation'
export type CardStatus = 'running' | 'done'

export interface RoundCardData {
  kind: 'round'
  id: string
  roundNumber: number
  status: CardStatus
  speaking: SpeakingEntry[]
  reports: AgentReportEntry[]
}

export interface PhaseCardData {
  kind: 'phase'
  id: string
  phase: PhaseKind
  status: CardStatus
  /** Populated for inception/analysis/team_analysis phases. */
  reports: AgentReportEntry[]
  /** Agents currently speaking in this phase with no report yet (non-round phases only). */
  speaking: SpeakingEntry[]
  /** Populated for the deliberation phase only. */
  rounds: RoundCardData[]
}

export interface BoardDecisionCardData {
  kind: 'board_decision'
  id: string
  boardDecision: BoardDecision
  /** The run this decision belongs to — lets "Continue this decision" set parentRunId. */
  sourceRunId: string
  sourcePrompt: string
}

export interface ErrorCardData {
  kind: 'error'
  id: string
  message: string
  phase: string
  agentName?: string
}

export type TranscriptCard = PhaseCardData | BoardDecisionCardData | ErrorCardData
