import { motion } from 'motion/react'
import './ActivityByMonthChart.css'

interface ActivityByMonthChartProps {
  perMonth: { month: string; count: number }[]
}

function formatMonthLabel(month: string): string {
  const [year, monthNum] = month.split('-')
  const date = new Date(Number(year), Number(monthNum) - 1, 1)
  return date.toLocaleString('en-US', { month: 'short' })
}

export function ActivityByMonthChart({ perMonth }: ActivityByMonthChartProps) {
  if (perMonth.length === 0) return <p className="activity-by-month-chart__empty">No activity yet.</p>

  const maxCount = Math.max(...perMonth.map((m) => m.count))

  return (
    <div className="activity-by-month-chart">
      {perMonth.map((m, i) => (
        <div key={m.month} className="activity-by-month-chart__bar-wrapper">
          <span className="activity-by-month-chart__count">{m.count}</span>
          {/* height stays the inline layout value so the count label above each bar sits
              at its final position from the first frame; only scaleY animates, which is
              a transform and so honours reducedMotion="user" for free. Origin is bottom
              because the bars sit on a baseline. */}
          <motion.div
            className="activity-by-month-chart__bar"
            style={{ height: `${(m.count / maxCount) * 100}%`, transformOrigin: 'bottom' }}
            initial={{ scaleY: 0 }}
            animate={{ scaleY: 1 }}
            transition={{ duration: 0.4, ease: 'easeOut', delay: i * 0.04 }}
          />
          <span className="activity-by-month-chart__label">{formatMonthLabel(m.month)}</span>
        </div>
      ))}
    </div>
  )
}
