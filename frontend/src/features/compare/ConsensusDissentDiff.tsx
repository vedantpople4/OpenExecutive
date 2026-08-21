import { DiffList } from './DiffList'
import type { CompareResult } from '../../api/types'

interface ConsensusDissentDiffProps {
  result: CompareResult
}

export function ConsensusDissentDiff({ result }: ConsensusDissentDiffProps) {
  return (
    <div className="compare-section">
      <DiffList title="Consensus" added={result.consensus_added} removed={result.consensus_removed} />
      <DiffList title="Dissent" added={result.dissent_added} removed={result.dissent_removed} />
    </div>
  )
}
