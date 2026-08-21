import './SummaryDiff.css'

interface SummaryDiffProps {
  oldPrompt: string
  newPrompt: string
  oldSummary: string
  newSummary: string
  samePrompt: boolean
}

export function SummaryDiff({ oldPrompt, newPrompt, oldSummary, newSummary, samePrompt }: SummaryDiffProps) {
  return (
    <div className="summary-diff">
      {!samePrompt && (
        <p className="summary-diff__note">These decisions were made in response to different prompts.</p>
      )}
      <div className="summary-diff__columns">
        <div>
          <h4>Older</h4>
          <p className="summary-diff__prompt">{oldPrompt}</p>
          <p>{oldSummary}</p>
        </div>
        <div>
          <h4>Newer</h4>
          <p className="summary-diff__prompt">{newPrompt}</p>
          <p>{newSummary}</p>
        </div>
      </div>
    </div>
  )
}
