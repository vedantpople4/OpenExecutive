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
      {perMonth.map((m) => (
        <div key={m.month} className="activity-by-month-chart__bar-wrapper">
          <span className="activity-by-month-chart__count">{m.count}</span>
          <div
            className="activity-by-month-chart__bar"
            style={{ height: `${(m.count / maxCount) * 100}%` }}
          />
          <span className="activity-by-month-chart__label">{formatMonthLabel(m.month)}</span>
        </div>
      ))}
    </div>
  )
}
