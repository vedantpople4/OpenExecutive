import { DiffList } from './DiffList'
import type { CompareResult } from '../../api/types'

interface RisksDiffProps {
  result: CompareResult
}

export function RisksDiff({ result }: RisksDiffProps) {
  return (
    <div className="compare-section">
      <DiffList title="Risks" added={result.risks_added} removed={result.risks_removed} />
    </div>
  )
}
