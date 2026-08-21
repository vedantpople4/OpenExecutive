import { RoleBadge } from '../../components/RoleBadge'
import type { AgentScoreDelta } from '../../api/types'
import './AgentScoreDeltaTable.css'

interface AgentScoreDeltaTableProps {
  scores: AgentScoreDelta[]
}

function formatScore(score: number | null): string {
  return score === null ? '—' : `${Math.round(score * 100)}%`
}

export function AgentScoreDeltaTable({ scores }: AgentScoreDeltaTableProps) {
  return (
    <table className="agent-score-delta-table">
      <thead>
        <tr>
          <th>Agent</th>
          <th>Older</th>
          <th>Newer</th>
          <th>Delta</th>
        </tr>
      </thead>
      <tbody>
        {scores.map((score) => (
          <tr key={score.agent}>
            <td>
              <RoleBadge name={score.agent} />
            </td>
            <td>{formatScore(score.old)}</td>
            <td>{formatScore(score.new)}</td>
            <td
              className={
                score.delta === null
                  ? ''
                  : score.delta > 0
                    ? 'agent-score-delta-table__positive'
                    : score.delta < 0
                      ? 'agent-score-delta-table__negative'
                      : ''
              }
            >
              {score.delta === null ? '—' : `${score.delta > 0 ? '+' : ''}${Math.round(score.delta * 100)}%`}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
