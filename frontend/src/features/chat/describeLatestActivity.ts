import type { TranscriptCard, PhaseCardData, RoundCardData } from './chat.types'

const PHASE_LABELS: Record<PhaseCardData['phase'], string> = {
  inception: 'Inception',
  analysis: 'Analysis',
  team_analysis: 'Team analysis',
  deliberation: 'Deliberation',
}

/**
 * One short sentence describing the newest thing to happen in a run, for the polite live
 * region in MessageList.
 *
 * Deliberately a *derived summary* rather than aria-live on the transcript itself. The
 * transcript holds full agent reports; marking it live would make a screen reader read every
 * report body aloud as it lands, which is unusable during a four-agent deliberation. This
 * announces only the frontier -- who is working, what just landed, where the run is -- which
 * is the same information the animation conveys to a sighted user.
 *
 * Returns null when there is nothing worth announcing yet.
 */
export function describeLatestActivity(cards: TranscriptCard[]): string | null {
  if (cards.some((c) => c.kind === 'board_decision')) {
    return 'The board reached a decision.'
  }

  // Errors are announced by ErrorCard's own role="alert", which interrupts rather than
  // queueing -- correct for a failure, and it would be duplicated if repeated here.
  const phases = cards.filter((c): c is PhaseCardData => c.kind === 'phase')
  const phase = phases.at(-1)
  if (!phase) return null

  const label = PHASE_LABELS[phase.phase]
  const round = phase.rounds.at(-1)
  const scope: PhaseCardData | RoundCardData = round ?? phase
  const where = round ? `${label}, round ${round.roundNumber}` : label

  // Speaking outranks reports: an agent still working is the most recent event, because the
  // projector drops a speaking entry as soon as that agent's report lands.
  const speaking = scope.speaking.at(-1)
  if (speaking) return `${where}: ${speaking.agentName.toUpperCase()} is thinking.`

  const report = scope.reports.at(-1)
  if (report) {
    const percent = Math.round(report.report.alignment_score * 100)
    return `${where}: ${report.agentName.toUpperCase()} reported, ${percent} percent alignment.`
  }

  return `${where} started.`
}
