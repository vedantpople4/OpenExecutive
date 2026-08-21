import { useParams } from 'react-router-dom'
import { DecisionPickerPair } from './DecisionPickerPair'
import { SummaryDiff } from './SummaryDiff'
import { ConsensusDissentDiff } from './ConsensusDissentDiff'
import { ActionItemsDiff } from './ActionItemsDiff'
import { RisksDiff } from './RisksDiff'
import { AgentScoreDeltaTable } from './AgentScoreDeltaTable'
import { useCompare } from './hooks/useCompare'
import './ComparePage.css'

export function ComparePage() {
  const { oldId, newId } = useParams<{ oldId?: string; newId?: string }>()
  const hasBothIds = oldId !== undefined && newId !== undefined
  const { data: result, isLoading, isError } = useCompare(oldId ?? null, newId ?? null)

  return (
    <div className="compare-page">
      <h1>Compare decisions</h1>
      <DecisionPickerPair initialOldId={oldId} initialNewId={newId} />

      {hasBothIds && isLoading && <p>Loading comparison...</p>}
      {hasBothIds && isError && <p>Could not load this comparison.</p>}

      {result && (
        <>
          <div className="compare-panel">
            <h2>Summary</h2>
            <SummaryDiff
              oldPrompt={result.old_prompt}
              newPrompt={result.new_prompt}
              oldSummary={result.old_summary}
              newSummary={result.new_summary}
              samePrompt={result.same_prompt}
            />
          </div>

          <div className="compare-panel">
            <h2>Agent alignment</h2>
            <AgentScoreDeltaTable scores={result.agent_scores} />
          </div>

          <div className="compare-panel">
            <ConsensusDissentDiff result={result} />
          </div>

          <div className="compare-panel">
            <ActionItemsDiff result={result} />
          </div>

          <div className="compare-panel">
            <RisksDiff result={result} />
          </div>
        </>
      )}
    </div>
  )
}
