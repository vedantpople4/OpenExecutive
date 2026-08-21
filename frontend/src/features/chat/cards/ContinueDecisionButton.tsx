import './ContinueDecisionButton.css'

interface ContinueDecisionButtonProps {
  onContinue: () => void
}

/** Starts a new run with parentRunId set to this decision — the real branch point in the
 * "history as a tree" design (see plan Section 9), not a client-side grouping heuristic. */
export function ContinueDecisionButton({ onContinue }: ContinueDecisionButtonProps) {
  return (
    <button type="button" className="continue-decision-button" onClick={onContinue}>
      Continue this decision →
    </button>
  )
}
