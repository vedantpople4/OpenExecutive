import { useState } from 'react'
import { AgentReportCard } from './AgentReportCard'
import { AgentSpeakingIndicator } from './AgentSpeakingIndicator'
import { RoundCard } from './RoundCard'
import type { PhaseCardData, PhaseKind } from '../chat.types'
import './PhaseCard.css'

const PHASE_LABELS: Record<PhaseKind, string> = {
  inception: 'Inception',
  analysis: 'Analysis',
  team_analysis: 'Team Analysis',
  deliberation: 'Deliberation',
}

interface PhaseCardProps {
  phase: PhaseCardData;
}

export function PhaseCard({ phase }: PhaseCardProps) {
  const [manuallyOpen, setManuallyOpen] = useState<boolean | null>(null)
  const isOpen = manuallyOpen ?? phase.status === 'running'

  return (
    <div className="phase-card">
      <button
        type="button"
        className="phase-card__header"
        onClick={() => setManuallyOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <span className={`phase-card__chevron ${isOpen ? 'phase-card__chevron--open' : ''}`}>▸</span>
        <span className="phase-card__title">{PHASE_LABELS[phase.phase]}</span>
        <span className={`phase-card__status phase-card__status--${phase.status}`}>
          {phase.status === 'running' ? 'in progress' : 'done'}
        </span>
      </button>

      {isOpen && (
        <div className="phase-card__body">
          {phase.speaking.map((entry) => (
            <AgentSpeakingIndicator key={`speaking-${entry.agentName}`} entry={entry} />
          ))}
          {phase.reports.map((entry) => (
            <AgentReportCard key={`report-${entry.agentName}`} entry={entry} />
          ))}
          {phase.rounds.map((round) => (
            <RoundCard key={round.id} round={round} />
          ))}
        </div>
      )}
    </div>
  )
}
