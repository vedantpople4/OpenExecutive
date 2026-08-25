import type { RunOutcome } from '../../api/types'
import './RunStatusBadge.css'

interface RunStatusBadgeProps {
  status?: RunOutcome
}

/** Marks a run that ended badly, so failures are visible in the sidebar without
 * opening each decision. Silent for the ordinary cases — a badge on every row
 * would carry no information. */
export function RunStatusBadge({ status }: RunStatusBadgeProps) {
  if (status !== 'error' && status !== 'stopped') return null

  const label = status === 'error' ? 'Deliberation failed' : 'Stopped before a decision'
  return (
    <span
      className={`run-status-badge run-status-badge--${status}`}
      role="img"
      aria-label={label}
      title={label}
    >
      {status === 'error' ? '!' : '■'}
    </span>
  )
}
