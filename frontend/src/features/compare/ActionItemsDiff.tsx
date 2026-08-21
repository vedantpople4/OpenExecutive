import { DiffList } from './DiffList'
import type { CompareResult } from '../../api/types'

interface ActionItemsDiffProps {
  result: CompareResult
}

export function ActionItemsDiff({ result }: ActionItemsDiffProps) {
  return (
    <div className="compare-section">
      <DiffList title="Action items" added={result.actions_added} removed={result.actions_removed} />
    </div>
  )
}
