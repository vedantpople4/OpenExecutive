import { Link } from 'react-router-dom'
import { BranchIndicator } from './BranchIndicator'
import { RunStatusBadge } from './RunStatusBadge'
import { formatRelativeTime } from '../../lib/formatRelativeTime'
import type { DecisionSummary } from '../../api/types'
import './HistoryItem.css'

interface HistoryItemProps {
  decision: DecisionSummary
  isActive: boolean
}

function truncate(text: string, max = 60): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text
}

export function HistoryItem({ decision, isActive }: HistoryItemProps) {
  return (
    <Link
      to={`/chat/${decision.runId}`}
      className={`history-item ${isActive ? 'history-item--active' : ''}`}
    >
      <span className="history-item__prompt">{truncate(decision.prompt)}</span>
      <span className="history-item__meta">
        <span className="history-item__time">{formatRelativeTime(decision.timestamp)}</span>
        {decision.topRisks.length > 0 && (
          <span
            className="history-item__risk-dot"
            role="img"
            aria-label="Has flagged risks"
            title="Has flagged risks"
          />
        )}
        <RunStatusBadge status={decision.status} />
        {decision.hasChildren && <BranchIndicator />}
      </span>
    </Link>
  )
}
