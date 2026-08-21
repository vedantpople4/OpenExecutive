import { useRunStore } from '../../stores/useRunStore'
import './TeamModeToggle.css'

export function TeamModeToggle() {
  const teamModeEnabled = useRunStore((s) => s.teamModeEnabled)
  const toggleTeamMode = useRunStore((s) => s.toggleTeamMode)
  const selectedAgents = useRunStore((s) => s.selectedAgents)
  const disabled = selectedAgents.length === 0

  return (
    <label className={`team-mode-toggle ${disabled ? 'team-mode-toggle--disabled' : ''}`}>
      <input
        type="checkbox"
        checked={teamModeEnabled}
        disabled={disabled}
        onChange={toggleTeamMode}
      />
      <span>Enable specialist teams</span>
    </label>
  )
}
