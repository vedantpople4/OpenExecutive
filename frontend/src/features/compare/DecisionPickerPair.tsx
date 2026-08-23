import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useDecisionHistory } from '../sidebar/hooks/useDecisionHistory'
import './DecisionPickerPair.css'

interface DecisionPickerPairProps {
  initialOldId?: string
  initialNewId?: string
}

export function DecisionPickerPair({ initialOldId, initialNewId }: DecisionPickerPairProps) {
  const navigate = useNavigate()
  const { decisions, isLoading } = useDecisionHistory('')
  const [oldId, setOldId] = useState(initialOldId ?? '')
  const [newId, setNewId] = useState(initialNewId ?? '')

  function handleCompare() {
    if (oldId && newId) navigate(`/compare/${oldId}/${newId}`)
  }

  if (isLoading) return <p className="decision-picker-pair__loading">Loading decisions...</p>
  if (!decisions || decisions.length < 2) {
    return <p className="decision-picker-pair__loading">Need at least two decisions to compare.</p>
  }

  return (
    <div className="decision-picker-pair">
      <label>
        Older decision
        <select value={oldId} onChange={(e) => setOldId(e.target.value)}>
          <option value="" disabled>
            Select a decision...
          </option>
          {decisions.map((d) => (
            <option key={d.runId} value={d.runId}>
              {d.prompt}
            </option>
          ))}
        </select>
      </label>
      <label>
        Newer decision
        <select value={newId} onChange={(e) => setNewId(e.target.value)}>
          <option value="" disabled>
            Select a decision...
          </option>
          {decisions.map((d) => (
            <option key={d.runId} value={d.runId}>
              {d.prompt}
            </option>
          ))}
        </select>
      </label>
      <button type="button" onClick={handleCompare} disabled={!oldId || !newId}>
        Compare
      </button>
    </div>
  )
}
