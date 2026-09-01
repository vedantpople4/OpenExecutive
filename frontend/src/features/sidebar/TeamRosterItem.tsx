import { useId, useState } from 'react'
import { RoleBadge } from '../../components/RoleBadge'
import { AgentPromptPreview } from './AgentPromptPreview'
import { SpecialistList } from './SpecialistList'
import type { Agent, Specialist } from '../../api/types'
import './TeamRosterItem.css'

interface TeamRosterItemProps {
  agent: Agent
  specialists: Specialist[]
  teamModeEnabled: boolean
}

/** Independently-expandable accordion row — not tied to any other roster item's state, since
 * users may want to compare two CXOs' prompts side by side while scrolling. */
export function TeamRosterItem({ agent, specialists, teamModeEnabled }: TeamRosterItemProps) {
  const [open, setOpen] = useState(false)
  const panelId = useId()

  return (
    <div className="team-roster-item">
      <button
        type="button"
        className="team-roster-item__header"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-controls={open ? panelId : undefined}
      >
        <span className={`team-roster-item__chevron ${open ? 'team-roster-item__chevron--open' : ''}`}>
          ▸
        </span>
        <RoleBadge name={agent.name} role={agent.role} />
        <span className="team-roster-item__role">{agent.role}</span>
        <span className="team-roster-item__focus">{agent.focus}</span>
      </button>

      {open && (
        <div id={panelId} className="team-roster-item__body">
          <AgentPromptPreview agentName={agent.name} />
          {teamModeEnabled && <SpecialistList specialists={specialists} />}
        </div>
      )}
    </div>
  )
}
