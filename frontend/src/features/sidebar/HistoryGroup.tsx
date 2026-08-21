import { HistoryItem } from './HistoryItem'
import type { DecisionSummary } from '../../api/types'
import './HistoryGroup.css'

interface HistoryGroupProps {
  label: string
  items: DecisionSummary[]
  activeRunId?: string
}

export function HistoryGroup({ label, items, activeRunId }: HistoryGroupProps) {
  return (
    <div className="history-group">
      {label && <h3 className="history-group__label">{label}</h3>}
      <div className="history-group__items">
        {items.map((item) => (
          <HistoryItem key={item.runId} decision={item} isActive={item.runId === activeRunId} />
        ))}
      </div>
    </div>
  )
}
