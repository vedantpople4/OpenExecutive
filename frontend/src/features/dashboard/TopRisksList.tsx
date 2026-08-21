import './TopRisksList.css'

interface TopRisksListProps {
  risks: { text: string; count: number }[]
}

export function TopRisksList({ risks }: TopRisksListProps) {
  if (risks.length === 0) return <p className="top-risks-list__empty">No recurring risks yet.</p>

  const maxCount = Math.max(...risks.map((r) => r.count));

  return (
    <ul className="top-risks-list">
      {risks.map((risk) => (
        <li key={risk.text}>
          <div className="top-risks-list__bar-track">
            <div
              className="top-risks-list__bar-fill"
              style={{ width: `${(risk.count / maxCount) * 100}%` }}
            />
          </div>
          <span className="top-risks-list__text">{risk.text}</span>
          <span className="top-risks-list__count">{risk.count}×</span>
        </li>
      ))}
    </ul>
  )
}
