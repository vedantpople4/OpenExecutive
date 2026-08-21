import type { ReactNode } from 'react'
import type { BoardDecision } from '../../../api/types'
import './BoardDecisionCard.css'

interface ParsedActionItem {
  action: string
  owner?: string
  timeframe?: string
}

/** Parses "[Action] | Owner: X | Timeframe: Y" into fields; falls back to the raw string. */
function parseActionItemString(raw: string): ParsedActionItem {
  const match = raw.match(/^\[(.+?)\]\s*(?:\|\s*Owner:\s*(.+?))?\s*(?:\|\s*Timeframe:\s*(.+))?$/)
  if (!match) return { action: raw }
  const [, action, owner, timeframe] = match
  return { action, owner, timeframe }
}

function List({ items }: { items: string[] }) {
  if (items.length === 0) return <p className="board-decision-card__empty">None recorded.</p>
  return (
    <ul>
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  )
}

interface BoardDecisionCardProps {
  boardDecision: BoardDecision
  children?: ReactNode
}

export function BoardDecisionCard({ boardDecision, children }: BoardDecisionCardProps) {
  const actionItems = boardDecision.final_priority_actions.map(parseActionItemString)

  return (
    <div className="board-decision-card">
      <div className="board-decision-card__header">
        <span className="board-decision-card__badge">Board Decision</span>
        {boardDecision.status && <span className="board-decision-card__status">{boardDecision.status}</span>}
      </div>

      {boardDecision.summary && <p className="board-decision-card__summary">{boardDecision.summary}</p>}

      <div className="board-decision-card__grid">
        <section>
          <h4>Consensus</h4>
          <List items={boardDecision.consensus_points} />
        </section>
        <section>
          <h4>Dissent</h4>
          <List items={[...boardDecision.dissent_points, ...boardDecision.dissenting_opinions]} />
        </section>
      </div>

      <section>
        <h4>Priority actions</h4>
        {actionItems.length === 0 ? (
          <p className="board-decision-card__empty">None recorded.</p>
        ) : (
          <ul className="board-decision-card__actions">
            {actionItems.map((item, i) => (
              <li key={i}>
                <span className="board-decision-card__action-text">{item.action}</span>
                {item.owner && <span className="board-decision-card__action-owner">{item.owner}</span>}
                {item.timeframe && <span className="board-decision-card__action-timeframe">{item.timeframe}</span>}
              </li>
            ))}
          </ul>
        )}
      </section>

      {boardDecision.contingencies.length > 0 && (
        <section>
          <h4>Contingencies</h4>
          <List items={boardDecision.contingencies} />
        </section>
      )}

      {children}
    </div>
  )
}
