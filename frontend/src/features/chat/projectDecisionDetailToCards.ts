import type { DecisionDetail } from '../../api/types'
import type { AgentReportEntry, RoundCardData, TranscriptCard } from './chat.types'

/**
 * Adapts an already-persisted DecisionDetail (a completed decision loaded from history) into
 * the same TranscriptCard tree projectEventsToCards produces for a live run, so PhaseCard/
 * RoundCard/AgentReportCard/BoardDecisionCard can render either without knowing which one they
 * got. Everything renders as 'done' — there's no speaking/in-progress state for a past record.
 */
export function projectDecisionDetailToCards(detail: DecisionDetail): TranscriptCard[] {
  const cards: TranscriptCard[] = []

  cards.push({
    kind: 'phase',
    id: `${detail.runId}-inception`,
    phase: 'inception',
    status: 'done',
    reports: [],
    speaking: [],
    rounds: [],
  })

  const analysisReports: AgentReportEntry[] = Object.entries(detail.agent_reports).map(
    ([agentName, report]) => ({ agentName, report }),
  )
  cards.push({
    kind: 'phase',
    id: `${detail.runId}-analysis`,
    phase: 'analysis',
    status: 'done',
    reports: analysisReports,
    speaking: [],
    rounds: [],
  })

  const roundNumbers = Object.keys(detail.deliberation_rounds)
    .map(Number)
    .sort((a, b) => a - b)

  if (roundNumbers.length > 0) {
    const rounds: RoundCardData[] = roundNumbers.map((roundNumber) => ({
      kind: 'round',
      id: `${detail.runId}-round-${roundNumber}`,
      roundNumber,
      status: 'done',
      speaking: [],
      reports: Object.entries(detail.deliberation_rounds[roundNumber]).map(
        ([agentName, report]) => ({ agentName, report }),
      ),
    }))
    cards.push({
      kind: 'phase',
      id: `${detail.runId}-deliberation`,
      phase: 'deliberation',
      status: 'done',
      reports: [],
      speaking: [],
      rounds,
    })
  }

  // A failed or stopped run has no board decision to show. Keying the fallback
  // off the decision's presence (not status alone) means rows persisted before
  // status was exposed still render correctly.
  const hasBoardDecision =
    detail.board_decision != null && Object.keys(detail.board_decision).length > 0

  if (detail.status === 'error') {
    cards.push({
      kind: 'error',
      id: `${detail.runId}-error`,
      variant: 'error',
      message: detail.error_message ?? 'This deliberation failed before reaching a decision.',
    })
  } else if (!hasBoardDecision) {
    cards.push({
      kind: 'error',
      id: `${detail.runId}-incomplete`,
      variant: 'stopped',
      message:
        detail.status === 'stopped'
          ? 'This deliberation was stopped before the board reached a decision. The discussion above is what completed.'
          : 'No board decision was recorded for this run.',
    })
  } else {
    cards.push({
      kind: 'board_decision',
      id: `${detail.runId}-board-decision`,
      boardDecision: detail.board_decision,
      sourceRunId: detail.runId,
      sourcePrompt: detail.prompt,
    })
  }

  return cards
}
