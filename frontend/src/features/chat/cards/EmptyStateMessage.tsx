import './EmptyStateMessage.css'

const EXAMPLE_PROMPTS = [
  'Should we hire more Software Engineers or build AI agents to do the work?',
  'Should we raise prices on the Pro tier by 15% next quarter?',
  'Should we build our own data pipeline or buy a vendor solution?',
]

interface EmptyStateMessageProps {
  onPickExample?: (prompt: string) => void
}

export function EmptyStateMessage({ onPickExample }: EmptyStateMessageProps) {
  return (
    <div className="empty-state">
      <h2>Bring a decision to the board</h2>
      <p>
        The CEO, CFO, CTO, and CMO will each analyze it independently, then deliberate over
        several rounds until they converge on a decision with explicit consensus, dissent, and
        action items.
      </p>
      <ul className="empty-state__examples">
        {EXAMPLE_PROMPTS.map((example) => (
          <li key={example}>
            <button type="button" onClick={() => onPickExample?.(example)}>
              {example}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
