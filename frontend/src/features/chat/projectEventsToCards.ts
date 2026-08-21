import type { DeliberationEvent } from '../../api/types'
import type { PhaseCardData, PhaseKind, RoundCardData, TranscriptCard } from './chat.types'

interface FoldState {
  currentPhase: PhaseCardData | null
  currentRound: RoundCardData | null
}

/**
 * Pure fold: flat, append-only DeliberationEvent[] -> nested transcript card tree
 * (PhaseCard[] -> (AgentReportEntry[] | RoundCard[]) -> AgentReportEntry[]).
 *
 * Deterministic and side-effect free so it's unit-testable without rendering React, and so IDs
 * derived here stay stable across successive calls as more events arrive (callers key React
 * nodes on these ids to avoid remounting existing cards). See plan Section 5.
 *
 * Mutable fold state is kept on a `state` object (not bare `let` locals) so that narrowing
 * (`state.currentPhase?.phase === ...`) stays correct after calls into the helper functions below
 * that reassign it — this TypeScript toolchain miscompiles that narrowing for plain closed-over
 * `let` variables reassigned inside a sibling function.
 */
export function projectEventsToCards(events: DeliberationEvent[]): TranscriptCard[] {
  const cards: TranscriptCard[] = []
  const state: FoldState = { currentPhase: null, currentRound: null }

  function closeCurrentPhase() {
    if (state.currentPhase) state.currentPhase.status = 'done'
    state.currentPhase = null
    state.currentRound = null
  }

  function openPhase(phase: PhaseKind, id: string) {
    if (state.currentPhase && state.currentPhase.phase !== phase) closeCurrentPhase()
    const existing = cards.find(
      (c): c is PhaseCardData => c.kind === 'phase' && c.phase === phase,
    )
    if (existing) {
      state.currentPhase = existing
      return
    }
    const phaseCard: PhaseCardData = {
      kind: 'phase',
      id,
      phase,
      status: 'running',
      reports: [],
      speaking: [],
      rounds: [],
    }
    cards.push(phaseCard)
    state.currentPhase = phaseCard
  }

  for (const event of events) {
    switch (event.type) {
      case 'simulation_initialized':
        break

      case 'inception_started':
        openPhase('inception', `phase-inception-${event.event_id}`)
        break
      case 'inception_completed':
        if (state.currentPhase?.phase === 'inception') state.currentPhase.status = 'done'
        break

      case 'analysis_started':
        openPhase('analysis', `phase-analysis-${event.event_id}`)
        break
      case 'analysis_completed':
        if (state.currentPhase?.phase === 'analysis') state.currentPhase.status = 'done'
        break

      case 'team_analysis_started':
        openPhase('team_analysis', `phase-team-${event.event_id}`)
        break
      case 'team_analysis_completed':
        if (state.currentPhase?.phase === 'team_analysis') state.currentPhase.status = 'done'
        break

      case 'deliberation_started':
        openPhase('deliberation', `phase-deliberation-${event.event_id}`)
        break
      case 'deliberation_completed':
        if (state.currentPhase?.phase === 'deliberation') state.currentPhase.status = 'done'
        break

      case 'deliberation_round_started': {
        if (state.currentRound) state.currentRound.status = 'done'
        const round: RoundCardData = {
          kind: 'round',
          id: `round-${event.round_number}-${event.event_id}`,
          roundNumber: event.round_number,
          status: 'running',
          speaking: [],
          reports: [],
        }
        state.currentPhase?.rounds.push(round)
        state.currentRound = round
        break
      }
      case 'deliberation_round_completed':
        if (state.currentRound && state.currentRound.roundNumber === event.round_number) {
          state.currentRound.status = 'done'
        }
        break

      case 'agent_speaking': {
        const inRound = event.round_number !== undefined && state.currentRound
        const target = inRound ? state.currentRound : state.currentPhase
        target?.speaking.push({ agentName: event.agent_name })
        break
      }

      case 'agent_report_generated':
      case 'specialist_report_generated': {
        const entry = {
          agentName: event.agent_name,
          report: event.report_data,
          parentCXO: event.parent_cxo,
        }
        const isRoundReport = event.report_data.round_number > 0 && state.currentRound
        const target = isRoundReport ? state.currentRound : state.currentPhase
        if (target) {
          target.speaking = target.speaking.filter((s) => s.agentName !== event.agent_name)
          target.reports.push(entry)
        }
        break
      }

      case 'synthesis_started':
        break
      case 'synthesis_completed':
        closeCurrentPhase()
        cards.push({
          kind: 'board_decision',
          id: `board-${event.event_id}`,
          boardDecision: event.final_report.board_decision,
          sourceRunId: event.aggregate_id,
          sourcePrompt: event.final_report.prompt,
        })
        break

      case 'error_occurred':
        cards.push({
          kind: 'error',
          id: `error-${event.event_id}`,
          message: event.error_message,
          phase: event.phase,
          agentName: event.agent_name,
        })
        break
    }
  }

  return cards
}
