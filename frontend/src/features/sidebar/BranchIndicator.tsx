import './BranchIndicator.css'

/** Shown on a HistoryItem when another run was started from it via "Continue this decision". */
export function BranchIndicator() {
  return (
    <span className="branch-indicator" role="img" aria-label="Has follow-up decisions" title="Has follow-up decisions">
      ⑂
    </span>
  )
}
