import { RoleBadge } from '../../components/RoleBadge'
import './AgentAlignmentChart.css'

interface AgentAlignmentChartProps {
  alignment: Record<string, { mean: number; samples: number }>
}

export function AgentAlignmentChart({ alignment }: AgentAlignmentChartProps) {
  const entries = Object.entries(alignment)
  if (entries.length === 0) return <p className="agent-alignment-chart__empty">No data yet.</p>

  return (
    <div className="agent-alignment-chart">
      {entries.map(([agent, stat]) => (
        <div key={agent} className="agent-alignment-chart__row">
          <RoleBadge name={agent} />
          <div className="agent-alignment-chart__track">
            <div className="agent-alignment-chart__fill" style={{ width: `${stat.mean * 100}%` }} />
          </div>
          <span className="agent-alignment-chart__value">{Math.round(stat.mean * 100)}%</span>
          <span className="agent-alignment-chart__samples">{stat.samples} samples</span>
        </div>
      ))}
    </div>
  )
}
