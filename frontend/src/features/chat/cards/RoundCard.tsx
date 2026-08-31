import { useState } from 'react'
import { AgentReportCard } from './AgentReportCard'
import { AgentSpeakingIndicator } from './AgentSpeakingIndicator'
import type { RoundCardData } from '../chat.types'
import './RoundCard.css'

const ROUND_LABELS: Record<number, string> = {
  1: 'Framing',
  2: 'Response',
  3: 'Response',
  4: 'Revision',
  5: 'Synthesis',
}

interface RoundCardProps {
  round: RoundCardData
}

export function RoundCard({ round }: RoundCardProps) {
  const [manuallyOpen, setManuallyOpen] = useState<boolean | null>(null)
  const isOpen = manuallyOpen ?? round.status === 'running'

  return (
    <div className="round-card">
      <button
        type="button"
        className="round-card__header"
        onClick={() => setManuallyOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <span className={`round-card__chevron ${isOpen ? 'round-card__chevron--open' : ''}`}>▸</span>
        <span className="round-card__title">
          Round {round.roundNumber}/10 — {ROUND_LABELS[round.roundNumber] ?? 'Deliberation'}
        </span>
        <span className={`round-card__status round-card__status--${round.status}`}>
          {round.status === 'running' ? 'in progress' : 'done'}
        </span>
      </button>

      {isOpen && (
        <div className="round-card__body">
          {round.speaking.map((entry) => (
            <AgentSpeakingIndicator key={`speaking-${entry.agentName}`} entry={entry} />
          ))}
          {round.reports.map((entry) => (
            <AgentReportCard key={`report-${entry.agentName}`} entry={entry} />
          ))}
        </div>
      )}
    </div>
  )
}
