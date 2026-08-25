import type { ErrorCardData } from '../chat.types'
import './ErrorCard.css'

interface ErrorCardProps {
  error: ErrorCardData
}

/** Renders inline, not as a toast, so the transcript stays a faithful record of what happened. */
export function ErrorCard({ error }: ErrorCardProps) {
  const stopped = error.variant === 'stopped'
  return (
    <div className={`error-card${stopped ? ' error-card--stopped' : ''}`}>
      <span className="error-card__icon">{stopped ? '■' : '!'}</span>
      <div>
        <p className="error-card__message">{error.message}</p>
        {error.phase && (
          <p className="error-card__meta">
            {error.phase}
            {error.agentName && ` — ${error.agentName.toUpperCase()}`}
          </p>
        )}
      </div>
    </div>
  )
}
