import { StatTiles } from './StatTiles'
import { TopRisksList } from './TopRisksList'
import { AgentAlignmentChart } from './AgentAlignmentChart'
import { ActivityByMonthChart } from './ActivityByMonthChart'
import { useRegisterDashboard } from './hooks/useRegisterDashboard'
import './RegisterDashboardPage.css'

export function RegisterDashboardPage() {
  const { data, isLoading, isError } = useRegisterDashboard()

  return (
    <div className="dashboard-page">
      <h1>Dashboard</h1>

      {isLoading && <p>Loading dashboard...</p>}
      {isError && <p>Could not load the dashboard.</p>}

      {data && (
        <>
          <StatTiles
            totalDecisions={data.total_decisions}
            distinctPrompts={data.distinct_prompts}
            totalActionItems={data.total_action_items}
            highPriorityActions={data.high_priority_actions}
          />

          <div className="dashboard-page__grid">
            <div className="dashboard-panel">
              <h2>Top recurring risks</h2>
              <TopRisksList risks={data.top_risks} />
            </div>

            <div className="dashboard-panel">
              <h2>Agent alignment</h2>
              <AgentAlignmentChart alignment={data.agent_alignment} />
            </div>
          </div>

          <div className="dashboard-panel">
            <h2>Activity by month</h2>
            <ActivityByMonthChart perMonth={data.per_month} />
          </div>
        </>
      )}
    </div>
  )
}
