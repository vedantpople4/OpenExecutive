import { RoleBadge } from '../../../components/RoleBadge'
import type { SpeakingEntry } from '../chat.types'
import './AgentSpeakingIndicator.css'

interface AgentSpeakingIndicatorProps {
  entry: SpeakingEntry
}

/**
 * Placeholder for an agent mid-response. Gets *replaced* by an AgentReportCard at the same
 * list position once the matching report event arrives — not a loading state the card itself
 * transitions through (see plan Section 2).
 */
export function AgentSpeakingIndicator({ entry }: AgentSpeakingIndicatorProps) {
  return (
    <div className="agent-speaking">
      <RoleBadge name={entry.agentName} />
      <span className="agent-speaking__label">
        {entry.agentName.toUpperCase()} is thinking
        <span className="agent-speaking__dots">
          <span />
          <span />
          <span />
        </span>
      </span>
    </div>
  )
}
