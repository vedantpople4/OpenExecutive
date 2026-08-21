import type { ErrorCardData } from '../chat.types'
import './ErrorCard.css'

interface ErrorCardProps {
  error: ErrorCardData
}

/** Renders inline, not as a toast, so the transcript stays a faithful record of what happened. */
export function ErrorCard({ error }: ErrorCardProps) {
  return (
    <div className="error-card">
      <span className="error-card__icon">!</span>
      <div>
        <p className="error-card__message">{error.message}</p>
        <p className="error-card__meta">
          {error.phase}
          {error.agentName && ` — ${error.agentName.toUpperCase()}`}
        </p>
      </div>
    </div>
  )
}
