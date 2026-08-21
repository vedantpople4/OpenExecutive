import { AgentPicker } from './AgentPicker'
import { TeamModeToggle } from './TeamModeToggle'

export function SelectionPanel() {
  return (
    <section className="sidebar__section" aria-label="Agent and team selection">
      <h2 className="sidebar__heading">Board Selection</h2>
      <AgentPicker />
      <TeamModeToggle />
    </section>
  )
}
