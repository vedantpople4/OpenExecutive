import './ContinuationBanner.css'

interface ContinuationBannerProps {
  parentPrompt: string
  onCancel: () => void
}

/** Shown above PromptInput when the next submission will carry parentRunId — gives the user
 * visible context (and an escape hatch) for the branch they're about to create. */
export function ContinuationBanner({ parentPrompt, onCancel }: ContinuationBannerProps) {
  return (
    <div className="continuation-banner">
      <span>
        Continuing from: <em>{parentPrompt}</em>
      </span>
      <button type="button" onClick={onCancel} aria-label="Cancel continuation">
        ×
      </button>
    </div>
  )
}
