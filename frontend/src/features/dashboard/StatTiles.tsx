import './StatTiles.css'

interface StatTilesProps {
  totalDecisions: number
  distinctPrompts: number
  totalActionItems: number
  highPriorityActions: number
}

export function StatTiles({
  totalDecisions,
  distinctPrompts,
  totalActionItems,
  highPriorityActions,
}: StatTilesProps) {
  const tiles = [
    { label: 'Total decisions', value: totalDecisions },
    { label: 'Distinct prompts', value: distinctPrompts },
    { label: 'Action items', value: totalActionItems },
    { label: 'High priority actions', value: highPriorityActions },
  ]

  return (
    <div className="stat-tiles">
      {tiles.map((tile) => (
        <div key={tile.label} className="stat-tiles__tile">
          <span className="stat-tiles__value">{tile.value}</span>
          <span className="stat-tiles__label">{tile.label}</span>
        </div>
      ))}
    </div>
  )
}
