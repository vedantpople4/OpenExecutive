import type { ErrorCardData } from '../chat.types'
import './ErrorCard.css'

interface ErrorCardProps {
  error: ErrorCardData
  /** Re-asks the same question as a fresh run. Omitted when there is nothing to retry with. */
  onRetry?: () => void
}

/** Renders inline, not as a toast, so the transcript stays a faithful record of what happened. */
export function ErrorCard({ error, onRetry }: ErrorCardProps) {
  const stopped = error.variant === 'stopped'
  return (
    // role="alert" only on a genuine failure. A stopped run is the user's own doing --
    // interrupting a screen reader to announce what they just asked for is noise.
    <div
      className={`error-card${stopped ? ' error-card--stopped' : ''}`}
      role={stopped ? undefined : 'alert'}
    >
      <span className="error-card__icon">{stopped ? '■' : '!'}</span>
      <div className="error-card__body">
        <p className="error-card__message">{error.message}</p>
        {error.phase && (
          <p className="error-card__meta">
            {error.phase}
            {error.agentName && ` — ${error.agentName.toUpperCase()}`}
          </p>
        )}
        {onRetry && (
          <button type="button" className="error-card__retry" onClick={onRetry}>
            Try again
          </button>
        )}
      </div>
    </div>
  )
}
