import { useRunStore } from '../../stores/useRunStore'
import { useAgentsMetadata } from './hooks/useAgentsMetadata'
import { useTeamStructure } from './hooks/useTeamStructure'
import { TeamRosterItem } from './TeamRosterItem'
import './TeamRosterPanel.css'

/**
 * Derived view off selectedAgents/teamModeEnabled (Zustand) + agent/team metadata (React
 * Query) — not independently configured. Renders one TeamRosterItem per selected CXO.
 */
export function TeamRosterPanel() {
  const selectedAgents = useRunStore((s) => s.selectedAgents)
  const teamModeEnabled = useRunStore((s) => s.teamModeEnabled)
  const { data: agents, isLoading: agentsLoading, isError: agentsError } = useAgentsMetadata()
  const { data: teamStructure, isLoading: teamLoading, isError: teamError } = useTeamStructure()
  const isLoading = agentsLoading || teamLoading
  const isError = agentsError || teamError

  return (
    <section className="sidebar__section" aria-label="Team roster">
      <h2 className="sidebar__heading">Current Team</h2>

      {isLoading && <p className="sidebar__placeholder">Loading team...</p>}

      {!isLoading && isError && (
        <p className="sidebar__placeholder" role="alert">
          Couldn't load team info.
        </p>
      )}

      {!isLoading && !isError && selectedAgents.length === 0 && (
        <p className="sidebar__placeholder">No agents selected.</p>
      )}

      {agents && teamStructure && selectedAgents.length > 0 && (
        <div className="team-roster-panel">
          {selectedAgents.map((name) => {
            const agent = agents.find((a) => a.name === name)
            if (!agent) return null
            return (
              <TeamRosterItem
                key={name}
                agent={agent}
                specialists={teamStructure[name] ?? []}
                teamModeEnabled={teamModeEnabled}
              />
            )
          })}
        </div>
      )}
    </section>
  )
}
