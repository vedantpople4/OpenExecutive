import { motion } from 'motion/react'
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
      {entries.map(([agent, stat], i) => (
        <div key={agent} className="agent-alignment-chart__row">
          <RoleBadge name={agent} />
          <div className="agent-alignment-chart__track">
            {/* scaleX, not width -- see AlignmentScoreMeter for why. The small per-row
                delay makes the set read as one chart filling in rather than four
                independent bars that happen to start together. */}
            <motion.div
              className="agent-alignment-chart__fill"
              style={{ transformOrigin: 'left' }}
              initial={{ scaleX: 0 }}
              animate={{ scaleX: stat.mean }}
              transition={{ duration: 0.5, ease: 'easeOut', delay: i * 0.06 }}
            />
          </div>
          <span className="agent-alignment-chart__value">{Math.round(stat.mean * 100)}%</span>
          <span className="agent-alignment-chart__samples">{stat.samples} samples</span>
        </div>
      ))}
    </div>
  )
}
