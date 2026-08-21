import './DiffList.css'

interface DiffListProps {
  title: string
  added: string[]
  removed: string[]
}

/** Shared added/removed rendering for consensus/dissent, action items, and risks diffs. */
export function DiffList({ title, added, removed }: DiffListProps) {
  if (added.length === 0 && removed.length === 0) {
    return (
      <div className="diff-list">
        <h4>{title}</h4>
        <p className="diff-list__empty">No changes.</p>
      </div>
    )
  }

  return (
    <div className="diff-list">
      <h4>{title}</h4>
      <ul>
        {added.map((item, i) => (
          <li key={`added-${i}`} className="diff-list__added">
            + {item}
          </li>
        ))}
        {removed.map((item, i) => (
          <li key={`removed-${i}`} className="diff-list__removed">
            − {item}
          </li>
        ))}
      </ul>
    </div>
  )
}
