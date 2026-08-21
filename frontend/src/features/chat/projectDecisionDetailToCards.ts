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

  cards.push({
    kind: 'board_decision',
    id: `${detail.runId}-board-decision`,
    boardDecision: detail.board_decision,
    sourceRunId: detail.runId,
    sourcePrompt: detail.prompt,
  })

  return cards
}
