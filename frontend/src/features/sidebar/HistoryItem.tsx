import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BranchIndicator } from './BranchIndicator'
import { RunStatusBadge } from './RunStatusBadge'
import { useDeleteDecision } from './hooks/useDeleteDecision'
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

function TrashIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M2.5 4h11" />
      <path d="M6.5 4V2.5h3V4" />
      <path d="M4 4l.6 9a1 1 0 001 1h4.8a1 1 0 001-1L12 4" />
      <path d="M6.5 7v4M9.5 7v4" />
    </svg>
  )
}

export function HistoryItem({ decision, isActive }: HistoryItemProps) {
  const [confirming, setConfirming] = useState(false)
  const navigate = useNavigate()
  const { mutate, isPending, isError, error } = useDeleteDecision()

  function handleDelete() {
    mutate(decision.runId, {
      onSuccess: () => {
        setConfirming(false)
        // Leaving the user on a chat route for a run that no longer exists
        // would just render a 404 from the detail fetch.
        if (isActive) navigate('/')
      },
    })
  }

  // An inline confirm rather than window.confirm: a native dialog is untestable
  // under jsdom and blocks the whole tab for a destructive action that is one
  // click to reach.
  if (confirming) {
    return (
      <div className="history-item history-item--confirming">
        <span className="history-item__prompt">{truncate(decision.prompt)}</span>
        <div className="history-item__confirm">
          <span className="history-item__confirm-label">
            {isError ? (error as Error).message : 'Delete permanently?'}
          </span>
          <button
            type="button"
            className="history-item__confirm-yes"
            onClick={handleDelete}
            disabled={isPending}
          >
            {isPending ? 'Deleting…' : 'Delete'}
          </button>
          <button
            type="button"
            className="history-item__confirm-no"
            onClick={() => setConfirming(false)}
            disabled={isPending}
          >
            Cancel
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={`history-item ${isActive ? 'history-item--active' : ''}`}>
      {/* The link is a child rather than the wrapper: a <button> nested inside
          an <a> is invalid HTML, and the anchor would swallow its clicks and
          navigate instead of deleting. */}
      <Link to={`/chat/${decision.runId}`} className="history-item__link">
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

      <button
        type="button"
        className="history-item__delete"
        onClick={() => setConfirming(true)}
        aria-label={`Delete decision: ${truncate(decision.prompt, 40)}`}
        title="Delete decision"
      >
        <TrashIcon />
      </button>
    </div>
  )
}
